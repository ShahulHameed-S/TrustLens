from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.asset_metadata import AssetMetadata
from uuid import UUID
from typing import Tuple, List

class AssetRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create_asset(self, asset: Asset) -> Asset:
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset
        
    def create_asset_metadata(self, metadata: AssetMetadata) -> AssetMetadata:
        self.db.add(metadata)
        self.db.commit()
        self.db.refresh(metadata)
        return metadata

    def get_by_id(self, asset_id: UUID) -> Asset:
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def get_by_hash(self, file_hash: str) -> Asset:
        return self.db.query(Asset).filter(Asset.file_hash == file_hash).first()

    def get_by_user(self, user_id: UUID) -> List[Asset]:
        return self.db.query(Asset).filter(Asset.user_id == user_id).all()
        
    def list_assets_paginated(self, user_id: UUID, page: int, limit: int) -> Tuple[List[Asset], int]:
        query = self.db.query(Asset).filter(Asset.user_id == user_id)
        total = query.count()
        items = query.order_by(Asset.uploaded_at.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    def delete_asset(self, asset: Asset):
        self.db.delete(asset)
        self.db.commit()
