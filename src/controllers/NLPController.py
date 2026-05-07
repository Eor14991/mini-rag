import os
import re
import json

from ..models.db_schemas import Project,DataChunk
from ..stores.llm.LLMEnums import DocumentTypeEnum


from .BaseController import BaseController


class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()

    def reset_vectordb_collection(self, project: Project):
        collection_name = self.create_collection_name(project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vectordb_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project.project_id)
        collection_info =  self.vectordb_client.get_collection_info(collection_name=collection_name)
        if not collection_info:
            return False
        if hasattr(collection_info, "model_dump"):
            # Pydantic V2
            return collection_info.model_dump()

        return collection_info
    def index_into_vectordb(self, project: Project,
                            chunks: list[DataChunk], do_rest: bool = False):

        # get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # manage_collection
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]

        vectors = [
            self.embedding_client.embed_text(
                text=text, document_type = DocumentTypeEnum.DOCUMENT.value)
           for text in texts
        ]

        # create_collection
        _= self.vectordb_client.create_collection(
            collection_name = collection_name,
            embedding_size= self.embedding_client.embedding_size,
            do_reset= do_rest,
        )

        # insert into vectordb
        _= self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
        )

        return True

    def search_vectordb_collection(self, project: Project, text: str, limit: int = 10):

        collection_name = self.create_collection_name(project_id=project.project_id)

        vector = self.embedding_client.embed_text(
            text=text, document_type = DocumentTypeEnum.QUERY.value)

        if not vector or len(vector) == 0:
            return False

        results = self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit,
        )

        if not results:
            return []

        if hasattr(results[0], "model_dump"):
            return [res.model_dump() for res in results]

        return results
