# Runbook

## 启动

1. `cp .env.example .env`
2. `docker build -t localops-sandbox-runner:latest -f infra/docker/sandbox-runner/Dockerfile .`
3. `docker compose up --build`

## Demo

1. 打开 `http://localhost:3000`
2. 在 Projects 创建项目，`root_path` 可设为 `/workspace`
3. 进入 Planner，输入 `运行单测并生成报告`，生成 Plan，创建 Run
4. 打开 Run Detail，点击 Approve，观察实时日志和产物

## 排障

- API 健康检查：`GET http://localhost:8000/healthz`
- Prometheus 指标：`GET http://localhost:8000/metrics`
- Worker 日志：`docker compose logs -f worker`
- 若 sandbox 镜像缺失，先单独 build `localops-sandbox-runner:latest`
