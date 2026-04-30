from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class Project(BaseModel):
    id: Optional[ObjectId] = Field(None, alias='_id')
    project_id: str = Field(..., min_length=1, pattern=r"^[.a-zA-Z0-9]+$")

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
    @classmethod
    def get_indexes(cls) -> list[dict]:
        return [
            {
                "key": [("project_id", 1)],
                "unique": True,
                "name": "project_id_index"
            },
        ]
