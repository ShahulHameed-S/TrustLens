from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.asset_service import AssetService
from app.schemas.asset import AssetUploadData, AssetResponse, AssetListResponse
from app.core.responses import SuccessResponse
from uuid import UUID
from app.services.audit_log_service import AuditLogService
from app.schemas.audit_log import AuditAction

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.post("/upload", response_model=SuccessResponse[AssetUploadData])
async def upload_asset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset_service = AssetService(db)
    result = await asset_service.create_asset_record(current_user.id, file)
    AuditLogService().log_event(
        db=db,
        action=AuditAction.ASSET_UPLOAD,
        user_id=current_user.id,
        resource_type="asset",
        resource_id=str(result.asset_id) if hasattr(result, 'asset_id') else None
    )
    return SuccessResponse(data=result)

@router.get("", response_model=SuccessResponse[AssetListResponse])
def list_assets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("uploaded_at"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset_service = AssetService(db)
    items, total = asset_service.list_user_assets(current_user.id, page, limit)
    
    list_response = AssetListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )
    return SuccessResponse(data=list_response)

@router.get("/{asset_id}", response_model=SuccessResponse[AssetResponse])
def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset_service = AssetService(db)
    asset = asset_service.get_asset_details(asset_id, current_user.id)
    return SuccessResponse(data=asset)

@router.delete("/{asset_id}", response_model=SuccessResponse[dict])
def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset_service = AssetService(db)
    asset_service.delete_user_asset(asset_id, current_user.id)
    AuditLogService().log_event(
        db=db,
        action=AuditAction.ASSET_DELETE,
        user_id=current_user.id,
        resource_type="asset",
        resource_id=str(asset_id)
    )
    return SuccessResponse(data={"message": "Asset deleted successfully"})
