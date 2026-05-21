import asyncio
import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections per order_id: {order_id: [WebSocket1, WebSocket2, ...]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store connection metadata: {WebSocket: {"order_id": int, "user_id": int}}
        self.connection_metadata: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, order_id: int, user_id: int):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        
        # Add connection to the order group
        if order_id not in self.active_connections:
            self.active_connections[order_id] = []
        
        self.active_connections[order_id].append(websocket)
        
        # Store metadata for this connection
        self.connection_metadata[websocket] = {
            "order_id": order_id,
            "user_id": user_id
        }
        
        logger.info(f"WebSocket connected for order {order_id}, user {user_id}")
        print(f"WS CONNECT: Order {order_id}, User {user_id}, Total connections: {len(self.active_connections[order_id])}")
        
        # Notify others in the same order group
        await self.broadcast_to_order(order_id, {
            "type": "user_joined",
            "message": f"User {user_id} joined the order status updates",
            "timestamp": self._get_timestamp()
        }, exclude_websocket=websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return
        
        order_id = metadata["order_id"]
        user_id = metadata["user_id"]
        
        # Remove from active connections
        if order_id in self.active_connections:
            if websocket in self.active_connections[order_id]:
                self.active_connections[order_id].remove(websocket)
            
            # Clean up empty order groups
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]
        
        # Remove metadata
        del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected for order {order_id}, user {user_id}")
        print(f"WS DISCONNECT: Order {order_id}, User {user_id}, Remaining connections: {len(self.active_connections.get(order_id, []))}")
        
        # Notify others in the same order group
        if order_id in self.active_connections:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.broadcast_to_order(order_id, {
                    "type": "user_left",
                    "message": f"User {user_id} left the order status updates",
                    "timestamp": self._get_timestamp()
                }))
            except RuntimeError:
                pass
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
            logger.info(f"Personal message sent to user {self.connection_metadata.get(websocket, {}).get('user_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send personal message: {str(e)}")
    
    async def broadcast_to_order(self, order_id: int, message: dict, exclude_websocket: WebSocket = None):
        """Broadcast message to all connections for a specific order"""
        if order_id not in self.active_connections:
            return
        
        disconnected_connections = []
        for connection in self.active_connections[order_id]:
            if connection == exclude_websocket:
                continue
                
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to connection: {str(e)}")
                disconnected_connections.append(connection)
        
        # Clean up dead connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        logger.info(f"Broadcast sent to order {order_id}: {message.get('type', 'unknown')}")
        print(f"WS BROADCAST: Order {order_id}, Type: {message.get('type', 'unknown')}, Connections: {len(self.active_connections.get(order_id, []))}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Global connection manager instance
manager = ConnectionManager()
