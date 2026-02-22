from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.ws.manager import ws_manager
from app.core.security import require_api_key
from app.db.models.artifact import Artifact
from app.db.models.audit import Audit
from app.db.models.plan import Plan
from app.db.models.project import Project
from app.db.models.run import Run
from app.db.models.run_step import RunStep
from app.db.session import get_db
from app.schemas.run import RunActionResponse, RunCreate, RunRead
from app.services.tasks import celery_client
from app.state.machine import RunStatus, StepStatus, can_transition_run

router = APIRouter(dependencies=[Depends(require_api_key)])


def _validate_transition(current_status: str, target_status: RunStatus) -> None:
    if not can_transition_run(RunStatus(current_status), target_status):
        raise HTTPException(status_code=400, detail=f"invalid transition {current_status} -> {target_status.value}")


@router.post("/v1/projects/{project_id}/runs", response_model=RunActionResponse)
def create_run(project_id: int, payload: RunCreate, db: Session = Depends(get_db)) -> RunActionResponse:
    project = db.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    plan = db.scalar(select(Plan).where(Plan.id == payload.plan_id, Plan.project_id == project_id))
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")

    _validate_transition(RunStatus.PENDING.value, RunStatus.PLANNED)
    _validate_transition(RunStatus.PLANNED.value, RunStatus.AWAITING_REVIEW)

    run = Run(
        project_id=project_id,
        plan_id=plan.id,
        status=RunStatus.AWAITING_REVIEW.value,
        sandbox_meta={"network_default": "none", "cpus": 1, "memory": "512m", "pids_limit": 128},
        risk_level=plan.plan_json.get("risk_level", "medium"),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    commands = []
    for step_no, step in enumerate(plan.plan_json.get("steps", []), start=1):
        for command in step.get("commands", []):
            commands.append((step_no, step.get("type", "execute"), command))
    for idx, (step_no, step_type, command) in enumerate(commands, start=1):
        db.add(
            RunStep(
                run_id=run.id,
                step_no=idx,
                type=step_type,
                command=command,
                status=StepStatus.QUEUED.value,
            )
        )
    db.add(Audit(run_id=run.id, actor="user", action="run.created", payload_json={"plan_id": plan.id}))
    db.commit()
    return RunActionResponse(run_id=run.id, status=run.status)


@router.post("/v1/runs/{run_id}:approve", response_model=RunActionResponse)
def approve_run(run_id: int, db: Session = Depends(get_db)) -> RunActionResponse:
    run = db.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    _validate_transition(run.status, RunStatus.RUNNING)

    run.status = RunStatus.RUNNING.value
    run.started_at = datetime.now(timezone.utc)
    db.add(Audit(run_id=run.id, actor="user", action="run.approved", payload_json={}))
    db.commit()

    celery_client.send_task("worker.execute_run", kwargs={"run_id": run_id})
    return RunActionResponse(run_id=run.id, status=run.status)


@router.post("/v1/runs/{run_id}:cancel", response_model=RunActionResponse)
def cancel_run(run_id: int, db: Session = Depends(get_db)) -> RunActionResponse:
    run = db.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    _validate_transition(run.status, RunStatus.CANCELLED)
    run.status = RunStatus.CANCELLED.value
    run.finished_at = datetime.now(timezone.utc)
    db.add(Audit(run_id=run.id, actor="user", action="run.cancelled", payload_json={}))
    db.commit()
    return RunActionResponse(run_id=run.id, status=run.status)


@router.get("/v1/runs/{run_id}", response_model=RunRead)
def get_run(run_id: int, db: Session = Depends(get_db)) -> RunRead:
    run = db.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    steps = list(db.scalars(select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.step_no)).all())
    audits = list(db.scalars(select(Audit).where(Audit.run_id == run_id).order_by(Audit.id)).all())
    artifacts = list(db.scalars(select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.id)).all())

    report_content: str | None = None
    diff_content: str | None = None
    audit_content: str | None = None
    for artifact in artifacts:
        artifact_path = Path(artifact.path)
        if not artifact_path.exists():
            continue
        if artifact.kind == "report":
            report_content = artifact_path.read_text(encoding="utf-8", errors="ignore")
        elif artifact.kind == "diff":
            diff_content = artifact_path.read_text(encoding="utf-8", errors="ignore")
        elif artifact.kind == "audit":
            audit_content = artifact_path.read_text(encoding="utf-8", errors="ignore")

    return RunRead(
        id=run.id,
        project_id=run.project_id,
        plan_id=run.plan_id,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        sandbox_meta=run.sandbox_meta,
        risk_level=run.risk_level,
        steps=steps,
        audits=audits,
        artifacts=artifacts,
        report_content=report_content,
        diff_content=diff_content,
        audit_content=audit_content,
    )


@router.post("/v1/internal/runs/{run_id}/events")
async def post_run_event(run_id: int, payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, str]:
    run = db.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    await ws_manager.broadcast(run_id, payload)
    return {"status": "ok"}
