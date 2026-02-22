# 给下一个 Agent 的继续执行 Prompt（详细版）

你现在接手的是 `localops-copilot` 项目，目标是把当前 MVP 从“代码基本齐全”推进到“可在 Docker 环境完整演示并通过验收清单”。

## 1. 你要先理解的当前状态

当前仓库已完成以下核心内容：

- Monorepo 骨架、Compose、API/Worker/Web 三个应用目录。
- FastAPI 端点、状态机、审计与产物表、Alembic 初始化迁移。
- Worker 执行链：命令策略校验 -> Docker sandbox 执行 -> WS 事件推送 -> report/audit/diff 产物写入。
- Next.js 三页：Projects、Planner、Run Detail（含 Approve/Cancel、实时日志、Artifacts/Diff/Report 展示）。
- 文档：`docs/architecture.md`、`docs/threat-model.md`、`docs/runbook.md`、`docs/ws-protocol.md`、`docs/api.md`、`docs/openapi.yaml`。
- 单元测试通过，前端 build 通过。

已验证结果（可复查）：

- `python -m pytest` -> `7 passed, 1 skipped`（集成测试在无运行服务时跳过）。
- `python -m ruff check apps/api apps/worker` -> 通过。
- `npm run build`（`apps/web`）-> 通过。

阻塞点：

- 当前执行环境无 Docker 可执行文件（`docker: command not found`），所以尚未完成真实 `docker compose up` 的端到端在线验收。

## 2. 关键文件索引（先读这些）

先阅读以下文件再动手，避免重复造轮子：

- `docker-compose.yml`
- `.env.example`
- `infra/docker/sandbox-runner/Dockerfile`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/runs.py`
- `apps/api/app/services/executor/policies.py`
- `apps/api/app/state/machine.py`
- `apps/api/alembic/versions/0001_init.py`
- `apps/worker/worker/runner.py`
- `apps/web/app/page.tsx`
- `apps/web/app/planner/page.tsx`
- `apps/web/app/runs/[id]/page.tsx`
- `apps/api/tests/test_integration_flow.py`
- `docs/runbook.md`

## 3. 本轮必须完成的任务（按顺序）

### 任务 A：先把 Docker 在线验收跑通

1. 在支持 Docker 的环境执行：
   - `cp .env.example .env`
   - `docker build -t localops-sandbox-runner:latest -f infra/docker/sandbox-runner/Dockerfile .`
   - `docker compose up --build`
2. 确认服务状态：
   - API 健康：`GET /healthz`
   - Metrics：`GET /metrics`
   - Web 首页可访问。
3. 观察 Worker 日志，确认 Celery 启动成功并可消费任务。

### 任务 B：执行一条完整 Demo 流程并留证据

1. 在 Web 创建项目（root_path 指向容器内存在路径）。
2. 在 Planner 输入 demo intent：`运行单测并生成报告`。
3. 创建 run 后进入 Run Detail 点击 Approve。
4. 验证 WS 实时日志连续出现 `step.log`。
5. run 完成后验证：
   - 页面可见 Artifacts/Diff/Report。
   - 数据库存在 `runs/run_steps/audits/artifacts` 对应记录。
6. 另外执行一次“危险命令”场景（可通过构造 plan step 命令 `rm -rf /`），验证被策略拒绝并写入 audit。

### 任务 C：补齐验收细节中的薄弱点（如未满足）

重点检查以下是否与需求完全一致：

- Plan -> Review -> Run：是否严格禁止未审核执行。
- run_steps 审计字段：是否包含 command/cwd/env allowlist/stdout/stderr/exit_code/duration。
- Docker 沙箱参数：
  - `--network=none` 默认
  - `--cpus` / `--memory` / `--pids-limit`
  - `--cap-drop=ALL`
  - `--security-opt no-new-privileges`
- WS 事件全集：
  - `run.status`
  - `step.started`
  - `step.log`
  - `step.finished`
  - `artifact.created`
  - `run.completed`
- 三类产物必须自动归档：`report.md`、`audit.json`、`diff.patch`。

### 任务 D：集成测试升级为“可在线通过”

当前 `test_integration_flow.py` 在无环境变量时会 skip。你需要在 CI 或本地 docker 环境下让它真正运行并通过：

1. 设置 `IT_API_BASE` 和 `IT_API_KEY`。
2. 确保测试结束前可轮询到终态。
3. 断言 artifacts/audits/steps 实际存在，不只检查长度。

## 4. 可直接复制给执行 Agent 的操作指令

你是接手实现与验收的工程 Agent。请只做以下工作并给出证据：

1. 在支持 Docker 的环境启动当前仓库。
2. 跑通 Web 端完整流程：Projects -> Planner -> Run Detail(Approve) -> 实时日志 -> 产物展示。
3. 使用数据库查询验证 `runs/run_steps/audits/artifacts` 的完整落库。
4. 构造危险命令案例，证明命令策略能阻断并记录 audit。
5. 若发现任何未达标项，做最小改动修复并重新验收。
6. 输出最终验收报告：
   - 运行命令
   - 关键截图或日志要点
   - 每条验收项的 PASS/FAIL
   - 修改文件清单

禁止事项：

- 不要删减已有测试来“让它通过”。
- 不要跳过状态机约束。
- 不要绕过命令白名单/危险拦截。
- 不要添加与本项目目标无关的新功能。

## 5. 建议的验收命令清单

在仓库根目录执行：

- `cp .env.example .env`
- `docker build -t localops-sandbox-runner:latest -f infra/docker/sandbox-runner/Dockerfile .`
- `docker compose up --build`
- `python -m pytest`
- `python -m ruff check apps/api apps/worker`
- `cd apps/web && npm run build`

## 6. 最终交付格式（让面试展示可直接复用）

请输出：

1. 一段 1-2 句话总览（是否完全达标）。
2. 按验收条目逐项给出 PASS/FAIL 和证据位置。
3. 修改过的文件路径列表。
4. 一条 demo intent 和最短复现步骤（不超过 6 步）。

---

如果你只做一件事，优先确保 **Docker 在线端到端演示** 真正跑通并留证据，因为当前代码基础已经齐全，剩下的核心是“运行证明”。
