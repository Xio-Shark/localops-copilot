FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    nodejs \
    npm \
    ripgrep \
    sed \
    gawk \
  && npm install -g pnpm \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
