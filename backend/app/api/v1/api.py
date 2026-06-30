from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    users,
    assets,
    verifications,
    blockchain,
    analytics,
    reports,
    audit_logs
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(assets.router)
api_router.include_router(verifications.router)
api_router.include_router(blockchain.router)
api_router.include_router(analytics.router)
api_router.include_router(reports.router)
api_router.include_router(audit_logs.router)
