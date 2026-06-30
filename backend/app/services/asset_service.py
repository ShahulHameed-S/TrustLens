import os
import uuid
import hashlib
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.asset_repository import AssetRepository
from app.models.asset import Asset
from app.models.asset_metadata import AssetMetadata
from app.schemas.asset import AssetUploadData
from app.core.config import settings
from typing import Tuple, List

class AssetService:
    def __init__(self, db: Session):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.upload_dir = settings.UPLOAD_DIR
        
        # Ensure upload dir exists
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_file_type(self, mime_type: str) -> str:
        pdf_types = ["application/pdf"]
        image_types = ["image/jpeg", "image/png", "image/webp"]
        audio_types = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4"]
        
        if mime_type in pdf_types:
            return "PDF"
        elif mime_type in image_types:
            return "IMAGE"
        elif mime_type in audio_types:
            return "AUDIO"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {mime_type}"
            )

    def validate_file_size(self, file_size: int):
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
            )

    async def save_uploaded_file(self, file: UploadFile) -> Tuple[str, int, str]:
        # Generate safe unique filename
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        safe_filename = f"{uuid.uuid4()}{ext}"
        storage_path = os.path.join(self.upload_dir, safe_filename)
        
        sha256_hash = hashlib.sha256()
        file_size = 0
        
        with open(storage_path, "wb") as buffer:
            while chunk := await file.read(8192):
                sha256_hash.update(chunk)
                buffer.write(chunk)
                file_size += len(chunk)
                
                # Check size during stream to prevent DOS
                self.validate_file_size(file_size)
                
        # Reset file pointer
        await file.seek(0)
        
        return storage_path, file_size, sha256_hash.hexdigest()

    async def create_asset_record(self, user_id: uuid.UUID, file: UploadFile) -> AssetUploadData:
        # Validate basics
        asset_type = self.validate_file_type(file.content_type)
        
        # Save and Hash
        storage_path, file_size, file_hash = await self.save_uploaded_file(file)
        
        # Build Asset Model
        asset = Asset(
            user_id=user_id,
            original_filename=os.path.basename(file.filename) if file.filename else "unknown",
            asset_type=asset_type,
            file_hash=file_hash,
            storage_path=storage_path
        )
        created_asset = self.asset_repo.create_asset(asset)
        
        # Build Metadata Model
        metadata = AssetMetadata(
            asset_id=created_asset.id,
            file_size_bytes=file_size,
            mime_type=file.content_type,
            exif_data={},
            structural_data={}
        )
        self.asset_repo.create_asset_metadata(metadata)
        
        return AssetUploadData(
            asset_id=created_asset.id,
            filename=created_asset.original_filename,
            asset_type=created_asset.asset_type,
            file_hash=created_asset.file_hash,
            file_size_bytes=file_size,
            mime_type=file.content_type,
            uploaded_at=created_asset.uploaded_at
        )

    def list_user_assets(self, user_id: uuid.UUID, page: int, limit: int) -> Tuple[List[Asset], int]:
        return self.asset_repo.list_assets_paginated(user_id, page, limit)

    def get_asset_details(self, asset_id: uuid.UUID, user_id: uuid.UUID) -> Asset:
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        if asset.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return asset

    def delete_user_asset(self, asset_id: uuid.UUID, user_id: uuid.UUID):
        asset = self.get_asset_details(asset_id, user_id)
        
        # Delete from disk
        if os.path.exists(asset.storage_path):
            try:
                os.remove(asset.storage_path)
            except OSError:
                pass 
                
        # Delete from DB
        self.asset_repo.delete_asset(asset)
