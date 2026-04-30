from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field

class Asset(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias='_id')
    asset_project_id: ObjectId
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_size: Optional[int] = Field(default=None, gt=0)
    asset_config: Optional[dict] = Field(default=None)
    asset_pushed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

    @classmethod
    def get_indexes(cls) -> list[dict]:
        return [
            {
                "key": [("asset_project_id", 1)],
                "unique": False,
                "name": "asset_project_id_index"
            },
            {
                "key": [("asset_project_id", 1), ("asset_name", 1)],
                "unique": True,
                "name": "asset_project_id_name_index"
            },
        ]