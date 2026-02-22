from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    plan_id: int


class RunActionResponse(BaseModel):
    run_id: int
    status: str


class RunStepRead(BaseModel):
    id: int
    step_no: int
    type: str
    command: str
    status: str
    exit_code: int | None
    started_at: datetime | None
    finished_at: datetime | None
    stdout_path: str | None
    stderr_path: str | None

    model_config = {"from_attributes": True}


class AuditRead(BaseModel):
    id: int
    actor: str
    action: str
    payload_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactRead(BaseModel):
    id: int
    kind: str
    path: str
    sha256: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RunRead(BaseModel):
    id: int
    project_id: int
    plan_id: int | None
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    sandbox_meta: dict[str, Any] = Field(default_factory=dict)
    risk_level: str
    steps: list[RunStepRead] = Field(default_factory=list)
    audits: list[AuditRead] = Field(default_factory=list)
    artifacts: list[ArtifactRead] = Field(default_factory=list)
    report_content: str | None = None
    diff_content: str | None = None
    audit_content: str | None = None
