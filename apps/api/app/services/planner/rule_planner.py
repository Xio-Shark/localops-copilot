from __future__ import annotations

from typing import Any


def _test_plan(intent: str) -> dict[str, Any]:
    return {
        "version": "1.0",
        "intent": intent,
        "risk_level": "low",
        "assumptions": ["项目测试命令可用"],
        "steps": [
            {
                "id": "s1",
                "type": "inspect",
                "title": "检查工作区",
                "commands": ["git status"],
                "dangerous": False,
                "network_required": False,
            },
            {
                "id": "s2",
                "type": "execute",
                "title": "运行测试",
                "commands": ["pytest -q"],
                "dangerous": False,
                "network_required": False,
            },
        ],
        "outputs": ["report.md", "audit.json", "diff.patch"],
    }


def _build_plan(intent: str) -> dict[str, Any]:
    return {
        "version": "1.0",
        "intent": intent,
        "risk_level": "low",
        "assumptions": ["项目支持构建命令"],
        "steps": [
            {
                "id": "s1",
                "type": "inspect",
                "title": "检查依赖",
                "commands": ["node -v", "pnpm -v"],
                "dangerous": False,
                "network_required": False,
            },
            {
                "id": "s2",
                "type": "execute",
                "title": "构建项目",
                "commands": ["pnpm build"],
                "dangerous": False,
                "network_required": False,
            },
        ],
        "outputs": ["report.md", "audit.json", "diff.patch"],
    }


def _search_log_plan(intent: str) -> dict[str, Any]:
    return {
        "version": "1.0",
        "intent": intent,
        "risk_level": "low",
        "assumptions": ["日志文件可读"],
        "steps": [
            {
                "id": "s1",
                "type": "inspect",
                "title": "搜索错误日志",
                "commands": ["rg -n \"error|exception|traceback\" ."],
                "dangerous": False,
                "network_required": False,
            }
        ],
        "outputs": ["report.md", "audit.json", "diff.patch"],
    }


def generate_plan(intent: str) -> dict[str, Any]:
    lowered_intent = intent.lower()
    if "单测" in intent or "测试" in intent or "test" in lowered_intent:
        return _test_plan(intent)
    if "构建" in intent or "build" in lowered_intent:
        return _build_plan(intent)
    if "日志" in intent or "error" in lowered_intent or "错误" in intent:
        return _search_log_plan(intent)
    return {
        "version": "1.0",
        "intent": intent,
        "risk_level": "medium",
        "assumptions": ["按最小风险执行"],
        "steps": [
            {
                "id": "s1",
                "type": "inspect",
                "title": "检查目录结构",
                "commands": ["rg -n \"TODO|FIXME\" ."],
                "dangerous": False,
                "network_required": False,
            }
        ],
        "outputs": ["report.md", "audit.json", "diff.patch"],
    }
