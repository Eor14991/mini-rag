from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
import os
from helpers import get_settings, Settings
from controllers import DataController, ProjectController
from models import RespunseSignal
import aiofiles
import logging

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter()
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["mini-rag", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file:UploadFile,
                      app_settings: Settings = Depends(get_settings), ):
    #validate file
    data_controller = DataController()
    is_valid, result_signal = data_controller.val_uploaded_file(file=file)

    if not is_valid:
        return  JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'signal': result_signal.value,
            },
        )
    project_dir_path = ProjectController().get_project_path(project_id)
    file_path = data_controller.generate_unique_file_name(orig_file_name=file.filename, project_id=project_id)

    try:
        async with aiofiles.open(file_path, mode='wb') as f:
            while chunk:= await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)

    except Exception as e:
        logger.error(f"error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'signal': RespunseSignal.FILE_UPLOADED_FAILED.value,
            },
        )


    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'signal': RespunseSignal.FILE_UPLOADED_SUCCESSFULLY.value,
        },
    )



