# API 摘要

- `POST /v1/projects`
- `GET /v1/projects`
- `POST /v1/projects/{id}/plans`
- `POST /v1/projects/{id}/runs`
- `POST /v1/runs/{run_id}:approve`
- `POST /v1/runs/{run_id}:cancel`
- `GET /v1/runs/{run_id}`
- `POST /v1/projects/{id}/index:build`
- `POST /v1/projects/{id}/search`

示例：

```bash
curl -X POST "http://localhost:8000/v1/projects" \
  -H "x-api-key: localops-dev-key" \
  -H "content-type: application/json" \
  -d '{"name":"demo","root_path":"/workspace"}'
```
