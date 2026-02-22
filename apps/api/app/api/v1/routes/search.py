from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.models.project import Project
from app.db.session import get_db
from app.schemas.search import SearchRequest, SearchResult

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/v1/projects/{project_id}/index:build")
def build_index(project_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    project = db.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return {"status": "queued", "mode": "keyword", "project_id": str(project_id)}


@router.post("/v1/projects/{project_id}/search", response_model=list[SearchResult])
def search_project(project_id: int, payload: SearchRequest, db: Session = Depends(get_db)) -> list[SearchResult]:
    project = db.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    root_path = Path(project.root_path)
    if not root_path.exists():
        return []

    if payload.mode not in {"keyword", "vector", "hybrid"}:
        raise HTTPException(status_code=400, detail="unsupported mode")
    if payload.mode in {"vector", "hybrid"}:
        return []

    cmd = ["rg", "-n", payload.query, str(root_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    results: list[SearchResult] = []
    for line in proc.stdout.splitlines()[: payload.top_k]:
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        file_path, row_no, snippet = parts
        results.append(
            SearchResult(path=file_path, snippet=snippet, line_range=[int(row_no), int(row_no)], score=1.0)
        )
    return results
