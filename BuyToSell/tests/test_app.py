"""Test app configuration without startup events"""
from fastapi import FastAPI
from app.routers import users, products, orders, auth
from app.middleware import RequestLoggingMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

# Create test app without startup events
test_app = FastAPI(title="BestBuyAndSell Test API")

# Add rate limiter
limiter = Limiter(key_func=get_remote_address)
test_app.state.limiter = limiter

# Add rate limit exception handler
test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@test_app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

# Add middleware
test_app.add_middleware(RequestLoggingMiddleware)

# Include routers
test_app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

test_app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)

test_app.include_router(
    products.router,
    prefix="/api/v1/products", 
    tags=["products"]
)

test_app.include_router(
    orders.router,
    prefix="/api/v1/orders", 
    tags=["orders"]
)

@test_app.get("/")
def root():
    return {"message": "Welcome to BestBuyAndSell Test API"}
