from __future__ import annotations

import re

ALLOWED_COMMANDS = {
    "git",
    "python",
    "pytest",
    "node",
    "pnpm",
    "npm",
    "rg",
    "sed",
    "awk",
    "echo",
    "ls",
    "pwd",
}

DANGEROUS_PATTERNS = [
    re.compile(r"\brm\s+-rf\s+/(\s|$)"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+if="),
    re.compile(r"\bchmod\s+777\s+/\b"),
]


def validate_command_policy(command: str) -> tuple[bool, str]:
    stripped_command = command.strip()
    if not stripped_command:
        return False, "empty command"

    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(stripped_command):
            return False, "dangerous pattern blocked"

    head_token = stripped_command.split()[0]
    if head_token not in ALLOWED_COMMANDS:
        return False, f"command '{head_token}' not in allowlist"
    return True, "ok"


def evaluate_risk(command: str, network_required: bool) -> str:
    if network_required:
        return "high"
    if any(token in command for token in ["git", "pnpm", "npm"]):
        return "medium"
    return "low"
