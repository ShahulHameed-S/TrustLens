import uuid
from sqlalchemy import Column, BigInteger, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base

class AssetMetadata(Base):
    __tablename__ = "asset_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), unique=True, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    exif_data = Column(JSONB, nullable=True)
    structural_data = Column(JSONB, nullable=True)

    asset = relationship("Asset", back_populates="metadata_rel")

    __table_args__ = (
        Index('idx_asset_metadata_exif_data', 'exif_data', postgresql_using='gin'),
    )
