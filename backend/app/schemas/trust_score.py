from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class DocumentStatus(str, Enum):
    AUTHENTIC = "AUTHENTIC"
    SUSPICIOUS = "SUSPICIOUS"
    UNVERIFIED = "UNVERIFIED"

class Penalty(BaseModel):
    reason: str
    points_deducted: float

class TrustScoreResult(BaseModel):
    trust_score: float = Field(..., description="Final deterministic trust score from 0 to 100")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    document_status: DocumentStatus = Field(..., description="Overall document status classification")
    confidence: float = Field(..., description="Confidence in the score based on evidence availability, from 0 to 100")
    score_breakdown: Dict[str, float] = Field(..., description="Contribution from each evidence source")
    penalties: List[Penalty] = Field(default_factory=list, description="List of applied penalties")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of calculation")
