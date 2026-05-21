from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

async def get_all_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Product]:
    """Get all products with pagination"""
    stmt = select(Product).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    """Get product by ID"""
    stmt = select(Product).filter(Product.id == product_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_product(db: AsyncSession, data: ProductCreate, seller_id: int) -> Product:
    """Create a new product"""
    db_product = Product(
        title=data.title,
        description=data.description,
        price=data.price,
        stock_quantity=data.stock_quantity,
        seller_id=seller_id
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    logger.info(f"Created product {db_product.id} by seller {seller_id}")
    return db_product

async def update_product(
    db: AsyncSession, 
    product_id: int, 
    data: ProductUpdate, 
    current_user: User
) -> Product:
    """Update a product"""
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not Found")
    
    # Check ownership or admin
    if current_user.role.value != "admin" and product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to update this product"
        )
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    logger.info(f"Updated product {product_id} by user {current_user.id}")
    return product

async def delete_product(db: AsyncSession, product_id: int, current_user: User) -> None:
    """Delete a product"""
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not Found")
    
    await db.delete(product)
    await db.commit()
    logger.info(f"Deleted product {product_id} by user {current_user.id}")
