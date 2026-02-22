# LocalOps Copilot 架构

- Web(Next.js) 提供 Projects / Planner / Run Detail。
- API(FastAPI) 提供项目、计划、运行、检索、WS 与 metrics。
- Worker(Celery) 执行 run，调用 Docker sandbox，写入日志与产物。
- PostgreSQL 存储 projects/plans/runs/run_steps/audits/artifacts。
- Redis 作为 Celery broker/backend 与 WS 事件桥接入口。

数据流：Projects -> Planner 生成 Plan -> Runs 创建 AWAITING_REVIEW -> Approve 触发 Worker -> WS 实时日志 -> report/audit/diff 归档。
