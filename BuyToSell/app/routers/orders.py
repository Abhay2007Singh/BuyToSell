from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.schemas.order import OrderCreate, OrderOut
from app.database import get_db
from app.models.order import Order
from app.models.user import User
from app.utils.dependencies import require_customer_or_admin, get_current_active_user, require_admin
from app.utils.background import send_order_confirmation_email, deduct_stock
from app.utils.connection_manager import manager
from app.services.order_service import create_order, get_user_orders, update_order_status
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(
    order: OrderCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer_or_admin),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if current_user.role.value == "customer":
        order_user_id = current_user.id
    else:
        order_user_id = order.user_id
    
    db_order = create_order(db, order_user_id, order.items)
    
    # Add background tasks
    background_tasks.add_task(send_order_confirmation_email, db_order.id, current_user.email)
    background_tasks.add_task(deduct_stock, [{"product_id": item.product_id, "quantity": item.quantity} for item in order.items])
    
    # Broadcast order creation (fire-and-forget)
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast_to_order(db_order.id, {
            "type": "order_created",
            "order_id": db_order.id,
            "message": f"Order #{db_order.id} has been created"
        }))
    except RuntimeError:
        pass
    
    return db_order

@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(websocket: WebSocket, order_id: int, token: str = None):
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    try:
        user_id = 1  # Extract from token in production
        await manager.connect(websocket, order_id, user_id)
        
        await manager.send_personal_message(websocket, {
            "type": "connected",
            "order_id": order_id,
            "message": f"Connected to order #{order_id} status updates"
        })
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                await manager.send_personal_message(websocket, {
                    "type": "echo",
                    "message": f"Received: {message.get('message', '')}"
                })
                
        except WebSocketDisconnect:
            pass
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=4002, reason="Internal error")
    finally:
        manager.disconnect(websocket)

@router.put("/{id}/status", status_code=status.HTTP_200_OK)
def update_order_status_endpoint(
    id: int, 
    status_data: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    order = update_order_status(db, id, status_data.get("status"), current_user.id)
    
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast_to_order(id, {
            "type": "status_update",
            "order_id": id,
            "status": status_data.get("status"),
            "message": f"Order #{id} status updated to: {status_data.get('status')}"
        }))
    except RuntimeError:
        pass
    
    return {
        "order_id": id,
        "status": status_data.get("status"),
        "message": "Order status updated successfully"
    }

@router.get("/", response_model=List[OrderOut], status_code=status.HTTP_200_OK)
def get_orders(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.value == "customer":
        return get_user_orders(db, current_user.id, skip, limit)
    else:
        return get_user_orders(db, None, skip, limit)  # None means all users for admin

@router.get("/user/{user_id}", response_model=List[OrderOut], status_code=status.HTTP_200_OK)
def get_user_orders_endpoint(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.value == "customer" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these orders"
        )

    return get_user_orders(db, user_id, skip, limit)

@router.get("/{order_id}", response_model=OrderOut, status_code=status.HTTP_200_OK)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role.value != "admin" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )

    return order
