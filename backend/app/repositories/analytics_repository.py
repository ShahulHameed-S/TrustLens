from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc, cast, Date, String
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.models.asset import Asset
from app.models.verification import Verification
from app.models.report import Report
from app.models.blockchain_block import BlockchainBlock

class AnalyticsRepository:
    def get_total_assets(self, db: Session, user_id: UUID) -> int:
        return db.execute(
            select(func.count()).select_from(Asset).where(Asset.user_id == user_id)
        ).scalar() or 0

    def get_total_verifications(self, db: Session, user_id: UUID) -> int:
        return db.execute(
            select(func.count()).select_from(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
        ).scalar() or 0

    def get_completed_verifications(self, db: Session, user_id: UUID) -> int:
        return db.execute(
            select(func.count()).select_from(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id, Verification.status == "COMPLETED")
        ).scalar() or 0

    def get_failed_verifications(self, db: Session, user_id: UUID) -> int:
        return db.execute(
            select(func.count()).select_from(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id, Verification.status == "FAILED")
        ).scalar() or 0

    def get_average_trust_score(self, db: Session, user_id: UUID) -> float:
        result = db.execute(
            select(func.avg(Verification.trust_score)).select_from(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id, Verification.trust_score.isnot(None))
        ).scalar()
        return float(result) if result is not None else 0.0

    def get_total_reports(self, db: Session, user_id: UUID) -> int:
        return db.execute(
            select(func.count()).select_from(Report)
            .join(Verification, Report.verification_id == Verification.id)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
        ).scalar() or 0

    def get_blockchain_records(self, db: Session, user_id: UUID) -> int:
        return db.execute(
            select(func.count()).select_from(BlockchainBlock)
            .join(Verification, BlockchainBlock.verification_id == Verification.id)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
        ).scalar() or 0

    def get_latest_verification(self, db: Session, user_id: UUID) -> Optional[datetime]:
        return db.execute(
            select(func.max(Verification.started_at)).select_from(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id)
        ).scalar()

    def get_risk_distribution(self, db: Session, user_id: UUID) -> Dict[str, int]:
        results = db.execute(
            select(Verification.risk_level, func.count())
            .select_from(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id, Verification.risk_level.isnot(None))
            .group_by(Verification.risk_level)
        ).all()
        
        distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for level, count in results:
            if level and level.upper() in distribution:
                distribution[level.upper()] += count
                
        return distribution

    def get_verification_trends(self, db: Session, user_id: UUID, days: int) -> List[Tuple[str, int]]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Cross-db date formatting is tricky. Let's do it in Python if volume is manageable, 
        # but for analytics we usually aggregate in DB.
        # However, since we support SQLite for tests and Postgres for prod, 
        # we can fetch raw dates and group in python to avoid dialect-specific Date/Trunc logic.
        
        results = db.execute(
            select(Verification.started_at)
            .select_from(Verification)
            .join(Asset, Verification.asset_id == Asset.id)
            .where(Asset.user_id == user_id, Verification.started_at >= start_date)
            .order_by(Verification.started_at.asc())
        ).scalars().all()
        
        trends = {}
        # Pre-fill dates to ensure zero counts for missing days
        for i in range(days):
            d = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            trends[d] = 0
            
        # Add today
        trends[datetime.utcnow().strftime('%Y-%m-%d')] = 0
            
        for started_at in results:
            if started_at:
                date_str = started_at.strftime('%Y-%m-%d')
                if date_str in trends:
                    trends[date_str] += 1
                else:
                    trends[date_str] = 1
                    
        sorted_trends = sorted(trends.items())
        return sorted_trends

    def get_asset_type_distribution(self, db: Session, user_id: UUID) -> Dict[str, int]:
        results = db.execute(
            select(Asset.asset_type, func.count())
            .select_from(Asset)
            .where(Asset.user_id == user_id, Asset.asset_type.isnot(None))
            .group_by(Asset.asset_type)
        ).all()
        
        distribution = {"PDF": 0, "IMAGE": 0, "AUDIO": 0}
        for asset_type, count in results:
            if asset_type and asset_type.upper() in distribution:
                distribution[asset_type.upper()] += count
                
        return distribution
