import os
import time

import httpx
import pytest


@pytest.mark.integration
def test_minimal_run_flow() -> None:
    api_base = os.getenv("IT_API_BASE")
    api_key = os.getenv("IT_API_KEY")
    if not api_base or not api_key:
        pytest.skip("integration env not set")

    client = httpx.Client(base_url=api_base, headers={"x-api-key": api_key}, timeout=20.0)
    project = client.post("/v1/projects", json={"name": "it-demo", "root_path": "/workspace"}).json()
    plan = client.post(f"/v1/projects/{project['id']}/plans", json={"intent_text": "运行单测并生成报告"}).json()
    run = client.post(f"/v1/projects/{project['id']}/runs", json={"plan_id": plan['id']}).json()
    approve = client.post(f"/v1/runs/{run['run_id']}:approve").json()
    assert approve["status"] == "RUNNING"

    deadline = time.time() + 60
    terminal = None
    while time.time() < deadline:
        detail = client.get(f"/v1/runs/{run['run_id']}").json()
        if detail["status"] in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            terminal = detail
            break
        time.sleep(2)

    assert terminal is not None
    assert len(terminal["steps"]) >= 1
    assert len(terminal["audits"]) >= 1
    assert len(terminal["artifacts"]) >= 2
