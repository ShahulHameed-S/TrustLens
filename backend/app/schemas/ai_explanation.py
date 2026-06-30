from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ExplanationMode(str, Enum):
    RULE_BASED = "RULE_BASED"
    LOCAL_LLM = "LOCAL_LLM"
    FALLBACK = "FALLBACK"

class AIExplanationResult(BaseModel):
    summary: str = Field(..., description="Short plain-English explanation of the verification result")
    evidence: List[str] = Field(..., description="Important evidence used in the decision")
    reasoning: str = Field(..., description="Why the system classified the asset as AUTHENTIC, SUSPICIOUS, or UNVERIFIED")
    recommendation: str = Field(..., description="What the user should do next")
    confidence: float = Field(..., description="0 to 100 explanation confidence")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp")
    model_name: str = Field(..., description="Name of model or explanation method used")
    explanation_mode: ExplanationMode = Field(..., description="The mode used to generate the explanation")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal explanation warnings")
