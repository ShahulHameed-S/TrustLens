from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc
from typing import Optional, List
from uuid import UUID

from app.models.audit_log import AuditLog

class AuditLogRepository:
    def create_log(
        self,
        db: Session,
        action: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_by_id(self, db: Session, log_id: UUID) -> Optional[AuditLog]:
        return db.query(AuditLog).filter(AuditLog.id == log_id).first()

    def list_logs_paginated(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        sort: str = "timestamp",
        order: str = "desc"
    ) -> List[AuditLog]:
        query = db.query(AuditLog)
        
        sort_attr = getattr(AuditLog, sort, AuditLog.timestamp)
        if order.lower() == "asc":
            query = query.order_by(asc(sort_attr))
        else:
            query = query.order_by(desc(sort_attr))
            
        return query.offset(skip).limit(limit).all()

    def list_logs_by_user_paginated(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        sort: str = "timestamp",
        order: str = "desc"
    ) -> List[AuditLog]:
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        sort_attr = getattr(AuditLog, sort, AuditLog.timestamp)
        if order.lower() == "asc":
            query = query.order_by(asc(sort_attr))
        else:
            query = query.order_by(desc(sort_attr))
            
        return query.offset(skip).limit(limit).all()

    def get_total_logs_count(self, db: Session) -> int:
        return db.query(func.count(AuditLog.id)).scalar() or 0

    def get_total_logs_by_user_count(self, db: Session, user_id: UUID) -> int:
        return db.query(func.count(AuditLog.id)).filter(AuditLog.user_id == user_id).scalar() or 0
