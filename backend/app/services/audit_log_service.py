import logging
import math
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.user import UserResponse
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse

logger = logging.getLogger(__name__)

class AuditLogService:
    def __init__(self):
        self.repository = AuditLogRepository()

    def log_event(
        self,
        db: Session,
        action: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        try:
            self.repository.create_log(
                db=db,
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address
            )
        except Exception as e:
            # Audit logging failures must not crash the main business operation.
            logger.error(f"Failed to log audit event {action}: {e}")

    def list_audit_logs(
        self,
        db: Session,
        current_user: UserResponse,
        page: int = 1,
        limit: int = 50,
        sort: str = "timestamp",
        order: str = "desc"
    ) -> Dict[str, Any]:
        try:
            skip = (page - 1) * limit
            
            # Admins can view all audit logs
            is_admin = any(role.name == "admin" for role in getattr(current_user, 'roles', []))
            
            if is_admin:
                logs = self.repository.list_logs_paginated(db, skip, limit, sort, order)
                total = self.repository.get_total_logs_count(db)
            else:
                logs = self.repository.list_logs_by_user_paginated(db, current_user.id, skip, limit, sort, order)
                total = self.repository.get_total_logs_by_user_count(db, current_user.id)
                
            total_pages = math.ceil(total / limit) if total > 0 else 0
            
            response = AuditLogListResponse(
                items=[
                    AuditLogResponse(
                        id=log.id,
                        user_id=log.user_id,
                        action=log.action,
                        resource_type=log.resource_type,
                        resource_id=log.resource_id,
                        ip_address=log.ip_address,
                        timestamp=log.timestamp
                    ) for log in logs
                ],
                total=total,
                page=page,
                limit=limit,
                total_pages=total_pages
            )
            return {"success": True, "data": response.model_dump()}
            
        except Exception as e:
            logger.error(f"Failed to list audit logs: {e}")
            raise RuntimeError("AUDIT_QUERY_FAILED")

    def get_audit_log(self, db: Session, log_id: UUID, current_user: UserResponse) -> Dict[str, Any]:
        try:
            log = self.repository.get_by_id(db, log_id)
            if not log:
                raise ValueError("AUDIT_LOG_NOT_FOUND")
                
            is_admin = any(role.name == "admin" for role in getattr(current_user, 'roles', []))
            
            # Normal users can only view their own logs
            if not is_admin and log.user_id != current_user.id:
                raise PermissionError("FORBIDDEN")
                
            response = AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                timestamp=log.timestamp
            )
            return {"success": True, "data": response.model_dump()}
            
        except ValueError as e:
            raise e
        except PermissionError as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to get audit log {log_id}: {e}")
            raise RuntimeError("AUDIT_QUERY_FAILED")
