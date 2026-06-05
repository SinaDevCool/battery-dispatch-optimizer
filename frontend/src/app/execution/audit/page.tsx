"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionAuditPage() {
  return (
    <ExecutionPage
      description="Inspect automated lifecycle events, backend risk checks, audit evidence, and telemetry proof points."
      eyebrow="Automated trading"
      initialTab="audit"
      showTabs={false}
      title="Audit Evidence"
    />
  );
}
