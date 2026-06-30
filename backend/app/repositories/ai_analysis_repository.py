from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, Dict, Any
from uuid import UUID

from app.models.ai_analysis import AIAnalysis

class AIAnalysisRepository:
    def create_ai_analysis(self, db: Session, verification_id: UUID, forensic_evidence: Dict[str, Any], ai_explanation: Dict[str, Any], model_version: str) -> AIAnalysis:
        ai_analysis = AIAnalysis(
            verification_id=verification_id,
            forensic_evidence=forensic_evidence,
            ai_explanation=ai_explanation,
            model_version=model_version
        )
        db.add(ai_analysis)
        db.commit()
        db.refresh(ai_analysis)
        return ai_analysis

    def get_by_verification_id(self, db: Session, verification_id: UUID) -> Optional[AIAnalysis]:
        return db.execute(
            select(AIAnalysis).where(AIAnalysis.verification_id == verification_id)
        ).scalar_one_or_none()
