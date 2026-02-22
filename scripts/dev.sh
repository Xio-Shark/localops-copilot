#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  cp .env.example .env
fi

docker build -t localops-sandbox-runner:latest -f infra/docker/sandbox-runner/Dockerfile .
docker compose up --build
