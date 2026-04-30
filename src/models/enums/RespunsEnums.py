from enum import Enum


class RespunseSignal(Enum):
    FILE_TYPE_NOT_ALLOWED = "File type not allowed"
    FILE_SIZE_EXCEEDED = "File size exceeded"
    FILE_UPLOAD_SUCCESSFUL = "File upload successful"
    FILE_UPLOAD_FAILED = "File upload failed"
    FILE_CHUNKING_SUCCESSFUL = "File chunking successful"
    FILE_CHUNKING_FAILED = "File chunking failed"
