from typing import Optional

from pydantic import BaseModel


class ProcessFileRequest(BaseModel):
    file_id: str
    chunk_size: Optional[int] = 800
    overlap_size: Optional[int] = 100
    do_reset: Optional[int] = 0

class ProcessRequest(BaseModel):
    chunk_size: Optional[int] = 800
    overlap_size: Optional[int] = 100
    do_reset: Optional[int] = 0
