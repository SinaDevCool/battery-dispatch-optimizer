"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionRiskApprovalPage() {
  return (
    <ExecutionPage
      description="Manage automation guardrails, forecast confidence, hard blockers, and operator approval before supervised execution."
      eyebrow="Trading operations"
      initialTab="risk"
      showTabs={false}
      title="Risk and approval"
    />
  );
}
