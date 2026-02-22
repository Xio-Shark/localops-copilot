from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    root_path: str


class ProjectRead(BaseModel):
    id: int
    name: str
    root_path: str
    created_at: datetime

    model_config = {"from_attributes": True}
