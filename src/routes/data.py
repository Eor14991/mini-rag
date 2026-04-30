import logging

import aiofiles
from bson import ObjectId
from controllers import DataController, ProjectController, ProcessController
from models.enums import RespunseSignal
from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers import get_settings, Settings
from models import ProjectModel, ChunkModel,AssetModel
from models.db_schemas import DataChunk, Asset
from models.enums import AssetTypeEnum
import os
from .schemas import ProcessRequest

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter()
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["mini-rag", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings), ):
    project_model = await ProjectModel.create_instance(request.app.mongo_db)
    project = await project_model.get_project_or_create_project(project_id=project_id)
    # validate file
    data_controller = DataController()
    is_valid, result_signal = data_controller.val_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'signal': result_signal.value,
            },
        )
    file_path, file_id = data_controller.generate_unique_filepath(orig_file_name=file.filename, project_id=project_id)

    try:
        async with aiofiles.open(file_path, mode='wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)

    except Exception as e:
        logger.error(f"error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'signal': RespunseSignal.FILE_UPLOAD_FAILED.value,
            },
        )
    # create Asse
    asset_model = await AssetModel.create_instance(request.app.mongo_db)
    asset_resources =Asset(
    asset_project_id=project.id,
    asset_type=AssetTypeEnum.FILE.value,
    asset_name=file_id,
    asset_size=os.path.getsize(file_path)
    )

    asset_recor = await asset_model.create_asset(asset_resources)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'signal': RespunseSignal.FILE_UPLOAD_SUCCESSFUL.value,
            'file id': str(asset_recor.id)
        },
    )


@data_router.post("/process/{project_id}")
async def process_request(request: Request, project_id: str, process_request: ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_rest = process_request.do_reset

    process_controller = ProcessController(project_id)


    project_model = await ProjectModel.create_instance(request.app.mongo_db)
    chunk_model = await ChunkModel.create_instance(request.app.mongo_db)
    project = await project_model.get_project_or_create_project(project_id=project_id)

    file_content = process_controller.get_content(file_id=file_id)

    file_chunks = process_controller.process_file_content(
        file_content=file_content, file_id=file_id, chunk_size=chunk_size, overlap_size=overlap_size)

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'signal': RespunseSignal.FILE_CHUNKING_FAILED.value}
        )
    file_chunks_records = [DataChunk(
        chunk_text=chunk.page_content,
        chunk_metadata=chunk.metadata,
        chunk_order = i+1,
    chunk_project_id = project.id)
    for i,chunk in enumerate(file_chunks)]
    if do_rest ==1:
        _ = await chunk_model.delete_chunk_by_project_id(
            project_id=project_id
        )
    num_records = await chunk_model.inset_chunk_bulk(file_chunks_records, batch_size=150)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'signal': RespunseSignal.FILE_CHUNKING_SUCCESSFUL.value,
            'chunks count': num_records
        }
    )
