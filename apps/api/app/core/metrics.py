from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

run_duration_seconds = Histogram("run_duration_seconds", "Run duration in seconds", ["project_id"])
step_failures_total = Counter("step_failures_total", "Total failed steps", ["command"])
ws_connections_current = Gauge("ws_connections_current", "Current websocket connections")
