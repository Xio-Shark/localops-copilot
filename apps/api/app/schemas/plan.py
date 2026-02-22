from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PlanCreate(BaseModel):
    intent_text: str


class PlanRead(BaseModel):
    id: int
    project_id: int
    intent_text: str
    plan_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
