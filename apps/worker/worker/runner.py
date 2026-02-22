from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import select

from app.core.config import settings
from app.core.metrics import step_failures_total
from app.db.models.artifact import Artifact
from app.db.models.audit import Audit
from app.db.models.plan import Plan
from app.db.models.project import Project
from app.db.models.run import Run
from app.db.models.run_step import RunStep
from app.db.session import SessionLocal
from app.services.executor.policies import evaluate_risk, validate_command_policy
from app.state.machine import RunStatus, StepStatus, can_transition_run, can_transition_step
from worker.celery_app import celery_app


def _sha256_of_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        while True:
            block = handle.read(8192)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _emit_event(run_id: int, payload: dict) -> None:
    with httpx.Client(timeout=3.0) as client:
        client.post(
            f"{settings.api_base_url}/v1/internal/runs/{run_id}/events",
            headers={"x-api-key": settings.api_key},
            json=payload,
        )


def _docker_command(command: str, workspace: Path, needs_network: bool) -> list[str]:
    network_mode = "bridge" if needs_network else "none"
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        network_mode,
        "--cpus",
        "1.0",
        "--memory",
        "512m",
        "--pids-limit",
        "128",
        "--cap-drop=ALL",
        "--security-opt",
        "no-new-privileges",
        "-v",
        f"{workspace}:/workspace",
        "-w",
        "/workspace",
        settings.sandbox_image,
        "sh",
        "-lc",
        command,
    ]


def _write_artifact(db, run_id: int, kind: str, path: Path) -> None:
    if not path.exists():
        return
    db.add(
        Artifact(
            run_id=run_id,
            kind=kind,
            path=str(path),
            sha256=_sha256_of_file(path),
            size=path.stat().st_size,
        )
    )


def _generate_report(run: Run, steps: list[RunStep], report_path: Path) -> None:
    lines: list[str] = []
    lines.append(f"# Run {run.id} Report")
    lines.append("")
    lines.append(f"- status: {run.status}")
    lines.append(f"- risk_level: {run.risk_level}")
    lines.append(f"- started_at: {run.started_at}")
    lines.append(f"- finished_at: {run.finished_at}")
    lines.append("")
    lines.append("## Steps")
    for step in steps:
        lines.append(f"- step {step.step_no}: {step.command} => {step.status} (exit={step.exit_code})")
    failed_steps = [step for step in steps if step.status == StepStatus.FAILED.value]
    if failed_steps:
        lines.append("")
        lines.append("## Failure")
        for step in failed_steps:
            lines.append(f"- step {step.step_no} failed")
    lines.append("")
    lines.append("## Next")
    if failed_steps:
        lines.append("- review stderr logs and fix command or source code")
    else:
        lines.append("- review generated artifacts and finalize")
    report_path.write_text("\n".join(lines), encoding="utf-8")


