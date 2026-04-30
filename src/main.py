from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from helpers import get_settings
from routes import base, data


@asynccontextmanager
async def startup_db_client(app: FastAPI):
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongo_db = app.mongo_conn[settings.MONGODB_DATABASE]

    yield
    app.mongo_conn.close()


app = FastAPI(lifespan=startup_db_client)

app.include_router(base.base_router)
app.include_router(data.data_router)
