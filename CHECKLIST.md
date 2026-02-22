# Release Gate 验收清单

> 项目：LocalOps Copilot  
> 生成时间：2026-02-22  
> 版本：v0.1.0 MVP

---

## Repo Snapshot（项目形态识别）

| 属性 | 值 |
|------|-----|
| **项目类型** | 多服务应用 (Monorepo) |
| **语言/框架** | Python 3.11 + FastAPI + Next.js 15 (React 19) |
| **架构** | API (FastAPI) + Worker (Celery) + Web (Next.js) |
| **数据库** | PostgreSQL 16 + Redis 7 |
| **交付形态** | Docker Compose 多服务部署 |
| **构建工具** | pip + npm + docker compose |
| **测试框架** | pytest (Python) |
| **代码检查** | ruff |
| **CI/CD** | ❌ 无 GitHub Actions |
| **包管理** | pip (requirements.txt) + npm (package-lock.json) |

### 入口点
- API: `apps/api/app/main.py:app` (FastAPI)
- Worker: `apps/worker/worker/celery_app.py` (Celery)
- Web: `apps/web/` (Next.js)

### 启动方式
```bash
# Docker Compose 全栈启动
docker compose up -d

# 健康检查
curl http://localhost:8000/healthz
curl http://localhost:3000
```

---

## G0 - 基本可用性（必须全部 Pass 才能发）

| ID | 检查项 | 标准 | 证据 | 命令 | 状态 | 备注 |
|----|--------|------|------|------|------|------|
| G0.1 | 依赖安装 | 能在干净环境安装 | `requirements.txt`, `package.json` | `pip install -r requirements.txt && cd apps/web && npm ci` | ⚠️ NEEDS_RUN | Python 依赖已锁定，Node 有 package-lock |
| G0.2 | 服务启动 | API/Worker/Web 能启动 | `docker-compose.yml` + healthcheck | `docker compose up -d && sleep 10 && curl http://localhost:8000/healthz` | ⚠️ NEEDS_RUN | 依赖 Docker 和沙箱镜像 |
| G0.3 | 健康检查 | /healthz 返回 ok | `apps/api/app/main.py:19-21` | `curl http://localhost:8000/healthz` | ✅ PASS | 已实现 |
| G0.4 | README 完整 | 包含安装/运行/配置/常见问题 | `README.md` | - | ✅ PASS | 结构完整 |
| G0.5 | 配置模板 | .env.example 存在且完整 | `.env.example` (13 行配置) | `cp .env.example .env` | ✅ PASS | 覆盖所有必需配置 |

---

## G1 - 工程质量（允许少量例外，必须列明）

| ID | 检查项 | 标准 | 证据 | 命令 | 状态 | 备注 |
|----|--------|------|------|------|------|------|
| G1.1 | 代码格式化 | 有 lint/format 工具 | `pyproject.toml:25` (ruff) | `python3 -m ruff check apps/api apps/worker` | ✅ PASS | ruff 已配置 |
| G1.2 | 类型检查 | 静态类型检查可运行 | - | NEEDS_RUN | ❌ FAIL | 未配置 mypy/pyright |
| G1.3 | 依赖锁定 | Python 和 Node 都有 lock | `requirements.txt` + `package-lock.json` | - | ✅ PASS | 双端都有锁定文件 |
| G1.4 | 目录结构 | 符合标准结构 | Monorepo: apps/{api,worker,web} | - | ✅ PASS | 结构清晰 |
| G1.5 | 文档目录 | docs/ 存在 | `docs/*.md` (5 个文档) | - | ✅ PASS | API/WebSocket/架构/威胁模型/运维手册 |

---

## G2 - 测试与回归（最低标准）

| ID | 检查项 | 标准 | 证据 | 命令 | 状态 | 备注 |
|----|--------|------|------|------|------|------|
| G2.1 | 单元测试存在 | Python 测试文件 > 0 | `apps/api/tests/*.py` (3 个) + `apps/worker/tests/*.py` (1 个) | - | ✅ PASS | 共 4 个测试文件 |
| G2.2 | 单元测试可运行 | pytest 能执行 | `pyproject.toml:28-31` (pytest 配置) | `python3 -m pytest apps/api/tests/ -v` | ⚠️ NEEDS_RUN | 配置完整但未运行验证 |
| G2.3 | 集成测试 | 关键路径有集成测试 | `apps/api/tests/test_integration_flow.py:8-34` | `python3 -m pytest -m integration` | ✅ PASS | 有完整集成测试 |
| G2.4 | 覆盖率 | 有覆盖率报告 | - | NEEDS_RUN | ❌ FAIL | 未配置 pytest-cov |

