from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import math
import os

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.report_repository import ReportRepository
from app.repositories.verification_repository import VerificationRepository
from app.services.report_engine import ReportEngine
from app.services.audit_log_service import AuditLogService
from app.schemas.audit_log import AuditAction

router = APIRouter(prefix="/reports", tags=["Reports"])

def format_error(code: str, message: str, details: dict = None):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }

def format_success(data: dict):
    return {
        "success": True,
        "data": data
    }

class ReportGenerateRequest(BaseModel):
    report_format: str = "JSON"

def get_report_metadata(report):
    return {
        "report_id": str(report.id),
        "verification_id": str(report.verification_id),
        "report_format": "JSON" if report.report_url.endswith(".json") else "HTML",
        "status": "READY",
        "generated_at": report.generated_at.isoformat() if report.generated_at else None
    }

def verify_report_ownership(db: Session, report_id: UUID, user_id: UUID):
    report_repo = ReportRepository()
    report = report_repo.get_report_by_id(db, report_id)
    if not report:
        return None, JSONResponse(
            status_code=404,
            content=format_error("REPORT_NOT_FOUND", "Report not found")
        )
        
    verif_repo = VerificationRepository()
    verif = verif_repo.get_by_user(db, report.verification_id, user_id)
    if not verif:
        return None, JSONResponse(
            status_code=403,
            content=format_error("FORBIDDEN", "You do not have access to this report")
        )
        
    return report, None

@router.post("/generate/{verification_id}", response_model=dict)
def generate_report(
    verification_id: UUID,
    request: Optional[ReportGenerateRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req_format = request.report_format.upper() if request else "JSON"
    if req_format not in ["JSON", "HTML"]:
        return JSONResponse(
            status_code=400,
            content=format_error("INVALID_REPORT_FORMAT", f"Unsupported report format: {req_format}")
        )
        
    verif_repo = VerificationRepository()
    verif = verif_repo.get_by_user(db, verification_id, current_user.id)
    
    if not verif:
        return JSONResponse(
            status_code=404,
            content=format_error("VERIFICATION_NOT_FOUND", "Verification not found or unauthorized")
        )
        
    engine = ReportEngine()
    try:
        # Use existing JSON report to regenerate requested format or return existing
        result = engine.generate_report_from_existing(db, verification_id, req_format)
        
        AuditLogService().log_event(
            db=db,
            action=AuditAction.REPORT_GENERATED,
            user_id=current_user.id,
            resource_type="report",
            resource_id=str(result.report_id) if hasattr(result, 'report_id') else None
        )
        
        return format_success({
            "report_id": str(result.report_id),
            "verification_id": str(result.verification_id),
            "report_format": result.report_format,
            "status": result.status,
            "generated_at": result.generated_at.isoformat() if result.generated_at else None
        })
    except ValueError as e:
        error_msg = str(e)
        if "VERIFICATION_NOT_FOUND" in error_msg or "REPORT_NOT_FOUND" in error_msg:
            return JSONResponse(
                status_code=404,
                content=format_error("REPORT_NOT_FOUND", "No existing report found to generate from")
            )
        elif "Unsupported report format" in error_msg or "cannot convert" in error_msg:
            return JSONResponse(
                status_code=400,
                content=format_error("INVALID_REPORT_FORMAT", error_msg)
            )
        else:
            return JSONResponse(
                status_code=500,
                content=format_error("REPORT_GENERATION_FAILED", error_msg)
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=format_error("REPORT_GENERATION_FAILED", str(e))
        )

@router.get("/{report_id}", response_model=dict)
def get_report_info(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report, error_resp = verify_report_ownership(db, report_id, current_user.id)
    if error_resp:
        return error_resp
        
    return format_success(get_report_metadata(report))

@router.get("/download/{report_id}")
def download_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report, error_resp = verify_report_ownership(db, report_id, current_user.id)
    if error_resp:
        return error_resp
        
    file_path = report.report_url
    if not file_path or not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content=format_error("REPORT_FILE_NOT_FOUND", "The report file is missing on the server")
        )
        
    # Prevent path traversal
    safe_path = os.path.abspath(file_path)
    if not os.path.isfile(safe_path):
        return JSONResponse(
            status_code=404,
            content=format_error("REPORT_FILE_NOT_FOUND", "Invalid report file path")
        )
        
    return FileResponse(
        path=safe_path, 
        filename=os.path.basename(safe_path),
        media_type="application/json" if safe_path.endswith(".json") else "text/html"
    )

@router.get("", response_model=dict)
def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("generated_at", pattern="^(generated_at|id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report_repo = ReportRepository()
    skip = (page - 1) * limit
    
    reports = report_repo.list_reports_paginated(
        db=db, user_id=current_user.id, skip=skip, limit=limit, sort_by=sort, order=order
    )
    total = report_repo.get_total_reports_count(db, current_user.id)
    
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    
    items = [get_report_metadata(r) for r in reports]
    
    return format_success({
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    })
