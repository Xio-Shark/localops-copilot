from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.models.plan import Plan
from app.db.models.project import Project
from app.db.session import get_db
from app.schemas.plan import PlanCreate, PlanRead
from app.services.planner.rule_planner import generate_plan
from app.state.machine import RunStatus, can_transition_run

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/v1/projects/{project_id}/plans", response_model=PlanRead)
def create_plan(project_id: int, payload: PlanCreate, db: Session = Depends(get_db)) -> Plan:
    project = db.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    plan_json = generate_plan(payload.intent_text)
    plan = Plan(project_id=project_id, intent_text=payload.intent_text, plan_json=plan_json)
    db.add(plan)
    db.commit()
    db.refresh(plan)

    if not can_transition_run(RunStatus.PENDING, RunStatus.PLANNED):
        raise HTTPException(status_code=500, detail="invalid run transition table")
    return plan