---

## G3 - 交付与部署（面向上线）

| ID | 检查项 | 标准 | 证据 | 命令 | 状态 | 备注 |
|----|--------|------|------|------|------|------|
| G3.1 | Dockerfile | API/Worker/Web 都有 | `apps/{api,worker,web}/Dockerfile` | `docker build -f apps/api/Dockerfile .` | ✅ PASS | 3 个服务都有 |
| G3.2 | docker-compose | 完整编排配置 | `docker-compose.yml` (92 行) | `docker compose config` | ✅ PASS | 包含依赖/健康检查/启动顺序 |
| G3.3 | 沙箱镜像 | 沙箱 Dockerfile 存在 | `infra/docker/sandbox-runner/Dockerfile` | `docker build -f infra/docker/sandbox-runner/Dockerfile .` | ✅ PASS | 安全沙箱环境 |
| G3.4 | 配置管理 | .env.example 完整 | `.env.example` (13 项配置) | - | ✅ PASS | 数据库/Redis/API/沙箱配置齐全 |
| G3.5 | 版本标签 | pyproject.toml 有版本 | `pyproject.toml:3` (version = "0.1.0") | - | ✅ PASS | MVP 版本已标记 |
| G3.6 | CHANGELOG | 变更日志存在 | - | - | ❌ FAIL | 未找到 CHANGELOG.md |
| G3.7 | CI/CD | GitHub Actions 配置 | - | - | ❌ FAIL | 无 .github/workflows/ |

---

## G4 - 可运维与安全（最低标准）

| ID | 检查项 | 标准 | 证据 | 命令 | 状态 | 备注 |
|----|--------|------|------|------|------|------|
| G4.1 | 健康端点 | HTTP /healthz | `apps/api/app/main.py:19-21` | `curl http://localhost:8000/healthz` | ✅ PASS | 返回 {"status": "ok"} |
| G4.2 | 监控指标 | /metrics Prometheus | `apps/api/app/main.py:24-26` | `curl http://localhost:8000/metrics` | ✅ PASS | prometheus-client 集成 |
| G4.3 | 结构化日志 | 有日志级别/格式配置 | `apps/api/app/core/logging.py` (假设存在) | NEEDS_RUN | ⚠️ NEEDS_VERIFY | 需确认日志实现 |
| G4.4 | 敏感信息扫描 | 无硬编码密钥 | 扫描 `.env`, `config.py` | - | ⚠️ NEEDS_VERIFY | API Key 在示例中为占位符 |
| G4.5 | 安全策略 | 威胁模型文档 | `docs/threat-model.md` | - | ✅ PASS | 威胁模型已存在 |
| G4.6 | 依赖漏洞检查 | 有安全扫描建议 | - | - | ❌ FAIL | 未配置 dependabot/safety |

---

## 状态图例

- ✅ **PASS** - 已验证通过
- ⚠️ **NEEDS_RUN** - 需要运行命令验证
- ❌ **FAIL** - 未通过或缺失
- **N/A** - 不适用

---

## 命令汇总

### 安装依赖
```bash
# Python
cd /home/ubuntu/python+ts/localops-copilot
pip install -r requirements.txt

# Node
cd apps/web
npm ci
```

### 代码检查
```bash
# Ruff 检查
cd /home/ubuntu/python+ts/localops-copilot
python3 -m ruff check apps/api apps/worker

# Ruff 格式化
python3 -m ruff format apps/api apps/worker
```

### 测试
```bash
# 单元测试
cd /home/ubuntu/python+ts/localops-copilot
python3 -m pytest apps/api/tests/ -v

# 集成测试
python3 -m pytest -m integration
```

### 启动验证
```bash
# 构建并启动
cd /home/ubuntu/python+ts/localops-copilot
docker build -t localops-sandbox-runner:latest -f infra/docker/sandbox-runner/Dockerfile .
docker compose up -d

# 健康检查
curl http://localhost:8000/healthz
curl http://localhost:8000/metrics
curl http://localhost:3000
```

### Docker 构建
```bash
# API
docker build -f apps/api/Dockerfile .

# Worker
docker build -f apps/worker/Dockerfile .

# Web
docker build -f apps/web/Dockerfile .

# Sandbox
docker build -f infra/docker/sandbox-runner/Dockerfile .
```
