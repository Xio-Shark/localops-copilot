# Threat Model

- 执行隔离：每个 step 通过 `docker run` 在短生命周期容器执行。
- 默认无网：默认 `--network=none`。
- 资源限制：`--cpus=1 --memory=512m --pids-limit=128`。
- 降权：`--cap-drop=ALL --security-opt no-new-privileges`。
- 命令策略：白名单 + 危险模式拦截（`rm -rf /`, `mkfs`, `dd`）。
- 审计可追溯：command/cwd/env allowlist/exit code/stdout/stderr 均落库与文件。
