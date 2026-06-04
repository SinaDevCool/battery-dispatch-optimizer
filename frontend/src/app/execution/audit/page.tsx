"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionAuditPage() {
  return (
    <ExecutionPage
      description="Inspect bid lifecycle events, backend risk checks, execution audit evidence, and telemetry proof points."
      eyebrow="Trading operations"
      initialTab="audit"
      showTabs={false}
      title="Audit trail"
    />
  );
}
