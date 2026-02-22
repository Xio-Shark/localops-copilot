"use client";

import Link from "next/link";
import { useState } from "react";
import { apiFetch } from "../../lib/api";

type Plan = {
  id: number;
  project_id: number;
  intent_text: string;
  plan_json: {
    risk_level: string;
    steps: Array<{ id: string; type: string; title: string; commands: string[] }>;
  };
};

type RunResponse = {
  run_id: number;
  status: string;
};

export default function PlannerPage() {
  const [projectId, setProjectId] = useState("1");
  const [intentText, setIntentText] = useState("运行单测并生成报告");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [run, setRun] = useState<RunResponse | null>(null);
  const [error, setError] = useState("");

  async function generatePlan() {
    try {
      const result = await apiFetch<Plan>(`/v1/projects/${projectId}/plans`, {
        method: "POST",
        body: JSON.stringify({ intent_text: intentText }),
      });
      setPlan(result);
      setRun(null);
      setError("");
    } catch (err) {
      setError(String(err));
    }
  }

  async function createRun() {
    if (!plan) {
      return;
    }
    try {
      const result = await apiFetch<RunResponse>(`/v1/projects/${projectId}/runs`, {
        method: "POST",
        body: JSON.stringify({ plan_id: plan.id }),
      });
      setRun(result);
      setError("");
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <main>
      <div className="panel">
        <h2>Planner</h2>
        <label>
          项目 ID
          <input value={projectId} onChange={(event) => setProjectId(event.target.value)} />
        </label>
        <label>
          Intent
          <textarea value={intentText} rows={4} onChange={(event) => setIntentText(event.target.value)} />
        </label>
        <button onClick={generatePlan}>生成 Plan</button>
      </div>

      {plan ? (
        <div className="panel">
          <h3>Plan JSON</h3>
          <div className="muted">risk_level: {plan.plan_json.risk_level}</div>
          {plan.plan_json.steps.map((step, index) => (
            <div key={step.id} className="panel">
              <strong>
                Step {index + 1}: {step.title}
              </strong>
              <div className="muted">{step.type}</div>
              <pre>{JSON.stringify(step.commands, null, 2)}</pre>
            </div>
          ))}
          <button onClick={createRun}>创建 Run（AWAITING_REVIEW）</button>
        </div>
      ) : null}

      {run ? (
        <div className="panel">
          <div>
            run_id: {run.run_id}, status: {run.status}
          </div>
          <Link href={`/runs/${run.run_id}`}>前往 Run 详情</Link>
        </div>
      ) : null}

      {error ? <div style={{ color: "#b00020" }}>{error}</div> : null}
    </main>
  );
}
