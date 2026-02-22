export type RunStatus =
  | "PENDING"
  | "PLANNED"
  | "AWAITING_REVIEW"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELLED";

export type StepStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "SKIPPED";
