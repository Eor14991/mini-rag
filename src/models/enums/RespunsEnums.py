from enum import Enum


class ResponseSignal(Enum):
    CHUNKS_INSERTED = "Inserted chunks Successfully"
    FILE_TYPE_NOT_ALLOWED = "File type not allowed"
    FILE_SIZE_EXCEEDED = "File size exceeded"
    FILE_UPLOAD_SUCCESSFUL = "File upload successful"
    FILE_UPLOAD_FAILED = "File upload failed"
    FILE_CHUNKING_SUCCESSFUL = "File chunking successful"
    FILE_CHUNKING_FAILED = "File chunking failed"
    PROJECT_NOT_FOUND = "Project not found"
    FILE_NOT_FOUND = "File not found"
    CHUNKS_NOT_INSERTED = "Chunks not inserted"
    COLLECTION_NOT_FOUND = "Collection not found"
    COLLECTION_RETRIEVED = "Collection retrieved"
