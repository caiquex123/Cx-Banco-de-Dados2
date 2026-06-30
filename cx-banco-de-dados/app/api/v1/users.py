from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...database import get_db
from ...models.user import User
from ...schemas.user import UserResponse, UserUpdate
from ...core.security import get_password_hash, hash_api_key, generate_api_key
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Users can only access their own data unless they're admin (future feature)
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        plan=user.plan,
        created_at=user.created_at
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        plan=user.plan,
        created_at=user.created_at
    )

@router.post("/{user_id}/regenerate-api-key", response_model=dict)
async def regenerate_api_key(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new API key
    new_api_key = generate_api_key()
    user.api_key = new_api_key
    user.api_key_hash = hash_api_key(new_api_key)
    
    db.commit()
    
    return {"api_key": new_api_key, "message": "API key regenerated successfully"}
