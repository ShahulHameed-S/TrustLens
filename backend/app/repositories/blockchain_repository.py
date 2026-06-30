from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import Optional, List
from uuid import UUID

from app.models.blockchain_block import BlockchainBlock

class BlockchainRepository:
    def create_block(self, db: Session, payload_hash: str, block_hash: str, previous_block_hash: str, timestamp, verification_id: Optional[UUID] = None) -> BlockchainBlock:
        block = BlockchainBlock(
            verification_id=verification_id,
            payload_hash=payload_hash,
            block_hash=block_hash,
            previous_block_hash=previous_block_hash,
            timestamp=timestamp
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return block

    def get_latest_block(self, db: Session) -> Optional[BlockchainBlock]:
        return db.execute(
            select(BlockchainBlock).order_by(desc(BlockchainBlock.id)).limit(1)
        ).scalar_one_or_none()

    def get_block_by_id(self, db: Session, block_id: int) -> Optional[BlockchainBlock]:
        return db.execute(
            select(BlockchainBlock).where(BlockchainBlock.id == block_id)
        ).scalar_one_or_none()

    def get_block_by_hash(self, db: Session, block_hash: str) -> Optional[BlockchainBlock]:
        return db.execute(
            select(BlockchainBlock).where(BlockchainBlock.block_hash == block_hash)
        ).scalar_one_or_none()

    def get_block_by_payload_hash(self, db: Session, payload_hash: str) -> Optional[BlockchainBlock]:
        return db.execute(
            select(BlockchainBlock).where(BlockchainBlock.payload_hash == payload_hash)
        ).scalar_one_or_none()

    def get_all_blocks_ordered(self, db: Session) -> List[BlockchainBlock]:
        return list(db.execute(
            select(BlockchainBlock).order_by(BlockchainBlock.id)
        ).scalars().all())

    def get_blocks_paginated(self, db: Session, skip: int, limit: int, sort_by: str = "timestamp", order: str = "desc") -> List[BlockchainBlock]:
        stmt = select(BlockchainBlock)
        
        if sort_by == "timestamp":
            order_col = BlockchainBlock.timestamp
        else:
            order_col = BlockchainBlock.id
            
        if order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)
            
        return list(db.execute(stmt.offset(skip).limit(limit)).scalars().all())

    def get_total_blocks_count(self, db: Session) -> int:
        from sqlalchemy import func
        return db.execute(select(func.count()).select_from(BlockchainBlock)).scalar_one()
