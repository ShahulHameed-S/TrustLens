from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.schemas.user import UserResponse
from app.schemas.verification import VerificationCreateRequest, VerificationResponse
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/verifications", tags=["verifications"])
verification_service = VerificationService()

@router.post("/pdf", response_model=VerificationResponse)
def verify_pdf_asset(
    request: VerificationCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Trigger full E2E verification for a PDF asset.
    """
    service = VerificationService()
    try:
        result = service.verify_pdf(
            db=db,
            asset_id=request.asset_id,
            current_user=current_user,
            register_to_blockchain=request.register_to_blockchain,
            generate_report=request.generate_report
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.post("/image", response_model=VerificationResponse)
def verify_image_asset(
    request: VerificationCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Trigger full E2E verification for an Image asset.
    """
    service = VerificationService()
    try:
        result = service.verify_image(
            db=db,
            asset_id=request.asset_id,
            current_user=current_user,
            register_to_blockchain=request.register_to_blockchain,
            generate_report=request.generate_report
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.post("/audio", response_model=VerificationResponse)
def verify_audio_asset(
    request: VerificationCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Trigger full E2E verification for an Audio asset.
    """
    service = VerificationService()
    try:
        result = service.verify_audio(
            db=db,
            asset_id=request.asset_id,
            current_user=current_user,
            register_to_blockchain=request.register_to_blockchain,
            generate_report=request.generate_report
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.get("", response_model=dict)
def list_verifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = "started_at",
    order: str = "desc",
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    return verification_service.list_verifications(db, current_user, page, limit, sort, order)

@router.get("/{verification_id}", response_model=VerificationResponse)
def get_verification(
    verification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    response = verification_service.get_verification(db, verification_id, current_user)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return response

@router.delete("/{verification_id}", response_model=dict)
def delete_verification(
    verification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    response = verification_service.delete_verification(db, verification_id, current_user)
    if not response.get("success"):
        raise HTTPException(status_code=404, detail=response.get("error"))
    return response

@router.get("/{verification_id}/report")
def get_verification_report(
    verification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    response = verification_service.get_verification_report(db, verification_id, current_user)
    if not response.get("success"):
        raise HTTPException(status_code=404, detail=response.get("error"))
    return response
