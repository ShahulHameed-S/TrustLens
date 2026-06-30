from pydantic import BaseModel, Field, ConfigDict, UUID4
from typing import Optional, Dict, Any, List
from datetime import datetime

class ReportContent(BaseModel):
    verification_summary: str
    asset_details: Dict[str, Any]
    hash_details: Optional[Dict[str, Any]]
    metadata_details: Optional[Dict[str, Any]]
    forensic_findings: Optional[Dict[str, Any]]
    trust_score: float
    risk_level: str
    document_status: str
    ai_explanation: Optional[Dict[str, Any]]
    blockchain_proof: Optional[Dict[str, Any]]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ReportGenerationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    report_id: Optional[UUID4] = None
    verification_id: UUID4
    report_format: str
    report_path: str
    generated_at: datetime
    status: str
    summary: str
