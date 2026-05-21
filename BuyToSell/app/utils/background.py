import asyncio
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.order_item import OrderItem
from app.models.product import Product

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_order_confirmation_email(order_id: int, user_email: str):
    """Mock function to send order confirmation email"""
    try:
        # Simulate email sending delay
        import time
        time.sleep(2)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] EMAIL SENT: Order confirmation for order #{order_id} sent to {user_email}"
        logger.info(message)
        print(message)
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order_id}: {str(e)}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EMAIL ERROR: {str(e)}")

async def deduct_stock(order_items: List[dict]):
    """Async background function to deduct stock from products"""
    try:
        db = SessionLocal()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[{timestamp}] STOCK DEDUCTION: Starting stock deduction for {len(order_items)} items")
        
        for item in order_items:
            try:
                product = db.query(Product).filter(Product.id == item["product_id"]).first()
                if not product:
                    error_msg = f"[{timestamp}] STOCK ERROR: Product {item['product_id']} not found"
                    logger.error(error_msg)
                    print(error_msg)
                    continue
                
                if product.stock_quantity >= item["quantity"]:
                    product.stock_quantity -= item["quantity"]
                    success_msg = f"[{timestamp}] STOCK SUCCESS: Deducted {item['quantity']} from product {item['product_id']} (new stock: {product.stock_quantity})"
                    logger.info(success_msg)
                    print(success_msg)
                else:
                    error_msg = f"[{timestamp}] STOCK INSUFFICIENT: Product {item['product_id']} has {product.stock_quantity}, need {item['quantity']}"
                    logger.error(error_msg)
                    print(error_msg)
                    
            except Exception as e:
                error_msg = f"[{timestamp}] STOCK ERROR: Failed to deduct stock for product {item['product_id']}: {str(e)}"
                logger.error(error_msg)
                print(error_msg)
        
        try:
            db.commit()
            print(f"[{timestamp}] STOCK DEDUCTION: Database commit completed")
        except Exception as e:
            db.rollback()
            error_msg = f"[{timestamp}] STOCK ERROR: Database commit failed: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            
    except Exception as e:
        error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] STOCK ERROR: Critical error in stock deduction: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
    finally:
        db.close()
