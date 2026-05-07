import logging
import os
import json
from urllib import request

import aiofiles
from bson import ObjectId
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from .schemas.nlp import PushRequest, SearchRequest
from ..models import ProjectModel, ResponseSignal, ChunkModel
from ..controllers import NLPController

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["mini-rag", "nlp"],
)


@nlp_router.post("/indx/push/{project_id}")
async def index_push_project(request: Request, project_id: str, push_request: PushRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongo_db
    )

    project = await project_model.get_project_or_create_project(
        project_id=project_id,
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.mongo_db
    )


    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND.value,
            }
        )
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
    )

    has_records = True
    page_number = 1
    inserted_counts = 0

    while has_records:
        pag_chunks = await chunk_model.get_project_chunks(project_id=project.id, page_number= page_number)


        if not pag_chunks or len(pag_chunks) == 0:
            has_records = False
            break
        page_number += 1

        is_inserted = nlp_controller.index_into_vectordb(
            project= project,
            chunks=pag_chunks,
            do_rest= bool(push_request.do_rest)
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.CHUNKS_NOT_INSERTED.value,
                }
            )

        inserted_counts+=len(pag_chunks)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"signal": ResponseSignal.CHUNKS_INSERTED.value,
                 "counts": inserted_counts
    })




@nlp_router.get("/indx/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongo_db
    )

    project = await project_model.get_project_or_create_project(
        project_id=project_id,
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
    )

    collection_info = nlp_controller.get_vectordb_collection_info(
        project=project,
    )

    if not collection_info:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.COLLECTION_NOT_FOUND.value,
            }
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.COLLECTION_RETRIEVED.value,
            "collection_info": collection_info,
        }
    )



@nlp_router.post("/indx/search/{project_id}")
async def index_push_project(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.mongo_db
    )

    project = await project_model.get_project_or_create_project(
        project_id=project_id,
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
    )

    results = nlp_controller.search_vectordb_collection(
        project=project,
        text=search_request.text,
        limit=search_request.limit,
    )
    if not results:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.COLLECTION_NOT_FOUND.value,
            }
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.COLLECTION_RETRIEVED.value,
            "results": [result['payload']['text'] for result in results],
        }
    )