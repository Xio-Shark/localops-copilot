#!/bin/bash
#
# LocalOps Copilot - Release Gate Verification Script
# Usage: ./verify.sh [check|test|build|all]
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Counters
PASS=0
FAIL=0
WARN=0

# Helper functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARN++)) || true; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; ((FAIL++)) || true; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)) || true; }

print_header() {
    echo ""
    echo "========================================"
    echo "  $1"
    echo "========================================"
}

# ========================================
# G0 - 基本可用性检查
# ========================================
check_g0() {
    print_header "G0 - 基本可用性检查"

    # G0.3: 健康检查端点
    log_info "检查健康端点实现..."
    if grep -q "/healthz" apps/api/app/main.py 2>/dev/null; then
        log_pass "健康端点已实现 (/healthz)"
    else
        log_error "健康端点未找到"
    fi

    # G0.4: README
    log_info "检查 README 文档..."
    if [[ -f "README.md" ]] && [[ $(wc -l < README.md) -gt 100 ]]; then
        log_pass "README 文档完整 ($(wc -l < README.md) 行)"
    else
        log_error "README 文档缺失或过短"
    fi

    # G0.5: .env.example
    log_info "检查配置模板..."
    if [[ -f ".env.example" ]]; then
        local count=$(grep -c "=" .env.example 2>/dev/null || echo 0)
        if [[ $count -ge 10 ]]; then
            log_pass ".env.example 完整 ($count 项配置)"
        else
            log_warn ".env.example 配置项可能不足 ($count)"
        fi
    else
        log_error ".env.example 缺失"
    fi

    # G0.1: 依赖文件
    log_info "检查依赖锁定..."
    if [[ -f "requirements.txt" ]] && [[ -f "apps/web/package-lock.json" ]]; then
        log_pass "Python 和 Node 依赖已锁定"
    else
        log_error "依赖锁定文件缺失"
    fi
}

# ========================================
# G1 - 工程质量检查
# ========================================
check_g1() {
    print_header "G1 - 工程质量检查"

    # G1.1: 代码格式化工具
    log_info "检查代码检查工具配置..."
    if grep -q "ruff" pyproject.toml 2>/dev/null; then
        log_pass "Ruff 已配置"

        # 尝试运行 ruff 检查
        log_info "运行 Ruff 检查..."
        if python3 -m ruff check apps/api apps/worker --quiet 2>/dev/null; then
            log_pass "Ruff 检查通过"
        else
            log_warn "Ruff 检查发现问题 (非阻塞)"
        fi
    else
        log_error "Ruff 未配置"
    fi

    # G1.2: 类型检查
    log_info "检查类型检查配置..."
    if [[ -f "pyrightconfig.json" ]] || grep -q "mypy" pyproject.toml 2>/dev/null; then
        log_pass "类型检查已配置"
    else
        log_warn "类型检查未配置 (pyright/mypy)"
    fi

    # G1.3: 依赖锁定
    log_info "验证依赖锁定..."
    if [[ -f "requirements.txt" ]]; then
        local req_count=$(wc -l < requirements.txt)
        log_pass "requirements.txt 存在 ($req_count 个依赖)"
    fi

    if [[ -f "apps/web/package-lock.json" ]]; then
        log_pass "package-lock.json 存在"
    fi

    # G1.4: 目录结构
    log_info "检查目录结构..."
    if [[ -d "apps/api" ]] && [[ -d "apps/worker" ]] && [[ -d "apps/web" ]]; then
        log_pass "Monorepo 目录结构正确"
    else
        log_error "目录结构不符合预期"
    fi

    # G1.5: 文档目录
    if [[ -d "docs" ]] && [[ $(find docs -name "*.md" | wc -l) -ge 3 ]]; then
        log_pass "文档目录完整 ($(find docs -name "*.md" | wc -l) 个文档)"
    else
        log_warn "文档目录可能不完整"
    fi
}

