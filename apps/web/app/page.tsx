"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type Project = {
  id: number;
  name: string;
  root_path: string;
  created_at: string;
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("demo-project");
  const [rootPath, setRootPath] = useState("/workspace");
  const [error, setError] = useState<string>("");

  async function loadProjects() {
    try {
      const data = await apiFetch<Project[]>("/v1/projects");
      setProjects(data);
      setError("");
    } catch (err) {
      setError(String(err));
    }
  }

  useEffect(() => {
    void loadProjects();
  }, []);

  async function createProject() {
    try {
      await apiFetch<Project>("/v1/projects", {
        method: "POST",
        body: JSON.stringify({ name, root_path: rootPath }),
      });
      await loadProjects();
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <main>
      <div className="panel">
        <h2>Projects Dashboard</h2>
        <label>
          项目名
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <label>
          根路径
          <input value={rootPath} onChange={(event) => setRootPath(event.target.value)} />
        </label>
        <button onClick={createProject}>新建项目</button>
      </div>

      <div className="panel">
        <h3>项目列表</h3>
        {projects.length === 0 ? <p className="muted">暂无项目</p> : null}
        {projects.map((project) => (
          <div key={project.id} className="panel" style={{ marginBottom: 8 }}>
            <div>
              <strong>{project.name}</strong> (ID: {project.id})
            </div>
            <div className="muted">{project.root_path}</div>
          </div>
        ))}
        {error ? <p style={{ color: "#b00020" }}>{error}</p> : null}
      </div>
    </main>
  );
}
