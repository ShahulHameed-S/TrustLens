from pydantic import BaseModel, Field, ConfigDict
from pydantic.types import UUID4
from typing import Optional
from datetime import datetime

class BlockchainBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    verification_id: Optional[UUID4] = None
    payload_hash: str = Field(..., description="Valid SHA-256 lowercase hex string")
    block_hash: str = Field(..., description="Valid SHA-256 lowercase hex string")
    previous_block_hash: str = Field(..., description="Valid SHA-256 lowercase hex string")
    timestamp: datetime

class BlockchainProof(BaseModel):
    registered: bool
    block_id: int
    block_hash: str
    previous_block_hash: str
    payload_hash: str
    timestamp: datetime

class BlockchainValidationResult(BaseModel):
    blockchain_valid: bool
    total_blocks: int
    broken_block: Optional[int] = None
    message: str
    validated_at: datetime = Field(default_factory=datetime.utcnow)
