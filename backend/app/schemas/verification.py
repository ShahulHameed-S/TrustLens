from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class VerificationCreateRequest(BaseModel):
    asset_id: UUID4
    register_to_blockchain: bool = True
    generate_report: bool = True

class VerificationResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    verification_id: UUID4
    asset_id: UUID4
    filename: str
    asset_type: str
    file_hash: str
    verification_status: str
    document_status: Optional[str] = None
    trust_score: Optional[float] = None
    risk_level: Optional[str] = None
    
    blockchain_proof: Optional[Dict[str, Any]] = None
    ai_explanation: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    forensics: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    
    created_at: datetime

class VerificationResponse(BaseModel):
    success: bool
    data: Optional[VerificationResponseData] = None
    error: Optional[str] = None