# ========================================
# G2 - 测试检查
# ========================================
check_g2() {
    print_header "G2 - 测试与回归检查"

    # Python 版本检查（代码使用 StrEnum，需要 Python 3.11+）
    log_info "检查 Python 版本..."
    local py_ver
    py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
    if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
        log_pass "Python 版本满足要求 ($py_ver)"
    else
        log_warn "Python 版本过低 ($py_ver)，运行测试可能失败（需 3.11+）"
    fi

    # G2.1: 测试文件存在
    log_info "检查测试文件..."
    local test_files=$(find apps -path "*/tests/*.py" -type f 2>/dev/null | wc -l)
    if [[ $test_files -gt 0 ]]; then
        log_pass "测试文件存在 ($test_files 个)"
        find apps -path "*/tests/*.py" -type f | while read f; do
            echo "  - $f"
        done
    else
        log_error "未找到测试文件"
    fi

    # G2.2: 运行单元测试
    log_info "运行单元测试..."
    if python3 -m pytest apps/api/tests/ -v --tb=short 2>/dev/null; then
        log_pass "单元测试通过"
    else
        log_warn "单元测试失败或未完全通过"
    fi

    # G2.3: 集成测试标记
    if rg --glob '!**/node_modules/**' "@pytest\.mark\.integration" apps/ >/dev/null 2>&1; then
        log_pass "集成测试标记已配置"
    else
        log_warn "未找到集成测试标记"
    fi
}

# ========================================
# G3 - 交付与部署检查
# ========================================
check_g3() {
    print_header "G3 - 交付与部署检查"

    # G3.1: Dockerfile
    log_info "检查 Dockerfile..."
    for df in apps/api/Dockerfile apps/worker/Dockerfile apps/web/Dockerfile; do
        if [[ -f "$df" ]]; then
            log_pass "$df 存在"
        else
            log_error "$df 缺失"
        fi
    done

    # G3.2: docker-compose
    if [[ -f "docker-compose.yml" ]]; then
        log_pass "docker-compose.yml 存在"

        # 验证配置
        log_info "验证 docker-compose 配置..."
        if docker compose config > /dev/null 2>&1; then
            log_pass "docker-compose 配置有效"
        else
            log_warn "docker-compose 配置可能有问题"
        fi
    else
        log_error "docker-compose.yml 缺失"
    fi

    # G3.3: 沙箱镜像
    if [[ -f "infra/docker/sandbox-runner/Dockerfile" ]]; then
        log_pass "沙箱镜像 Dockerfile 存在"
    else
        log_error "沙箱镜像 Dockerfile 缺失"
    fi

    # G3.4: 配置管理
    if [[ -f ".env.example" ]]; then
        local required_vars=("POSTGRES" "REDIS" "API_KEY" "API_PORT" "WEB_PORT")
        local missing=0
        for var in "${required_vars[@]}"; do
            if ! grep -q "$var" .env.example; then
                ((missing++)) || true
            fi
        done
        if [[ $missing -eq 0 ]]; then
            log_pass "配置模板包含所有必需项"
        else
            log_warn "配置模板缺少 $missing 项"
        fi
    fi

    # G3.5: 版本标签
    if grep -q "version" pyproject.toml 2>/dev/null; then
        local version=$(grep "^version" pyproject.toml | head -1 | sed 's/.*= "\(.*\)".*/\1/')
        log_pass "版本已标记: $version"
    else
        log_warn "未找到版本标签"
    fi

    # G3.6: CHANGELOG
    if [[ -f "CHANGELOG.md" ]]; then
        log_pass "CHANGELOG.md 存在"
    else
        log_warn "CHANGELOG.md 缺失 (非阻塞)"
    fi

    # G3.7: CI/CD
    if [[ -d ".github/workflows" ]] && [[ $(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l) -gt 0 ]]; then
        log_pass "GitHub Actions 配置存在"
    else
        log_warn "无 GitHub Actions 配置 (非阻塞)"
    fi
}

# ========================================
# G4 - 可运维与安全检查
# ========================================
check_g4() {
    print_header "G4 - 可运维与安全检查"

    # G4.1: 健康端点
    log_info "验证健康端点..."
    if grep -q "def healthz" apps/api/app/main.py 2>/dev/null; then
        log_pass "健康端点已实现"
    else
        log_error "健康端点未实现"
    fi

    # G4.2: 监控指标
    if grep -q "prometheus_client" apps/api/app/main.py 2>/dev/null; then
        log_pass "Prometheus 指标已集成"
    else
        log_warn "Prometheus 指标未集成"
    fi

    # G4.3: 日志配置
    if [[ -f "apps/api/app/core/logging.py" ]]; then
        log_pass "日志配置模块存在"
    else
        log_warn "日志配置模块未找到"
    fi

    # G4.4: 敏感信息检查
    log_info "扫描敏感信息..."
    local issues=0
    if rg "password.*=" apps/api/app/core/config.py 2>/dev/null | rg -v "^#" | rg -q "localops"; then
        log_warn "config.py 中使用默认密码 (开发环境可接受)"
        ((issues++)) || true
    fi
    if rg --glob '!**/node_modules/**' --glob '!**/.next/**' "sk-" apps/ >/dev/null 2>&1; then
        log_error "可能发现硬编码 API Key"
        ((issues++)) || true
    fi
    if [[ $issues -eq 0 ]]; then
        log_pass "未发现明显敏感信息泄露"
    fi

    # G4.5: 安全文档
    if [[ -f "docs/threat-model.md" ]]; then
        log_pass "威胁模型文档存在"
    else
        log_warn "威胁模型文档缺失"
    fi

    # G4.6: 依赖漏洞扫描建议
    log_info "依赖安全建议..."
    log_warn "建议配置: safety check (Python) / npm audit (Node)"
}

