# LocalOps Copilot

A secure, auditable local operations automation platform with sandboxed execution.

## Overview

LocalOps Copilot 是一个用于本地运维操作的自动化平台，提供以下核心功能：

- **项目管理**: 创建和管理项目，配置工作目录
- **计划生成**: 基于自然语言意图生成执行计划
- **审批工作流**: 执行前需人工审批，确保安全
- **沙箱执行**: 使用 Docker 沙箱隔离执行环境
- **实时日志**: WebSocket 推送执行日志
- **审计追踪**: 完整记录所有操作和产物

### Project Goals

本项目文档和实现围绕以下目标构建：

1. **安全优先**：所有命令在受限 Docker 沙箱中执行，并有策略引擎拦截高危命令。
2. **可审计**：每次运行必须可追踪，包含状态流转、日志、产物与审计记录。
3. **人机协作**：通过“计划 → 审批 → 执行”的流程降低误操作风险。
4. **本地优先**：核心组件可在本地一键拉起，便于开发和离线内网场景部署。

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Web UI    │────▶│  Next.js     │────▶│   API       │
│  (Port 3000)│     │   (Frontend) │     │ (Port 8000) │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌──────────────┐            │
                    │   Worker     │◄───────────┘
                    │   (Celery)   │    REST API
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌─────────┐ ┌──────────┐ ┌──────────┐
        │Postgres │ │  Redis   │ │  Docker  │
        │ (Data)   │ │ (Queue)  │ │ (Sandbox)│
        └─────────┘ └──────────┘ └──────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| API | FastAPI + SQLAlchemy | REST API, WebSocket, State Machine |
| Worker | Celery | Background task execution |
| Web | Next.js 15 + React | Frontend UI |
| Database | PostgreSQL 16 | Persistent storage |
| Queue | Redis 7 | Message broker |
| Sandbox | Docker | Isolated execution environment |

## Features

### State Machine

```
PENDING → PLANNED → AWAITING_REVIEW → RUNNING → SUCCEEDED/FAILED/CANCELLED
```

严格执行状态转换规则，禁止未审核执行。

### Command Policy

- **白名单**: `git`, `python`, `pytest`, `node`, `npm`, `pnpm`, `rg`, `sed`, `awk`, `echo`, `ls`, `pwd`
- **危险命令拦截**: `rm -rf /`, `mkfs`, `dd if=`, `chmod 777 /`
- **风险评估**: 基于命令类型和网络需求

### Docker Sandbox Security

```bash
--network=none              # 默认无网络访问
--cpus=1                   # CPU 限制
--memory=512m             # 内存限制
--pids-limit=128          # 进程数限制
--cap-drop=ALL            # 丢弃所有特权
--security-opt no-new-privileges  # 禁止提权
```

### WebSocket Events

- `run.status` - 运行状态变更
- `step.started` - 步骤开始
- `step.log` - 步骤日志
- `step.finished` - 步骤完成
- `artifact.created` - 产物创建
- `run.completed` - 运行完成

### Artifact Generation

每次运行自动生成：
- `report.md` - 执行报告
- `audit.json` - 审计日志
- `diff.patch` - 代码变更

## Quick Start

### Prerequisites

- Docker 29.2+
- Docker Compose v5.0+
- Node.js 20+
- Python 3.11+（推荐 3.12+）

> ⚠️ 项目代码使用了 `enum.StrEnum`（Python 3.11+），若使用 Python 3.10 运行测试会在导入阶段失败。

### Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd localops-copilot

# 2. Copy environment variables
cp .env.example .env

# 3. Build sandbox image
docker build -t localops-sandbox-runner:latest \
  -f infra/docker/sandbox-runner/Dockerfile .

# 4. Start all services
docker compose up -d

# 5. Verify services
curl http://localhost:8000/healthz  # API
curl http://localhost:3000          # Web UI
```

### Usage

最小可行路径（建议首次按此顺序验证）：

1. 访问 `http://localhost:3000` 并创建项目。
2. 在 Planner 输入自然语言意图并生成计划。
3. 创建 Run 后先审批，再执行。
4. 在 Run Detail 实时查看日志与状态。
5. 执行完成后检查报告、审计日志和代码差异产物。

详细步骤：

1. **访问 Web UI**: http://localhost:3000
2. **创建项目**: 输入项目名称和根目录
3. **生成计划**: 在 Planner 输入意图，如"运行单测并生成报告"
4. **创建运行**: 点击"创建 Run"
5. **审批执行**: 在 Run Detail 点击 "Approve"
6. **查看日志**: 实时日志通过 WebSocket 推送
7. **查看产物**: 在 Artifacts/Report/Diff 标签查看结果

### API Examples

```bash
# Create project
curl -X POST http://localhost:8000/v1/projects \
  -H "x-api-key: localops-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "demo-project", "root_path": "/workspace"}'

# Create plan
curl -X POST http://localhost:8000/v1/projects/1/plans \
  -H "x-api-key: localops-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"intent_text": "运行测试"}'

# Create run
curl -X POST http://localhost:8000/v1/projects/1/runs \
  -H "x-api-key: localops-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": 1}'

# Approve run
curl -X POST http://localhost:8000/v1/runs/1:approve \
  -H "x-api-key: localops-dev-key"

# Get run details
curl http://localhost:8000/v1/runs/1 \
  -H "x-api-key: localops-dev-key"
```

## Development

### Project Structure

```
localops-copilot/
├── apps/
│   ├── api/           # FastAPI backend
│   ├── worker/        # Celery worker
│   └── web/           # Next.js frontend
├── infra/
│   └── docker/        # Docker configurations
├── docs/              # Documentation
├── docker-compose.yml
└── README.md
```

### Running Tests

```bash
# Python tests
python3 -m pytest apps/api/tests/ -v

# Linting
python3 -m ruff check apps/api apps/worker

# Web build
cd apps/web && npm run build
```

### Configuration

Edit `.env` file:

```env
POSTGRES_USER=localops
POSTGRES_PASSWORD=localops
POSTGRES_DB=localops
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
API_KEY=localops-dev-key
API_PORT=8000
WEB_PORT=3000
WORKER_CONCURRENCY=1
ARTIFACT_ROOT=/workspace/data
SANDBOX_IMAGE=localops-sandbox-runner:latest
```

## Documentation

- [Architecture](docs/architecture.md) - 系统架构设计
- [API Reference](docs/api.md) - API 接口文档
- [WebSocket Protocol](docs/ws-protocol.md) - WebSocket 协议
- [Threat Model](docs/threat-model.md) - 威胁模型
- [Runbook](docs/runbook.md) - 运维手册

## Security

- 所有命令在 Docker 沙箱中隔离执行
- 危险命令被策略引擎自动拦截
- 完整审计日志记录所有操作
- 未审批任务禁止执行
- 细粒度权限控制

## License

MIT License - see LICENSE file for details.

## Contributors

- Built with ❤️ by LocalOps Team

## Support

For issues and feature requests, please open an issue on GitHub.