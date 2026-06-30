from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class DashboardMetrics(BaseModel):
    total_assets: int
    total_verifications: int
    completed_verifications: int
    failed_verifications: int
    average_trust_score: float
    total_reports: int
    blockchain_records: int
    latest_verification: Optional[datetime]

class RiskDistribution(BaseModel):
    LOW: int
    MEDIUM: int
    HIGH: int

class VerificationTrends(BaseModel):
    timeframe: str
    dates: List[str]
    counts: List[int]

class AssetTypeDistribution(BaseModel):
    PDF: int
    IMAGE: int
    AUDIO: int
