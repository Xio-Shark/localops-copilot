from __future__ import annotations

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    mode: str = "keyword"
    top_k: int = 10


class SearchResult(BaseModel):
    path: str
    snippet: str
    line_range: list[int]
    score: float
