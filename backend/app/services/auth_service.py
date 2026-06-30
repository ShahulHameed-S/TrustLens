from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_jwt_token
from typing import Dict, Any

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    def register_user(self, data: RegisterRequest) -> Dict[str, Any]:
        existing_user = self.user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user_in = UserCreate(email=data.email, password=data.password, is_active=True)
        new_user = self.user_repo.create_user(user_in)

        user_role = self.role_repo.get_by_name("user")
        if user_role:
            self.user_repo.assign_role(new_user, user_role)
            
        return new_user

    def authenticate_user(self, data: LoginRequest):
        user = self.user_repo.get_by_email(data.email)
        if not user:
            return None
        if not verify_password(data.password, user.password_hash):
            return None
        return user

    def generate_tokens(self, subject: str) -> Dict[str, str]:
        access_token = create_access_token(data={"sub": subject})
        refresh_token = create_refresh_token(data={"sub": subject})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        payload = decode_jwt_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
            
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")
            
        user = self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
            
        # Issue a new access token
        access_token = create_access_token(data={"sub": email})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
