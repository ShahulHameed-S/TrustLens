import uuid
from sqlalchemy import Column, String, DateTime, text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verification_id = Column(UUID(as_uuid=True), ForeignKey('verifications.id', ondelete='CASCADE'), unique=True, nullable=False)
    forensic_evidence = Column(JSONB, nullable=True)
    ai_explanation = Column(JSONB, nullable=True)
    model_version = Column(String(50), nullable=True)
    analyzed_at = Column(DateTime(timezone=True), server_default=text('NOW()'))

    verification = relationship("Verification", back_populates="ai_analysis")

    __table_args__ = (
        Index('idx_ai_analysis_forensic_evidence', 'forensic_evidence', postgresql_using='gin'),
    )
