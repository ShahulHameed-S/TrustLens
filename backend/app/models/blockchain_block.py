from sqlalchemy import Column, BigInteger, String, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class BlockchainBlock(Base):
    __tablename__ = "blockchain_blocks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    verification_id = Column(UUID(as_uuid=True), ForeignKey('verifications.id', ondelete='SET NULL'), nullable=True)
    payload_hash = Column(String(64), nullable=False)
    block_hash = Column(String(64), unique=True, nullable=False)
    previous_block_hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=text('NOW()'))

    verification = relationship("Verification", back_populates="blockchain_blocks")
