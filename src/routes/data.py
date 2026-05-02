import logging
import os
import json
import aiofiles
from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse

from controllers import DataController, ProjectController, ProcessController
from helpers import get_settings, Settings
from models import ProjectModel, ChunkModel, AssetModel
from models.db_schemas import DataChunk, Asset
from models.enums import AssetTypeEnum, ResponseSignal
from .schemas import ProcessRequest, ProcessFileRequest

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["mini-rag", "data"],
)


async def _process_file_core(request: Request,chunk_asset_id : object, project_id: str, project_db_id, file_id: str, chunk_size: int,
                             overlap_size: int):
    process_controller = ProcessController(project_id)
    chunk_model = await ChunkModel.create_instance(request.app.mongo_db)

    file_content = process_controller.get_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(
        file_content=file_content, file_id=file_id, chunk_size=chunk_size, overlap_size=overlap_size
    )

    if not file_chunks:
        return 0

    file_chunks_records = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i + 1,
            chunk_project_id=project_db_id,
            chunk_asset_id = chunk_asset_id,
        )
        for i, chunk in enumerate(file_chunks)
    ]

    return await chunk_model.insert_chunk_bulk(file_chunks_records, batch_size=150)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    project_model = await ProjectModel.create_instance(request.app.mongo_db)
    project = await project_model.get_project_or_create_project(project_id=project_id)

    data_controller = DataController()
    is_valid, result_signal = data_controller.val_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'signal': result_signal.value},
        )

    await file.seek(0)
    file_path, file_id = data_controller.generate_unique_filepath(orig_file_name=file.filename, project_id=project_id)

    try:
        async with aiofiles.open(file_path, mode='wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'signal': ResponseSignal.FILE_UPLOAD_FAILED.value},
        )

    asset_model = await AssetModel.create_instance(request.app.mongo_db)
    asset_resources = Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset_resources)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'signal': ResponseSignal.FILE_UPLOAD_SUCCESSFUL.value,
            'file_id': str(asset_record.id)
        },
    )


@data_router.post("/process/file/{project_id}")
async def process_single_file(request: Request, project_id: str, process_file_request: ProcessFileRequest):
    project_model = await ProjectModel.create_instance(request.app.mongo_db)
    project = await project_model.get_project_or_create_project(project_id=project_id)

    asset_model = await AssetModel.create_instance(request.app.mongo_db)
    # Require a method to get a single asset by name and project
    asset_record = await asset_model.get_asset(
        asset_name=process_file_request.file_id,
        asset_project_id=project.id
    )

    if not asset_record:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'signal': ResponseSignal.FILE_NOT_FOUND.value}  # Or appropriate not found signal
        )

    chunk_model = await ChunkModel.create_instance(request.app.mongo_db)

    if process_file_request.do_reset == 1:
        # Require a method to delete chunks by asset ID, NOT project ID
        await chunk_model.delete_chunk_by_asset_id(asset_id=asset_record.id)
        process_file_request.do_reset = 0

    num_records = await _process_file_core(
        request=request,
        chunk_asset_id=asset_record.id,
        project_id=project_id,
        project_db_id=project.id,
        file_id=process_file_request.file_id,
        chunk_size=process_file_request.chunk_size,
        overlap_size=process_file_request.overlap_size
    )

    if num_records == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'signal': ResponseSignal.FILE_CHUNKING_FAILED.value}
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'signal': ResponseSignal.FILE_CHUNKING_SUCCESSFUL.value,
            'chunks_count': num_records
        }
    )


@data_router.post("/process/{project_id}")
async def process_all_project_files(request: Request, project_id: str, process_request: ProcessRequest):
    asset_model = await AssetModel.create_instance(request.app.mongo_db)
    project_model = await ProjectModel.create_instance(request.app.mongo_db)
    project = await project_model.get_project_or_create_project(project_id=project_id)
    chunk_model = await ChunkModel.create_instance(request.app.mongo_db)

    process_files = await asset_model.get_all_project_assets(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
    )

    process_file_ids = { record.id :record.asset_name for record in process_files}

    if not process_file_ids:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'signal': ResponseSignal.PROJECT_NOT_FOUND.value}
        )

    if process_request.do_reset == 1:
        await chunk_model.delete_chunk_by_project_id(project_id=project.id)
        process_request.do_reset = 0

    total_records = 0
    for asset_id , file_id in process_file_ids.items():
        records_inserted = await _process_file_core(
            request=request,
            project_id=project_id,
            project_db_id=project.id,
            file_id=file_id,
            chunk_size=process_request.chunk_size,
            overlap_size=process_request.overlap_size,
            chunk_asset_id = asset_id
        )
        total_records += records_inserted

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'signal': ResponseSignal.FILE_CHUNKING_SUCCESSFUL.value,
            'chunks_count': total_records
        }
    )