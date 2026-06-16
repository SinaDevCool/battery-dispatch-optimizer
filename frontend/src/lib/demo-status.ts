export type FriendlyStatusTone = "amber" | "blue" | "emerald" | "red" | "slate";

const statusLabels: Record<string, string> = {
  blocked: "Production gated",
  client_ready: "Client-ready",
  complete: "Complete",
  completed: "Complete",
  draft: "Draft",
  error: "Action failed",
  failed: "Failed",
  fallback: "Fallback data",
  invalid: "Invalid",
  live: "Live",
  missing: "Missing evidence",
  mock: "Mock data",
  mock_ready: "Mock-ready",
  not_evaluated: "Not evaluated",
  not_found: "Not generated",
  not_loaded: "Not loaded",
  ok: "Mock-ready",
  paper: "Paper mode",
  partial: "Mock-ready / production gated",
  production: "Production data",
  ready: "Ready",
  review: "Needs production evidence",
  submitted: "Submitted",
  waiting: "Waiting",
};

export function formatDemoStatus(value: unknown) {
  const normalized = normalizeStatus(value);

  if (!normalized) {
    return "-";
  }

  return statusLabels[normalized] ?? titleCase(normalized);
}

export function demoStatusTone(value: unknown): FriendlyStatusTone {
  const normalized = normalizeStatus(value);

  if (
    normalized === "ok" ||
    normalized === "ready" ||
    normalized === "mock_ready" ||
    normalized === "client_ready" ||
    normalized === "complete" ||
    normalized === "completed" ||
    normalized === "submitted"
  ) {
    return "emerald";
  }

  if (normalized === "mock" || normalized === "paper" || normalized === "production") {
    return "blue";
  }

  if (normalized === "blocked" || normalized === "error" || normalized === "failed") {
    return "red";
  }

  if (
    normalized === "partial" ||
    normalized === "review" ||
    normalized === "not_found" ||
    normalized === "not_loaded" ||
    normalized === "missing" ||
    normalized === "fallback"
  ) {
    return "amber";
  }

  return "slate";
}

export function isStatusColumn(column: string) {
  const normalized = column.toLowerCase();

  return (
    normalized === "status" ||
    normalized.endsWith("_status") ||
    normalized.includes("readiness") ||
    normalized.includes("data_mode") ||
    normalized.includes("mock_or_production")
  );
}

function normalizeStatus(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  return String(value).trim().toLowerCase().replaceAll(" ", "_");
}

function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
