import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User, UserRole
from app.utils.security import hash_password, create_access_token
from tests.test_app import test_app

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client"""
    # Override database dependency
    from app.database import get_db
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        yield test_client
    
    test_app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def admin_client(db):
    """Create an authenticated admin client"""
    from app.database import get_db
    
    # Create admin user
    user = User(
        email="test_admin@example.com",
        hashed_password=hash_password("testpass"),
        role=UserRole.ADMIN
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    token = create_access_token(data={"sub": user.email})
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client
    
    test_app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def seller_client(db):
    """Create an authenticated seller client"""
    from app.database import get_db
    
    # Create seller user
    user = User(
        email="test_seller@example.com",
        hashed_password=hash_password("testpass"),
        role=UserRole.SELLER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    create_access_token(data={"sub": user.email})
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client
    
    test_app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def customer_client(db):
    """Create an authenticated customer client"""
    from app.database import get_db
    
    # Create customer user
    user = User(
        email="test_customer@example.com",
        hashed_password=hash_password("testpass"),
        role=UserRole.CUSTOMER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    token = create_access_token(data={"sub": user.email})
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client
    
    test_app.dependency_overrides.clear()
