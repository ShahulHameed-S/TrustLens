from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class AuditAction(str, Enum):
    AUTH_REGISTER = "AUTH_REGISTER"
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    ASSET_UPLOAD = "ASSET_UPLOAD"
    ASSET_DELETE = "ASSET_DELETE"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    REPORT_GENERATED = "REPORT_GENERATED"
    BLOCKCHAIN_VALIDATED = "BLOCKCHAIN_VALIDATED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"

class AuditLogBase(BaseModel):
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None

class AuditLogResponse(AuditLogBase):
    id: UUID
    timestamp: datetime
    
class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    limit: int
    total_pages: int
