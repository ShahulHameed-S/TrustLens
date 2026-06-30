import uuid
from sqlalchemy import Column, String, DateTime, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verification_id = Column(UUID(as_uuid=True), ForeignKey('verifications.id', ondelete='CASCADE'), unique=True, nullable=False)
    report_url = Column(String(512), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=text('NOW()'))

    verification = relationship("Verification", back_populates="report")
