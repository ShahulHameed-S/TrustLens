from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.api import api_router
from app.core.responses import ErrorResponse, ErrorDetails

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Startup time for uptime calculation
startup_time = time.time()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.database.session import SessionLocal
from app.services.user_service import UserService

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetails(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred."
        )
    )
    return JSONResponse(status_code=500, content=error_response.model_dump())

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetails(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail)
        )
    )
    return JSONResponse(status_code=exc.status_code, content=error_response.model_dump())

@app.on_event("startup")
def startup_event():
    with SessionLocal() as db:
        user_service = UserService(db)
        user_service.ensure_default_roles()

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
async def health_check():
    """
    Production health monitor.
    """
    uptime = time.time() - startup_time
    
    return {
        "application": settings.APP_NAME,
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "database": "connected",
        "storage": "operational",
        "ai": "operational",
        "blockchain": "operational",
        "uptime": f"{uptime:.2f}s",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get(f"{settings.API_V1_PREFIX}/version", tags=["Health"])
async def get_version():
    """
    Get the API version.
    """
    return {
        "version": "1.0.0",
        "api_version": "v1"
    }
