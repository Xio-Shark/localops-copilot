"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch, API_BASE, API_KEY } from "../../../lib/api";

type Step = {
  id: number;
  step_no: number;
  type: string;
  command: string;
  status: string;
  exit_code: number | null;
  started_at: string | null;
  finished_at: string | null;
};

type Audit = { id: number; actor: string; action: string; payload_json: Record<string, unknown> };
type Artifact = { id: number; kind: string; path: string; sha256: string; size: number };

type RunDetail = {
  id: number;
  status: string;
  steps: Step[];
  audits: Audit[];
  artifacts: Artifact[];
  report_content: string | null;
  diff_content: string | null;
  audit_content: string | null;
};

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const runId = useMemo(() => Number(params.id), [params.id]);
  const [run, setRun] = useState<RunDetail | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"artifacts" | "diff" | "report">("artifacts");

  async function loadRun() {
    try {
      const data = await apiFetch<RunDetail>(`/v1/runs/${runId}`);
      setRun(data);
      setError("");
    } catch (err) {
      setError(String(err));
    }
  }

  useEffect(() => {
    void loadRun();
    const timer = setInterval(() => {
      void loadRun();
    }, 2000);
    return () => clearInterval(timer);
  }, [runId]);

  useEffect(() => {
    const wsBase = API_BASE.replace("http://", "ws://").replace("https://", "wss://");
    const ws = new WebSocket(`${wsBase}/v1/ws/runs/${runId}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as { event: string; line?: string; status?: string };
      const logLine = data.line;
      if (data.event === "step.log" && typeof logLine === "string") {
        setLogs((prev) => [...prev, logLine]);
      }
      if (data.event === "run.completed" || data.event === "run.status") {
        void loadRun();
      }
    };
    ws.onopen = () => {
      ws.send("subscribe");
    };
    ws.onerror = () => setError("websocket 连接失败");
    return () => ws.close();
  }, [runId]);

  async function approveRun() {
    try {
      await fetch(`${API_BASE}/v1/runs/${runId}:approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": API_KEY },
      });
      await loadRun();
    } catch (err) {
      setError(String(err));
    }
  }

  async function cancelRun() {
    try {
      await fetch(`${API_BASE}/v1/runs/${runId}:cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": API_KEY },
      });
      await loadRun();
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <main className="grid grid-2">
      <section className="panel">
        <h2>Run #{runId}</h2>
        <div>状态: {run?.status ?? "-"}</div>
        <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
          <button onClick={approveRun}>Approve</button>
          <button className="danger" onClick={cancelRun}>
            Cancel
          </button>
        </div>
        <h3>Steps</h3>
        {(run?.steps ?? []).map((step) => (
          <div key={step.id} className="panel">
            <div>
              #{step.step_no} {step.command}
            </div>
            <div className="muted">
              {step.status} / exit={String(step.exit_code)}
            </div>
          </div>
        ))}
      </section>

      <section>
        <div className="panel">
          <h3>实时日志</h3>
          <div className="log">{logs.join("\n") || "等待日志..."}</div>
        </div>

        <div className="panel">
          <h3>Tabs</h3>
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            <button className={tab === "artifacts" ? "" : "secondary"} onClick={() => setTab("artifacts")}>Artifacts</button>
            <button className={tab === "diff" ? "" : "secondary"} onClick={() => setTab("diff")}>Diff</button>
            <button className={tab === "report" ? "" : "secondary"} onClick={() => setTab("report")}>Report</button>
          </div>
          {tab === "artifacts" ? (
            <div>
              {(run?.artifacts ?? []).map((artifact) => (
                <div key={artifact.id} className="muted">
                  {artifact.kind}: {artifact.path}
                </div>
              ))}
              <pre>{run?.audit_content ?? ""}</pre>
            </div>
          ) : null}
          {tab === "diff" ? <pre>{run?.diff_content ?? "暂无 diff"}</pre> : null}
          {tab === "report" ? <pre>{run?.report_content ?? "暂无 report"}</pre> : null}
        </div>

        <div className="panel">
          <h3>Audit</h3>
          {(run?.audits ?? []).map((audit) => (
            <div key={audit.id} className="muted">
              {audit.actor} / {audit.action}
            </div>
          ))}
        </div>

        {error ? <div style={{ color: "#b00020" }}>{error}</div> : null}
      </section>
    </main>
  );
}
