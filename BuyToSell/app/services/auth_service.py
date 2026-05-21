from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, Token
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

def register_user(db: Session, email: str, password: str, role: str = "customer") -> User:
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(password)
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User registered: {email} with role {role}")
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning(f"Authentication failed: user not found - {email}")
        return None
    
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed: invalid password - {email}")
        return None
    
    logger.info(f"User authenticated successfully: {email}")
    return user

def generate_tokens(user: User) -> Token:
    """Generate access and refresh tokens for user"""
    access_token_data = {"sub": user.email}
    refresh_token_data = {"sub": user.email}
    
    access_token = create_access_token(data=access_token_data)
    refresh_token = create_refresh_token(data=refresh_token_data)
    
    logger.info(f"Tokens generated for user: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
