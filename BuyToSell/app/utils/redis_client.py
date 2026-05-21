import os
import json
import logging
from typing import Optional, Any
from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

logger = logging.getLogger(__name__)

class AsyncRedisClient:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
            print("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            print(f"Redis connection failed: {str(e)}")
            raise e
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            if not self.redis:
                await self.connect()
            value = await self.redis.get(key)
            return value
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration"""
        try:
            if not self.redis:
                await self.connect()
            
            # Convert to JSON if it's a dict/list
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = await self.redis.set(key, value, ex=expire)
            return result
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            if not self.redis:
                await self.connect()
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {str(e)}")
            return False

# Global Redis client instance
redis_client = AsyncRedisClient()

async def get_redis() -> AsyncRedisClient:
    """Dependency to get Redis client"""
    return redis_client