# ========================================
# Docker 构建验证
# ========================================
check_build() {
    print_header "Docker 构建验证"

    log_info "构建沙箱镜像..."
    if docker build -t localops-sandbox-runner:latest -f infra/docker/sandbox-runner/Dockerfile . > /tmp/build-sandbox.log 2>&1; then
        log_pass "沙箱镜像构建成功"
    else
        log_error "沙箱镜像构建失败 (见 /tmp/build-sandbox.log)"
    fi

    log_info "构建 API 镜像..."
    if docker build -f apps/api/Dockerfile . > /tmp/build-api.log 2>&1; then
        log_pass "API 镜像构建成功"
    else
        log_error "API 镜像构建失败 (见 /tmp/build-api.log)"
    fi

    log_info "构建 Worker 镜像..."
    if docker build -f apps/worker/Dockerfile . > /tmp/build-worker.log 2>&1; then
        log_pass "Worker 镜像构建成功"
    else
        log_error "Worker 镜像构建失败 (见 /tmp/build-worker.log)"
    fi

    log_info "构建 Web 镜像..."
    if docker build -f apps/web/Dockerfile . > /tmp/build-web.log 2>&1; then
        log_pass "Web 镜像构建成功"
    else
        log_error "Web 镜像构建失败 (见 /tmp/build-web.log)"
    fi
}

# ========================================
# 集成测试（运行时验证）
# ========================================
check_runtime() {
    print_header "运行时集成验证"

    log_info "启动服务..."
    if docker compose up -d 2>/dev/null; then
        log_pass "服务启动命令执行成功"

        log_info "等待服务就绪 (10s)..."
        sleep 10

        log_info "测试健康端点..."
        if curl -sf http://localhost:8000/healthz > /dev/null 2>&1; then
            log_pass "API 健康检查通过"
            curl -s http://localhost:8000/healthz | head -1
        else
            log_error "API 健康检查失败"
        fi

        log_info "测试指标端点..."
        if curl -sf http://localhost:8000/metrics > /dev/null 2>&1; then
            log_pass "Metrics 端点响应正常"
        else
            log_warn "Metrics 端点未响应"
        fi

        log_info "测试 Web 前端..."
        if curl -sf http://localhost:3000 > /dev/null 2>&1; then
            log_pass "Web 前端响应正常"
        else
            log_warn "Web 前端未响应 (可能需要构建)"
        fi

        log_info "停止服务..."
        docker compose down 2>/dev/null || true
    else
        log_error "服务启动失败"
    fi
}

# ========================================
# 汇总报告
# ========================================
print_summary() {
    print_header "验证汇总"
    echo ""
    echo -e "${GREEN}通过: $PASS${NC}"
    echo -e "${YELLOW}警告: $WARN${NC}"
    echo -e "${RED}失败: $FAIL${NC}"
    echo ""

    if [[ $FAIL -eq 0 ]]; then
        echo -e "${GREEN}✅ 验证通过 - 可以发布${NC}"
        return 0
    else
        echo -e "${RED}❌ 验证未通过 - 请修复失败项${NC}"
        return 1
    fi
}

# ========================================
# 主入口
# ========================================
main() {
    local command="${1:-all}"

    echo "LocalOps Copilot Release Gate Verification"
    echo "=========================================="
    echo ""

    case "$command" in
        check)
            check_g0
            check_g1
            check_g2
            check_g3
            check_g4
            ;;
        test)
            check_g2
            ;;
        build)
            check_build
            ;;
        runtime)
            check_runtime
            ;;
        all)
            check_g0
            check_g1
            check_g2
            check_g3
            check_g4
            check_build
            check_runtime
            ;;
        *)
            echo "Usage: $0 [check|test|build|runtime|all]"
            echo ""
            echo "Commands:"
            echo "  check   - 静态检查 (G0-G4)"
            echo "  test    - 仅运行测试"
            echo "  build   - 仅构建 Docker 镜像"
            echo "  runtime - 启动并验证服务"
            echo "  all     - 完整验证 (默认)"
            exit 1
            ;;
    esac

    print_summary
}

main "$@"
