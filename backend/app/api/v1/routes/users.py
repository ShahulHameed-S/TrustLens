from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.repositories.user_repository import UserRepository
from app.core.responses import SuccessResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=SuccessResponse[UserResponse])
def get_user_me(current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=current_user)

@router.put("/me", response_model=SuccessResponse[UserResponse])
def update_user_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_repo = UserRepository(db)
    updated_user = user_repo.update_user(current_user, data)
    return SuccessResponse(data=updated_user)

@router.delete("/me", response_model=SuccessResponse[dict])
def delete_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_repo = UserRepository(db)
    user_repo.deactivate_user(current_user)
    return SuccessResponse(data={"message": "User deactivated successfully"})
