from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID

from app.models.report import Report
from app.models.verification import Verification
from app.models.asset import Asset

class ReportRepository:
    def create_report(self, db: Session, verification_id: UUID, report_url: str) -> Report:
        report = Report(
            verification_id=verification_id,
            report_url=report_url
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def get_report_by_id(self, db: Session, report_id: UUID) -> Optional[Report]:
        return db.execute(
            select(Report).where(Report.id == report_id)
        ).scalar_one_or_none()

    def get_report_by_verification_id(self, db: Session, verification_id: UUID) -> Optional[Report]:
        return db.execute(
            select(Report).where(Report.verification_id == verification_id)
        ).scalar_one_or_none()

    def list_reports_by_user(self, db: Session, user_id: UUID) -> List[Report]:
        # User -> Asset -> Verification -> Report
        return list(db.execute(
            select(Report)
            .join(Verification, Report.verification_id == Verification.id)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
            .order_by(Report.generated_at.desc())
        ).scalars().all())

    def list_reports_paginated(self, db: Session, user_id: UUID, skip: int, limit: int, sort_by: str = "generated_at", order: str = "desc") -> List[Report]:
        from sqlalchemy import desc
        stmt = (
            select(Report)
            .join(Verification, Report.verification_id == Verification.id)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
        )
        
        order_col = getattr(Report, sort_by, Report.generated_at)
        if order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)
            
        return list(db.execute(stmt.offset(skip).limit(limit)).scalars().all())

    def get_total_reports_count(self, db: Session, user_id: UUID) -> int:
        from sqlalchemy import func
        return db.execute(
            select(func.count())
            .select_from(Report)
            .join(Verification, Report.verification_id == Verification.id)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
        ).scalar_one()

    def delete_report(self, db: Session, report_id: UUID) -> bool:
        report = self.get_report_by_id(db, report_id)
        if report:
            db.delete(report)
            db.commit()
            return True
        return False
