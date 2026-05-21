from typing import List, Dict
from fastapi import APIRouter, status, HTTPException, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.dependencies.pagination import pagination
from app.async_database import get_async_db
from app.models.user import User
from app.utils.dependencies import get_current_active_user, require_seller_or_admin, require_admin
from app.utils.redis_client import get_redis
from app.utils.storage import upload_file
from app.services.product_service import (
    get_all_products, get_product_by_id,
    create_product as svc_create_product,
    update_product as svc_update_product,
    delete_product as svc_delete_product,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[ProductOut], status_code=status.HTTP_200_OK)
async def read_products(
    params: Dict[int, int] = Depends(pagination), 
    db: AsyncSession = Depends(get_async_db),
    redis_client = Depends(get_redis)
):
    skip = params["skip"]
    limit = params["limit"]
    
    cache_key = "products:list"
    
    try:
        cached_products = await redis_client.get(cache_key)
        if cached_products:
            logger.info("Cache HIT for products list")
            return cached_products
        
        logger.info("Cache MISS for products list")
        products = await get_all_products(db, skip, limit)
        
        # Cache the result
        products_data = []
        for product in products:
            products_data.append({
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": float(product.price),
                "stock_quantity": product.stock_quantity,
                "seller_id": product.seller_id,
                "created_at": product.created_at.isoformat() if product.created_at else None
            })
        
        await redis_client.set(cache_key, products_data, expire=60)
        logger.info("Cached products list for 60 seconds")
        
        return products_data
        
    except Exception as e:
        logger.error(f"Error in read_products: {str(e)}")
        products = await get_all_products(db, skip, limit)
        return products

@router.get("/{id}", response_model=ProductOut, status_code=status.HTTP_200_OK)
async def read_product(id: int, db: AsyncSession = Depends(get_async_db)):
    product = await get_product_by_id(db, id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not Found")
    return product

@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_seller_or_admin),
    redis_client = Depends(get_redis)
):
    db_product = await svc_create_product(db, product, current_user.id)
    
    # Invalidate cache
    await redis_client.delete("products:list")
    logger.info("Cache invalidated after product creation")
    
    return db_product

@router.put("/{id}", response_model=ProductOut, status_code=status.HTTP_200_OK)
async def update_product(
    id: int, 
    product_update: ProductUpdate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    redis_client = Depends(get_redis)
):
    db_product = await svc_update_product(db, id, product_update, current_user)
    
    # Invalidate cache
    await redis_client.delete("products:list")
    logger.info("Cache invalidated after product update")
    
    return db_product

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin),
    redis_client = Depends(get_redis)
):
    await svc_delete_product(db, id, current_user)
    
    # Invalidate cache
    await redis_client.delete("products:list")
    logger.info("Cache invalidated after product deletion")

@router.post("/{id}/image", status_code=status.HTTP_200_OK)
async def upload_product_image(
    id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_seller_or_admin)
):
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed"
        )
    
    product = await get_product_by_id(db, id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not Found")
    
    if current_user.role.value != "admin" and product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to upload image for this product"
        )
    
    image_url = await upload_file(file, id)
    logger.info(f"Image uploaded for product {id}: {image_url}")
    
    return {
        "message": "Image uploaded successfully",
        "image_url": image_url,
        "product_id": id
    }
