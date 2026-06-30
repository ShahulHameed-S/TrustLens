from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from app.schemas.metadata import AssetType

class ForensicsResult(BaseModel):
    asset_type: AssetType = Field(..., description="The type of the analyzed asset")
    analyzed_at: datetime = Field(..., description="Timestamp of the forensic analysis")
    tampering_detected: bool = Field(..., description="Indicates if tampering was strongly suspected")
    confidence: float = Field(..., description="Confidence level of the analysis from 0 to 100")
    forensic_score: float = Field(..., description="Module-level forensic score from 0 to 100")
    findings: List[str] = Field(default_factory=list, description="List of human-readable forensic observations")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal analysis warnings")
    raw_signals: Dict[str, Any] = Field(default_factory=dict, description="JSON/dict containing technical evidence")
