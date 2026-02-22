# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI/CD pipeline with GitHub Actions
- Test coverage reporting with pytest-cov
- Type checking configuration with Pyright
- Security scanning with Trivy

## [0.1.0] - 2026-02-22

### Added
- Initial MVP release of LocalOps Copilot
- **API Service** (FastAPI):
  - RESTful API with versioning (v1)
  - WebSocket support for real-time execution logs
  - State machine for run lifecycle management (PENDING → PLANNED → AWAITING_REVIEW → RUNNING → SUCCEEDED/FAILED/CANCELLED)
  - Health check endpoint (`/healthz`)
  - Prometheus metrics endpoint (`/metrics`)
  - PostgreSQL database integration with SQLAlchemy
  - Alembic database migrations
  - Command policy engine with allowlist and dangerous command blocking
  
- **Worker Service** (Celery):
  - Background task execution with Celery
  - Docker sandbox runner for isolated execution
  - Command sandboxing with security policies
  
- **Web Frontend** (Next.js 15):
  - React-based UI with TypeScript
  - Project management interface
  - Plan creation and execution flow
  - Real-time WebSocket log streaming
  - Artifact and report viewing
  
- **Infrastructure**:
  - Docker Compose configuration for full stack
  - Sandbox Dockerfile with security hardening
  - PostgreSQL 16 and Redis 7 services
  - Health checks and service dependencies
  
- **Documentation**:
  - README with quick start guide
  - API documentation
  - WebSocket protocol documentation
  - Architecture documentation
  - Threat model documentation
  - Runbook for operations
  
- **Testing**:
  - Unit tests for policies, state machine
  - Integration tests for end-to-end flow
  - Test coverage reporting
  
- **Security**:
  - Command whitelist/blacklist policy
  - Docker sandbox with no network access
  - Resource limits (CPU, memory, PIDs)
  - Security hardening flags
  - Audit logging

### Security
- All commands execute in isolated Docker sandbox
- Dangerous commands automatically blocked (rm -rf /, mkfs, dd, chmod 777 /, etc.)
- Resource isolation with Docker security options
- Review-before-execution workflow

[0.1.0]: https://github.com/Xio-Shark/localops-copilot/releases/tag/v0.1.0
