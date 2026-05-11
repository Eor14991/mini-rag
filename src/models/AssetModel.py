import math
from bson.objectid import ObjectId
from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from .enums import DataBaseEnum


class AssetModel(BaseDataModel):  # Standardized to PascalCase

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSETS_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_ASSETS_NAME.value not in all_collections:
            indexes = Asset.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index['key'],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_asset(self, asset: Asset):
        result = await self.collection.insert_one(
            asset.model_dump(by_alias=True, exclude_none=True)
        )

        asset.id = result.inserted_id
        return asset

    async def get_asset(self, asset_project_id: ObjectId, asset_name: str):
        record = await self.collection.find_one({
            "asset_project_id": asset_project_id,
            "asset_name": asset_name
        })
        if record is None:
            return None

        return Asset(**record)

    async def get_all_project_assets(self, asset_project_id: ObjectId, asset_type: str = "file") -> list[Asset]:
        cursor = self.collection.find({
            "asset_project_id": asset_project_id,
            "asset_type": asset_type
        })
        documents = await cursor.to_list(length=None)
        return [Asset(**doc) for doc in documents]