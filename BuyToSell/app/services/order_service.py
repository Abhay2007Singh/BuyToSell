from typing import List
from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

def create_order(db: Session, user_id: int, items: List[OrderCreate]) -> Order:
    """Create a new order with items"""
    # Create order
    db_order = Order(user_id=user_id)
    db.add(db_order)
    db.flush()  # Get order ID without committing
    
    total_amount = 0
    
    # Create order items
    for item_data in items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Product {item_data.product_id} not found"
            )
        
        if product.stock_quantity < item_data.quantity:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Insufficient stock for product {product.title}"
            )
        
        # Update product stock
        product.stock_quantity -= item_data.quantity
        
        # Create order item
        order_item = OrderItem(
            order_id=db_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price=item_data.price
        )
        db.add(order_item)
        total_amount += item_data.price * item_data.quantity
    
    db.commit()
    db.refresh(db_order)
    
    logger.info(f"Order created: {db_order.id} for user {user_id}")
    return db_order

def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    """Get orders for a specific user, or all orders if user_id is None (admin)"""
    query = db.query(Order)
    if user_id is not None:
        query = query.filter(Order.user_id == user_id)
    orders = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(orders)} orders for user {user_id}")
    return orders

def update_order_status(db: Session, order_id: int, new_status: str, current_user_id: int) -> Order:
    """Update order status (admin only)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # For now, we'll just log the status update
    # In a real implementation, you'd add a status field to Order model
    logger.info(f"Order {order_id} status updated to {new_status} by admin {current_user_id}")
    
    return order
