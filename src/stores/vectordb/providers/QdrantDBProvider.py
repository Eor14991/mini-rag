import uuid
import logging
from typing import List

from pymongo import MongoClient
from qdrant_client import QdrantClient, models
from ..VectorDBEnums import DistanceMethodEnums
from ..VectorDBInterFace import VectorDBInterface


class QdrantDB(VectorDBInterface):

    def __init__(self, db_path: str, distance_method: str):
        self.client = None
        self.db_path = db_path

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger(__name__)

    def connect(self):
        # FIX: Only pass the path to the client. Distance method belongs to the collection.
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        # FIX: Implemented graceful shutdown instead of NotImplementedError
        if self.client:
            self.client.close()

    def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)

    def list_all_collections(self) -> List:
        return self.client.get_collections()

    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)

    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
           return self.client.delete_collection(collection_name=collection_name)
        else:
            self.logger.warning(f"Collection {collection_name} does not exist")
            return None

    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset:
           _= self.delete_collection(collection_name)
        if not self.is_collection_existed(collection_name):
            _= self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                ),
            )
        return True

    def insert_one(self, collection_name: str, text: str, vector: list, metadata: dict = None, record_id: str = None):
        if not self.is_collection_existed(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist")
            return None

        point_id = record_id if record_id is not None else str(uuid.uuid4())

        try:
            self.client.upload_points(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "metadata": metadata or {},
                            "text": text
                        }
                    )
                ],
            )
        except Exception as e:
            self.logger.error(f"Error while inserting point: {e}")
            return None
        return True

    def insert_many(self, collection_name: str, texts: list, vectors: list, metadata: list = None,
                    record_ids: list = None, batch_size: int = 50):
        if not self.is_collection_existed(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist")
            return False

        metadata = metadata or [{}] * len(texts)

        final_ids = []
        if record_ids:
            for r_id in record_ids:
                final_ids.append(r_id if r_id is not None else str(uuid.uuid4()))
        else:
            final_ids = [str(uuid.uuid4()) for _ in range(len(texts))]

        points = [
            models.PointStruct(
                id=final_ids[i],
                vector=vectors[i],
                payload={
                    "metadata": metadata[i] or {},
                    "text": texts[i]
                }
            )
            for i in range(len(texts))
        ]

        try:
            self.client.upload_points(
                collection_name=collection_name,
                points=points,
                batch_size=batch_size
            )
        except Exception as e:
            self.logger.error(f"Error while inserting points: {e}")
            return False

        return True

    def search_by_vector(self, collection_name: str, vector: list, limit: int):
        return self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        ).points