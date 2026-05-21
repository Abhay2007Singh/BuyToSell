from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import get_db, engine, Base
from app.models import *  # noqa: F401,F403 — registers all models with Base
from app.routers import users, products, orders, auth
from app.utils.redis_client import get_redis
from app.middleware import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="BestBuyAndSell API", lifespan=lifespan)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

app.add_middleware(RequestLoggingMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router,     prefix="/api/v1/auth",     tags=["authentication"])
app.include_router(users.router,    prefix="/api/v1/users",    tags=["users"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(orders.router,   prefix="/api/v1/orders",   tags=["orders"])


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Welcome to BestBuyAndSell API"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/api/v1/cache/test")
async def cache_test(redis_client=Depends(get_redis)):
    try:
        await redis_client.set("test", "hello", expire=30)
        cached_value = await redis_client.get("test")
        return {
            "status": "success",
            "set_value": "hello",
            "cached_value": cached_value,
            "cache_hit": cached_value == "hello",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
