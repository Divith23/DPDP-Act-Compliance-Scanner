from pydantic import BaseModel
from typing import Any


class CrawlerResultResponse(BaseModel):
    scan_id: str
    data: dict[str, Any]
