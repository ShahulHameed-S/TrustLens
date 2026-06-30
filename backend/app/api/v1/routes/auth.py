from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest, CurrentUserResponse
from app.services.auth_service import AuthService
from app.core.responses import SuccessResponse, ErrorResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.schemas.audit_log import AuditAction

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=SuccessResponse[CurrentUserResponse])
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        user = auth_service.register_user(data)
        AuditLogService().log_event(
            db=db,
            action=AuditAction.AUTH_REGISTER,
            user_id=user.id,
            resource_type="USER",
            resource_id=str(user.id)
        )
        return SuccessResponse(data=user)
    except HTTPException as e:
        raise e

@router.post("/login", response_model=SuccessResponse[TokenResponse])
def login(data: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    tokens = auth_service.generate_tokens(user.email)
    AuditLogService().log_event(
        db=db,
        action=AuditAction.AUTH_LOGIN,
        user_id=user.id,
        resource_type="USER",
        resource_id=str(user.id)
    )
    return SuccessResponse(data=tokens)

@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
def refresh(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    tokens = auth_service.refresh_access_token(data.refresh_token)
    return SuccessResponse(data=tokens)

@router.post("/logout", response_model=SuccessResponse[dict])
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    AuditLogService().log_event(
        db=db,
        action=AuditAction.AUTH_LOGOUT,
        user_id=current_user.id
    )
    return SuccessResponse(data={"message": "Successfully logged out. Please remove token from storage."})

@router.get("/me", response_model=SuccessResponse[CurrentUserResponse])
def get_auth_me(current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=current_user)
