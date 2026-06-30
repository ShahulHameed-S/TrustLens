import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.blockchain_repository import BlockchainRepository
from app.schemas.blockchain import (
    BlockchainProof,
    BlockchainValidationResult
)

logger = logging.getLogger(__name__)

SHA256_REGEX = re.compile(r"^[a-f0-9]{64}$")

class BlockchainEngine:
    def __init__(self):
        self.repository = BlockchainRepository()

    def _is_valid_sha256(self, hash_str: str) -> bool:
        return bool(hash_str and SHA256_REGEX.match(hash_str))
        
    def validate_sha256_hash(self, hash_value: str) -> bool:
        """Public method to validate SHA-256 hash"""
        return self._is_valid_sha256(hash_value)

    def generate_block_hash(self, payload_hash: str, previous_block_hash: str, timestamp: datetime, verification_id: Optional[UUID] = None) -> str:
        """
        Generate deterministic block hash.
        """
        payload = {
            "payload_hash": payload_hash,
            "previous_block_hash": previous_block_hash,
            "timestamp": timestamp.isoformat(),
            "verification_id": str(verification_id) if verification_id else None
        }
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def register_hash(self, db: Session, payload_hash: str, verification_id: Optional[UUID] = None) -> BlockchainProof:
        """
        Create a new blockchain block for a payload hash.
        """
        logger.info(f"Block registration started for payload hash {payload_hash}")
        
        if not self._is_valid_sha256(payload_hash):
            logger.error("Invalid hash input")
            raise ValueError("payload_hash must be a valid SHA-256 lowercase hex string.")

        latest_block = self.repository.get_latest_block(db)
        previous_block_hash = latest_block.block_hash if latest_block else "0"
        
        # Ensure UTC timezone for deterministic timestamping
        timestamp = datetime.now(timezone.utc)
        
        block_hash = self.generate_block_hash(payload_hash, previous_block_hash, timestamp, verification_id)
        
        block = self.repository.create_block(
            db=db,
            payload_hash=payload_hash,
            block_hash=block_hash,
            previous_block_hash=previous_block_hash,
            timestamp=timestamp,
            verification_id=verification_id
        )
        
        logger.info(f"Block registration completed. Block ID: {block.id}")
        
        return BlockchainProof(
            registered=True,
            block_id=block.id,
            block_hash=block.block_hash,
            previous_block_hash=block.previous_block_hash,
            payload_hash=block.payload_hash,
            timestamp=block.timestamp
        )

    def get_latest_block(self, db: Session):
        return self.repository.get_latest_block(db)

    def get_block_by_id(self, db: Session, block_id: int):
        return self.repository.get_block_by_id(db, block_id)

    def get_block_by_hash(self, db: Session, block_hash: str):
        return self.repository.get_block_by_hash(db, block_hash)

    def get_block_by_payload_hash(self, db: Session, payload_hash: str):
        return self.repository.get_block_by_payload_hash(db, payload_hash)

    def validate_chain(self, db: Session) -> BlockchainValidationResult:
        """
        Validate complete chain integrity.
        """
        logger.info("Block validation started")
        
        blocks = self.repository.get_all_blocks_ordered(db)
        total_blocks = len(blocks)
        
        if total_blocks == 0:
            logger.info("Block validation completed (Empty chain)")
            return BlockchainValidationResult(
                blockchain_valid=True,
                total_blocks=0,
                broken_block=None,
                message="Chain is empty and valid."
            )
            
        previous_hash = "0"
        
        for block in blocks:
            # Check linking
            if block.previous_block_hash != previous_hash:
                logger.error(f"Block validation failed at block {block.id}: previous hash mismatch")
                return BlockchainValidationResult(
                    blockchain_valid=False,
                    total_blocks=total_blocks,
                    broken_block=block.id,
                    message=f"Previous hash mismatch at block {block.id}. Expected {previous_hash}, got {block.previous_block_hash}."
                )
                
            # Recalculate block hash
            # Note: Ensure timezone info is preserved for ISO format output. 
            # If the DB returns naive datetime, assume UTC.
            dt = block.timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                
            recalculated_hash = self.generate_block_hash(
                payload_hash=block.payload_hash,
                previous_block_hash=block.previous_block_hash,
                timestamp=dt,
                verification_id=block.verification_id
            )
            
            # Constant time comparison is safer though standard == is fine for internal non-secret hashes
            if not hmac_compare(recalculated_hash, block.block_hash):
                logger.error(f"Block validation failed at block {block.id}: block hash mismatch")
                return BlockchainValidationResult(
                    blockchain_valid=False,
                    total_blocks=total_blocks,
                    broken_block=block.id,
                    message=f"Block hash mismatch at block {block.id}. Recalculated hash does not match stored hash."
                )
                
            previous_hash = block.block_hash
            
        logger.info("Block validation completed successfully")
        return BlockchainValidationResult(
            blockchain_valid=True,
            total_blocks=total_blocks,
            broken_block=None,
            message="Blockchain is fully valid."
        )

def hmac_compare(a: str, b: str) -> bool:
    import hmac
    return hmac.compare_digest(a, b)
