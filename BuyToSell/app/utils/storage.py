import os
import uuid
from typing import Optional
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")

class LocalStorage:
    """Local file storage implementation"""
    
    def __init__(self):
        self.upload_dir = "static"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_file(self, file: UploadFile, product_id: int) -> str:
        """Save uploaded file locally and return URL"""
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{product_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Return URL path
        return f"/static/{unique_filename}"

class CloudinaryStorage:
    """Cloudinary cloud storage implementation"""
    
    def __init__(self):
        # This would be initialized with Cloudinary credentials
        # For now, we'll return a placeholder
        pass
    
    async def save_file(self, file: UploadFile, product_id: int) -> str:
        """Upload file to Cloudinary and return secure URL"""
        # Placeholder implementation
        # In production, you would:
        # 1. Configure Cloudinary with credentials
        # 2. Upload file using cloudinary.uploader.upload()
        # 3. Return the secure_url
        return f"https://res.cloudinary.com/demo/image/upload/v1/products/{product_id}_{file.filename}"

async def upload_file(file: UploadFile, product_id: int) -> str:
    """Upload file using configured storage backend"""
    if STORAGE_BACKEND == "cloudinary":
        storage = CloudinaryStorage()
    else:
        storage = LocalStorage()
    
    return await storage.save_file(file, product_id)
