from enum import Enum
class RespunseSignal(Enum):
    FILE_TYPE_NOT_ALLOWED = "file type not allowed"
    FILE_SIZE_TOO_EXCEEDED = "file size too large"
    FILE_UPLOADED_SUCCESSFULLY = "FILE UPLOADED SUCCESSFULLY"
    FILE_UPLOADED_FAILED = "FILE UPLOADED FAILED"