@celery_app.task(name="worker.execute_run")
def execute_run(run_id: int) -> None:
    db = SessionLocal()
    temp_workspace: Path | None = None
    try:
        run = db.scalar(select(Run).where(Run.id == run_id))
        if run is None:
            return
        plan = db.scalar(select(Plan).where(Plan.id == run.plan_id))
        project = db.scalar(select(Project).where(Project.id == run.project_id))
        if plan is None or project is None:
            run.status = RunStatus.FAILED.value
            db.add(Audit(run_id=run.id, actor="worker", action="run.failed", payload_json={"reason": "missing plan or project"}))
            db.commit()
            return

        if not can_transition_run(RunStatus(run.status), RunStatus.RUNNING):
            run.status = RunStatus.RUNNING.value
            run.started_at = datetime.now(timezone.utc)

        data_root = Path(settings.artifact_root)
        logs_dir = data_root / "logs" / str(run.id)
        reports_dir = data_root / "reports" / str(run.id)
        artifacts_dir = data_root / "artifacts" / str(run.id)
        logs_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        temp_workspace = Path(tempfile.mkdtemp(prefix=f"run-{run.id}-"))
        source_root = Path(project.root_path)
        if source_root.exists():
            shutil.copytree(source_root, temp_workspace, dirs_exist_ok=True)

        steps = list(db.scalars(select(RunStep).where(RunStep.run_id == run.id).order_by(RunStep.step_no)).all())
        _emit_event(run.id, {"event": "run.status", "run_id": run.id, "status": RunStatus.RUNNING.value})

        run_failed = False
        for step in steps:
            if not can_transition_step(StepStatus(step.status), StepStatus.RUNNING):
                continue

            ok, reason = validate_command_policy(step.command)
            if not ok:
                step.status = StepStatus.FAILED.value
                step.exit_code = 126
                step.finished_at = datetime.now(timezone.utc)
                step_failures_total.labels(command=step.command.split()[0] if step.command else "unknown").inc()
                db.add(
                    Audit(
                        run_id=run.id,
                        actor="worker",
                        action="command.blocked",
                        payload_json={"step_no": step.step_no, "command": step.command, "reason": reason},
                    )
                )
                _emit_event(
                    run.id,
                    {
                        "event": "step.finished",
                        "run_id": run.id,
                        "step_no": step.step_no,
                        "status": step.status,
                        "exit_code": step.exit_code,
                    },
                )
                run_failed = True
                break

            step.status = StepStatus.RUNNING.value
            step.started_at = datetime.now(timezone.utc)
            db.add(step)
            db.commit()

            _emit_event(
                run.id,
                {"event": "step.started", "run_id": run.id, "step_no": step.step_no, "command": step.command},
            )

            stdout_path = logs_dir / f"{step.step_no}.out"
            stderr_path = logs_dir / f"{step.step_no}.err"
            docker_cmd = _docker_command(step.command, temp_workspace, False)
            process = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            collected_lines: list[str] = []
            if process.stdout is not None:
                for line in process.stdout:
                    stripped = line.rstrip("\n")
                    collected_lines.append(stripped)
                    _emit_event(
                        run.id,
                        {
                            "event": "step.log",
                            "run_id": run.id,
                            "step_no": step.step_no,
                            "stream": "stdout",
                            "line": stripped,
                        },
                    )
            return_code = process.wait()

            stdout_path.write_text("\n".join(collected_lines), encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")

            step.stdout_path = str(stdout_path)
            step.stderr_path = str(stderr_path)
            step.exit_code = return_code
            step.finished_at = datetime.now(timezone.utc)
            step.status = StepStatus.SUCCEEDED.value if return_code == 0 else StepStatus.FAILED.value
            db.add(step)

            db.add(
                Audit(
                    run_id=run.id,
                    actor="worker",
                    action="step.executed",
                    payload_json={
                        "step_no": step.step_no,
                        "command": step.command,
                        "cwd": "/workspace",
                        "env_allowlist": ["PATH", "HOME"],
                        "exit_code": return_code,
                        "risk": evaluate_risk(step.command, False),
                        "sandbox": {
                            "network": "none",
                            "cpus": "1.0",
                            "memory": "512m",
                            "pids_limit": "128",
                        },
                    },
                )
            )

            _emit_event(
                run.id,
                {
                    "event": "step.finished",
                    "run_id": run.id,
                    "step_no": step.step_no,
                    "status": step.status,
                    "exit_code": return_code,
                },
            )

            if return_code != 0:
                step_failures_total.labels(command=step.command.split()[0] if step.command else "unknown").inc()
                run_failed = True
                db.commit()
                break

            db.commit()

        run.finished_at = datetime.now(timezone.utc)
        run.status = RunStatus.FAILED.value if run_failed else RunStatus.SUCCEEDED.value

        report_path = reports_dir / "report.md"
        audit_path = artifacts_dir / "audit.json"
        diff_path = artifacts_dir / "diff.patch"

        steps = list(db.scalars(select(RunStep).where(RunStep.run_id == run.id).order_by(RunStep.step_no)).all())
        _generate_report(run, steps, report_path)

        audit_records = [
            {
                "step_no": step.step_no,
                "command": step.command,
                "status": step.status,
                "exit_code": step.exit_code,
                "stdout_path": step.stdout_path,
                "stderr_path": step.stderr_path,
            }
            for step in steps
        ]
        audit_path.write_text(
            json.dumps(
                {
                    "run_id": run.id,
                    "status": run.status,
                    "timeline": audit_records,
                    "sandbox": run.sandbox_meta,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        diff_cmd = ["git", "-C", str(temp_workspace), "diff"]
        diff_proc = subprocess.run(diff_cmd, capture_output=True, text=True, check=False)
        diff_path.write_text(diff_proc.stdout, encoding="utf-8")

        _write_artifact(db, run.id, "report", report_path)
        _emit_event(run.id, {"event": "artifact.created", "run_id": run.id, "kind": "report", "path": str(report_path)})
        _write_artifact(db, run.id, "audit", audit_path)
        _emit_event(run.id, {"event": "artifact.created", "run_id": run.id, "kind": "audit", "path": str(audit_path)})
        _write_artifact(db, run.id, "diff", diff_path)
        _emit_event(run.id, {"event": "artifact.created", "run_id": run.id, "kind": "diff", "path": str(diff_path)})

        db.add(Audit(run_id=run.id, actor="worker", action="run.completed", payload_json={"status": run.status}))
        db.add(run)
        db.commit()

        _emit_event(run.id, {"event": "run.completed", "run_id": run.id, "status": run.status})
    finally:
        db.close()
        if temp_workspace is not None and temp_workspace.exists():
            shutil.rmtree(temp_workspace, ignore_errors=True)
