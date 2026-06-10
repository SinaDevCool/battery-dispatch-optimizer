"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionRiskApprovalPage() {
  return (
    <ExecutionPage
      description="Approve, hold, or unblock automated trading with guardrails, forecast confidence, human approval, freshness, and route evidence in one decision view."
      eyebrow="Automated trading"
      initialTab="risk"
      showTabs={false}
      title="Automation Gates"
    />
  );
}
