# WS Protocol

Endpoint: `WS /v1/ws/runs/{run_id}`

事件：

- `run.status`
  - `{ "event": "run.status", "run_id": 1, "status": "RUNNING" }`
- `step.started`
  - `{ "event": "step.started", "run_id": 1, "step_no": 1, "command": "pytest -q" }`
- `step.log`
  - `{ "event": "step.log", "run_id": 1, "step_no": 1, "stream": "stdout", "line": "..." }`
- `step.finished`
  - `{ "event": "step.finished", "run_id": 1, "step_no": 1, "status": "SUCCEEDED", "exit_code": 0 }`
- `artifact.created`
  - `{ "event": "artifact.created", "run_id": 1, "kind": "report", "path": ".../report.md" }`
- `run.completed`
  - `{ "event": "run.completed", "run_id": 1, "status": "SUCCEEDED" }`
