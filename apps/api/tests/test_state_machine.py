from app.state.machine import RunStatus, StepStatus, can_transition_run, can_transition_step


def test_run_transition_valid() -> None:
    assert can_transition_run(RunStatus.PENDING, RunStatus.PLANNED)
    assert can_transition_run(RunStatus.PLANNED, RunStatus.AWAITING_REVIEW)
    assert can_transition_run(RunStatus.AWAITING_REVIEW, RunStatus.RUNNING)
    assert can_transition_run(RunStatus.RUNNING, RunStatus.SUCCEEDED)


def test_run_transition_invalid() -> None:
    assert not can_transition_run(RunStatus.PENDING, RunStatus.RUNNING)
    assert not can_transition_run(RunStatus.SUCCEEDED, RunStatus.RUNNING)


def test_step_transition() -> None:
    assert can_transition_step(StepStatus.QUEUED, StepStatus.RUNNING)
    assert can_transition_step(StepStatus.RUNNING, StepStatus.FAILED)
    assert not can_transition_step(StepStatus.SUCCEEDED, StepStatus.RUNNING)
