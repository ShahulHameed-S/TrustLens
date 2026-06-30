import uuid
from sqlalchemy import Column, String, DateTime, text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=text('NOW()'))

    __table_args__ = (
        CheckConstraint("asset_type IN ('PDF', 'IMAGE', 'AUDIO')", name='chk_asset_type'),
    )

    user = relationship("User", back_populates="assets")
    metadata_rel = relationship("AssetMetadata", back_populates="asset", uselist=False, cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="asset", cascade="all, delete-orphan")
