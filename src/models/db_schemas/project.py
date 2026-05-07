from typing import Optional, Annotated
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

# Custom type to handle ObjectId parsing
PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(lambda v: ObjectId(v) if isinstance(v, str) and ObjectId.is_valid(v) else v)
]

class Project(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias='_id')
    project_id: str = Field(..., min_length=1, pattern=r"^[.a-zA-Z0-9]+$")

    # Pydantic V2 Configuration
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str} # Ensures the ID serializes to a string in your API responses
    )

    @classmethod
    def get_indexes(cls) -> list[dict]:
        return [
            {
                "key": [("project_id", 1)],
                "unique": True,
                "name": "project_id_index"
            },
        ]