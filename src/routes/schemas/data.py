from typing import Optional

from pydantic import BaseModel


class ProcessRequest(BaseModel):
    file_id: str
    chunk_size: Optional[int] = 800
    overlap_size: Optional[int] = 100
    do_reset: Optional[int] = 0
