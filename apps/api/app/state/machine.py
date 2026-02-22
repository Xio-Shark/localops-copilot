from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    PENDING = "PENDING"
    PLANNED = "PLANNED"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


RUN_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.PENDING: {RunStatus.PLANNED, RunStatus.CANCELLED},
    RunStatus.PLANNED: {RunStatus.AWAITING_REVIEW, RunStatus.CANCELLED},
    RunStatus.AWAITING_REVIEW: {RunStatus.RUNNING, RunStatus.CANCELLED},
    RunStatus.RUNNING: {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.SUCCEEDED: set(),
    RunStatus.FAILED: set(),
    RunStatus.CANCELLED: set(),
}

STEP_TRANSITIONS: dict[StepStatus, set[StepStatus]] = {
    StepStatus.QUEUED: {StepStatus.RUNNING, StepStatus.SKIPPED},
    StepStatus.RUNNING: {StepStatus.SUCCEEDED, StepStatus.FAILED},
    StepStatus.SUCCEEDED: set(),
    StepStatus.FAILED: set(),
    StepStatus.SKIPPED: set(),
}


def can_transition_run(current: RunStatus, target: RunStatus) -> bool:
    return target in RUN_TRANSITIONS[current]


def can_transition_step(current: StepStatus, target: StepStatus) -> bool:
    return target in STEP_TRANSITIONS[current]
