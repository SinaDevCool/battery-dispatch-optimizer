"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionRiskApprovalPage() {
  return (
    <ExecutionPage
      description="Evaluate automation guardrails, forecast confidence, hard blockers, and the human gate before supervised or live automated trading."
      eyebrow="Automated trading"
      initialTab="risk"
      showTabs={false}
      title="Risk Gates"
    />
  );
}
