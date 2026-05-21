from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.dependencies.pagination import pagination
from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import hash_password
from app.utils.dependencies import get_current_active_user, require_admin

router = APIRouter()

@router.get("/", response_model=List[UserOut], status_code=status.HTTP_200_OK)
def read_users(
    params: Dict[int, int] = Depends(pagination), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    skip = params["skip"]
    limit = params["limit"]
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def read_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found")
    return user

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Create new user
    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def update_user(
    id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found")
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found")
    
    db.delete(user)
    db.commit()
    return
