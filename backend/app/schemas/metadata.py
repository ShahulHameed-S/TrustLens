from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AssetType(str, Enum):
    PDF = "PDF"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    UNKNOWN = "UNKNOWN"

class MetadataResult(BaseModel):
    asset_type: AssetType = Field(..., description="The detected type of the asset")
    filename: str = Field(..., description="Original or resolved filename")
    extension: str = Field(..., description="File extension")
    mime_type: str = Field(..., description="MIME type of the file")
    size_bytes: int = Field(..., description="Size of the file in bytes")
    extracted_at: datetime = Field(..., description="Timestamp of metadata extraction")
    basic_metadata: Dict[str, Any] = Field(default_factory=dict, description="Basic extracted metadata")
    technical_metadata: Dict[str, Any] = Field(default_factory=dict, description="Advanced technical metadata")
    warnings: list[str] = Field(default_factory=list, description="Warnings generated during extraction")
