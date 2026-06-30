from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.database.session import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.services.blockchain_engine import BlockchainEngine
from app.schemas.blockchain import BlockchainBlockResponse, BlockchainValidationResult
from app.services.audit_log_service import AuditLogService
from app.schemas.audit_log import AuditAction

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])

def format_error(code: str, message: str, details: dict = None):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }

def format_success(data: dict):
    return {
        "success": True,
        "data": data
    }

@router.get("", response_model=dict)
def list_blockchain_blocks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("timestamp", regex="^(timestamp|id)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    engine = BlockchainEngine()
    skip = (page - 1) * limit
    
    blocks = engine.repository.get_blocks_paginated(
        db=db, skip=skip, limit=limit, sort_by=sort, order=order
    )
    total = engine.repository.get_total_blocks_count(db)
    
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    
    items = [BlockchainBlockResponse.model_validate(block).model_dump(mode="json") for block in blocks]
    
    return format_success({
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    })

@router.get("/blocks/{block_id}", response_model=dict)
def get_block_by_id(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    engine = BlockchainEngine()
    block = engine.get_block_by_id(db, block_id)
    if not block:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content=format_error("BLOCK_NOT_FOUND", f"Block with ID {block_id} not found")
        )
        
    return format_success(BlockchainBlockResponse.model_validate(block).model_dump(mode="json"))

@router.get("/hash/{hash}", response_model=dict)
def search_by_hash(
    hash: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    engine = BlockchainEngine()
    
    if not engine.validate_sha256_hash(hash):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content=format_error("INVALID_HASH", "Provided hash is not a valid SHA-256 string")
        )

    # First check payload hash
    block = engine.get_block_by_payload_hash(db, hash)
    if block:
        proof = {
            "registered": True,
            "block_id": block.id,
            "block_hash": block.block_hash,
            "previous_block_hash": block.previous_block_hash,
            "payload_hash": block.payload_hash,
            "timestamp": block.timestamp.isoformat()
        }
        return format_success({
            "type": "proof",
            "proof": proof
        })
        
    # Check block hash
    block = engine.get_block_by_hash(db, hash)
    if block:
        return format_success({
            "type": "block",
            "block": BlockchainBlockResponse.model_validate(block).model_dump(mode="json")
        })
        
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content=format_error("HASH_NOT_FOUND", f"No block found with hash {hash}")
    )

@router.get("/validate", response_model=dict)
def validate_blockchain(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    engine = BlockchainEngine()
    validation_result = engine.validate_chain(db)
    
    # Prompt asks for:
    # {
    #   "success": true,
    #   "data": {
    #     "blockchain_valid": true,
    #     "total_blocks": 0,
    #     "broken_block": null,
    #     "message": "...",
    #     "validated_at": "timestamp"
    #   }
    # }
    
    # Even if valid is false, the request was successful in checking it.
    
    if not validation_result.blockchain_valid:
        # According to requirements we might need to return a specific error code?
        # "Required error cases: ... BLOCKCHAIN_VALIDATION_FAILED"
        # Wait, the prompt says "Return: { success: true, data: { blockchain_valid: true... } }"
        # If it's valid, it returns the data. If it fails, maybe still return success: true with blockchain_valid: false?
        # Actually it says required error cases: BLOCKCHAIN_VALIDATION_FAILED. Let's return error if invalid.
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content=format_error(
                "BLOCKCHAIN_VALIDATION_FAILED",
                validation_result.message,
                {
                    "total_blocks": validation_result.total_blocks,
                    "broken_block": validation_result.broken_block,
                    "validated_at": validation_result.validated_at.isoformat()
                }
            )
        )
    
    AuditLogService().log_event(
        db=db,
        action=AuditAction.BLOCKCHAIN_VALIDATED,
        user_id=current_user.id,
        resource_type="BLOCKCHAIN",
        resource_id="CHAIN"
    )
    
    return format_success(validation_result.model_dump(mode="json"))
