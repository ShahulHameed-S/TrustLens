import uuid
from sqlalchemy import Column, String, Numeric, DateTime, text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    trust_score = Column(Numeric(5, 2), nullable=True)
    risk_level = Column(String(20), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')", name='chk_verif_status'),
        CheckConstraint("trust_score >= 0.00 AND trust_score <= 100.00", name='chk_verif_trust_score'),
        CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name='chk_verif_risk_level'),
    )

    asset = relationship("Asset", back_populates="verifications")
    ai_analysis = relationship("AIAnalysis", back_populates="verification", uselist=False, cascade="all, delete-orphan")
    report = relationship("Report", back_populates="verification", uselist=False, cascade="all, delete-orphan")
    blockchain_blocks = relationship("BlockchainBlock", back_populates="verification")
