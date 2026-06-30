from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

def format_error(code: str, message: str, details: dict = None):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AnalyticsService()
    try:
        return service.get_dashboard_analytics(db, current_user)
    except Exception as e:
        if str(e) == "ANALYTICS_QUERY_FAILED":
            return JSONResponse(
                status_code=500,
                content=format_error("ANALYTICS_QUERY_FAILED", "Failed to calculate dashboard analytics")
            )
        return JSONResponse(
            status_code=500,
            content=format_error("INTERNAL_ERROR", str(e))
        )

@router.get("/risk-distribution")
def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AnalyticsService()
    try:
        return service.get_risk_distribution(db, current_user)
    except Exception as e:
        if str(e) == "ANALYTICS_QUERY_FAILED":
            return JSONResponse(
                status_code=500,
                content=format_error("ANALYTICS_QUERY_FAILED", "Failed to calculate risk distribution")
            )
        return JSONResponse(
            status_code=500,
            content=format_error("INTERNAL_ERROR", str(e))
        )

@router.get("/verification-trends")
def get_verification_trends(
    timeframe: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AnalyticsService()
    try:
        return service.get_verification_trends(db, current_user, timeframe)
    except ValueError as e:
        if str(e) == "INVALID_TIMEFRAME":
            return JSONResponse(
                status_code=400,
                content=format_error("INVALID_TIMEFRAME", f"Unsupported timeframe: {timeframe}. Allowed: 7d, 30d, 90d.")
            )
        return JSONResponse(
            status_code=400,
            content=format_error("BAD_REQUEST", str(e))
        )
    except Exception as e:
        if str(e) == "ANALYTICS_QUERY_FAILED":
            return JSONResponse(
                status_code=500,
                content=format_error("ANALYTICS_QUERY_FAILED", "Failed to calculate verification trends")
            )
        return JSONResponse(
            status_code=500,
            content=format_error("INTERNAL_ERROR", str(e))
        )

@router.get("/asset-types")
def get_asset_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AnalyticsService()
    try:
        return service.get_asset_type_distribution(db, current_user)
    except Exception as e:
        if str(e) == "ANALYTICS_QUERY_FAILED":
            return JSONResponse(
                status_code=500,
                content=format_error("ANALYTICS_QUERY_FAILED", "Failed to calculate asset type distribution")
            )
        return JSONResponse(
            status_code=500,
            content=format_error("INTERNAL_ERROR", str(e))
        )
