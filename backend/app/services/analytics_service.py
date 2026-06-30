import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.user import UserResponse
from app.schemas.analytics import (
    DashboardMetrics,
    RiskDistribution,
    VerificationTrends,
    AssetTypeDistribution
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.repository = AnalyticsRepository()
        
    def _parse_timeframe(self, timeframe: str) -> int:
        if timeframe == "7d":
            return 7
        elif timeframe == "30d":
            return 30
        elif timeframe == "90d":
            return 90
        raise ValueError("INVALID_TIMEFRAME")

    def get_dashboard_analytics(self, db: Session, current_user: UserResponse) -> Dict[str, Any]:
        try:
            metrics = DashboardMetrics(
                total_assets=self.repository.get_total_assets(db, current_user.id),
                total_verifications=self.repository.get_total_verifications(db, current_user.id),
                completed_verifications=self.repository.get_completed_verifications(db, current_user.id),
                failed_verifications=self.repository.get_failed_verifications(db, current_user.id),
                average_trust_score=self.repository.get_average_trust_score(db, current_user.id),
                total_reports=self.repository.get_total_reports(db, current_user.id),
                blockchain_records=self.repository.get_blockchain_records(db, current_user.id),
                latest_verification=self.repository.get_latest_verification(db, current_user.id)
            )
            return {"success": True, "data": metrics.model_dump()}
        except Exception as e:
            logger.error(f"Failed to get dashboard analytics: {e}")
            raise RuntimeError("ANALYTICS_QUERY_FAILED")

    def get_risk_distribution(self, db: Session, current_user: UserResponse) -> Dict[str, Any]:
        try:
            distribution = self.repository.get_risk_distribution(db, current_user.id)
            return {"success": True, "data": distribution}
        except Exception as e:
            logger.error(f"Failed to get risk distribution: {e}")
            raise RuntimeError("ANALYTICS_QUERY_FAILED")

    def get_verification_trends(self, db: Session, current_user: UserResponse, timeframe: str = "30d") -> Dict[str, Any]:
        try:
            days = self._parse_timeframe(timeframe)
        except ValueError as e:
            raise e
            
        try:
            trends = self.repository.get_verification_trends(db, current_user.id, days)
            dates = [t[0] for t in trends]
            counts = [t[1] for t in trends]
            
            result = VerificationTrends(
                timeframe=timeframe,
                dates=dates,
                counts=counts
            )
            return {"success": True, "data": result.model_dump()}
        except Exception as e:
            logger.error(f"Failed to get verification trends: {e}")
            raise RuntimeError("ANALYTICS_QUERY_FAILED")

    def get_asset_type_distribution(self, db: Session, current_user: UserResponse) -> Dict[str, Any]:
        try:
            distribution = self.repository.get_asset_type_distribution(db, current_user.id)
            return {"success": True, "data": distribution}
        except Exception as e:
            logger.error(f"Failed to get asset type distribution: {e}")
            raise RuntimeError("ANALYTICS_QUERY_FAILED")
