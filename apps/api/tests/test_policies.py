from app.services.executor.policies import validate_command_policy


def test_allowlist_command_allowed() -> None:
    ok, reason = validate_command_policy("pytest -q")
    assert ok is True
    assert reason == "ok"


def test_dangerous_command_blocked() -> None:
    ok, reason = validate_command_policy("rm -rf /")
    assert ok is False
    assert "blocked" in reason


def test_unknown_command_blocked() -> None:
    ok, reason = validate_command_policy("curl https://example.com")
    assert ok is False
    assert "allowlist" in reason
