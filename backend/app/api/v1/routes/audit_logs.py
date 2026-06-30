from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

def format_error(code: str, message: str, details: dict = None):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }

@router.get("")
def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort: str = Query("timestamp"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AuditLogService()
    try:
        return service.list_audit_logs(db, current_user, page, limit, sort, order)
    except Exception as e:
        if str(e) == "AUDIT_QUERY_FAILED":
            return JSONResponse(
                status_code=500,
                content=format_error("AUDIT_QUERY_FAILED", "Failed to retrieve audit logs")
            )
        return JSONResponse(
            status_code=500,
            content=format_error("INTERNAL_ERROR", str(e))
        )

@router.get("/{log_id}")
def get_audit_log(
    log_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AuditLogService()
    try:
        return service.get_audit_log(db, log_id, current_user)
    except ValueError as e:
        if str(e) == "AUDIT_LOG_NOT_FOUND":
            return JSONResponse(
                status_code=404,
                content=format_error("AUDIT_LOG_NOT_FOUND", f"Audit log {log_id} not found")
            )
        return JSONResponse(
            status_code=400,
            content=format_error("BAD_REQUEST", str(e))
        )
    except PermissionError as e:
        if str(e) == "FORBIDDEN":
            return JSONResponse(
                status_code=403,
                content=format_error("FORBIDDEN", "You do not have permission to access this audit log")
            )
        return JSONResponse(
            status_code=403,
            content=format_error("FORBIDDEN", str(e))
        )
    except Exception as e:
        if str(e) == "AUDIT_QUERY_FAILED":
            return JSONResponse(
                status_code=500,
                content=format_error("AUDIT_QUERY_FAILED", "Failed to retrieve audit log")
            )
        return JSONResponse(
            status_code=500,
            content=format_error("INTERNAL_ERROR", str(e))
        )
