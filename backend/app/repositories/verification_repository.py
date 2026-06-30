from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.verification import Verification
from app.models.asset import Asset
from app.schemas.trust_score import TrustScoreResult

class VerificationRepository:
    def create_verification(self, db: Session, asset_id: UUID) -> Verification:
        verification = Verification(
            asset_id=asset_id,
            status="PROCESSING"
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        return verification

    def update_verification_status(self, db: Session, verification_id: UUID, status: str) -> None:
        db.execute(
            update(Verification)
            .where(Verification.id == verification_id)
            .values(status=status)
        )
        db.commit()

    def update_verification_result(self, db: Session, verification_id: UUID, trust_score_result: TrustScoreResult) -> None:
        db.execute(
            update(Verification)
            .where(Verification.id == verification_id)
            .values(
                status="COMPLETED",
                trust_score=trust_score_result.trust_score,
                risk_level=trust_score_result.risk_level.value if hasattr(trust_score_result.risk_level, 'value') else str(trust_score_result.risk_level),
                completed_at=datetime.utcnow()
            )
        )
        db.commit()

    def get_by_id(self, db: Session, verification_id: UUID) -> Optional[Verification]:
        return db.execute(
            select(Verification).where(Verification.id == verification_id)
        ).scalar_one_or_none()

    def get_by_user(self, db: Session, verification_id: UUID, user_id: UUID) -> Optional[Verification]:
        return db.execute(
            select(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Verification.id == verification_id, Asset.user_id == user_id)
        ).scalar_one_or_none()

    def list_user_verifications_paginated(self, db: Session, user_id: UUID, page: int = 1, limit: int = 20, sort: str = "started_at", order: str = "desc") -> List[Verification]:
        offset = (page - 1) * limit
        order_col = getattr(Verification, sort, Verification.started_at)
        if order == "desc":
            order_col = order_col.desc()
            
        return list(db.execute(
            select(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
            .order_by(order_col)
            .offset(offset)
            .limit(limit)
        ).scalars().all())

    def delete_verification(self, db: Session, verification_id: UUID) -> bool:
        verification = self.get_by_id(db, verification_id)
        if verification:
            db.delete(verification)
            db.commit()
            return True
        return False
