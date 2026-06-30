from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class AssetMetadataResponse(BaseModel):
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    exif_data: Optional[Dict[str, Any]] = None
    structural_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class AssetResponse(BaseModel):
    id: UUID
    user_id: UUID
    original_filename: str
    asset_type: str
    file_hash: str
    uploaded_at: datetime
    metadata_rel: Optional[AssetMetadataResponse] = None

    model_config = ConfigDict(from_attributes=True)

class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    page: int
    limit: int

class AssetUploadData(BaseModel):
    asset_id: UUID
    filename: str
    asset_type: str
    file_hash: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: datetime
