from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from .helpers import get_settings
from .routes import base, data, nlp
from .stores.llm import LLMProviderFactory
from .stores.vectordb import VectorDBProviderFactory

@asynccontextmanager
async def startup_app(app: FastAPI):
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongo_db = app.mongo_conn[settings.MONGODB_DATABASE]

    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(settings)

    # generation clint
    app.generation_client = llm_provider_factory.create(
        provider=settings.ACTIVE_GENERATION_BACKEND)
    model_id = settings.GROK_GENERATION_MODEL if settings.ACTIVE_GENERATION_BACKEND == "GROK" else settings.COHERE_GENERATION_MODEL
    app.generation_client.get_generation_model(model_id=model_id)

    # embedding clint
    app.embedding_client = llm_provider_factory.create(
        provider=settings.ACTIVE_GENERATION_BACKEND)
    app.embedding_client.get_embedding_model(
        model_id=settings.EMBEDDING_MODEL_ID,
        embedding_size=settings.EMBEDDING_MODEL_SIZE
    )

    # vectordb clint

    app.vectordb_client = vectordb_provider_factory.create(
        provider=settings.VECTOR_DB_BACKEND)

    app.vectordb_client.connect()

    yield
    app.mongo_conn.close()
    app.vectordb_client.disconnect()


app = FastAPI(lifespan=startup_app)

app.include_router(base.base_router)
app.include_router(data.data_router)

app.include_router(nlp.nlp_router)