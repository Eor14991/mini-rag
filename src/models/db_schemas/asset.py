from typing import Optional, Annotated
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

# Custom type to handle ObjectId validation and serialization
PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(lambda v: ObjectId(v) if isinstance(v, str) and ObjectId.is_valid(v) else v)
]

class Asset(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias='_id')
    asset_project_id: PyObjectId # Uses the custom type to automatically parse strings
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_size: Optional[int] = Field(default=None, gt=0)
    asset_config: Optional[dict] = Field(default=None)
    asset_pushed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Updated Pydantic V2 Config
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str} # Ensures ObjectId is converted to string for JSON responses
    )

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