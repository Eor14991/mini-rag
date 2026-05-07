from .providers import QdrantDB
from .VectorDBEnums import VectorDBEnums
from ...helpers.config import Settings
from ...controllers.BaseController import BaseController


class VectorDBFactory:
    def __init__(self, config: Settings):
        self.config = config
        self.base_controller = BaseController()

    def create(self, provider: str) -> QdrantDB:
        if provider == VectorDBEnums.QDRANT.value:
            return QdrantDB(
                db_path=self.base_controller.get_database_path(provider),
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )

        raise ValueError(f"Unsupported Vector DB provider: '{provider}'")