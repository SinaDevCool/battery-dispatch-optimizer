"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionRiskApprovalPage() {
  return (
    <ExecutionPage
      description="Decide whether automated trading can advance, which gate blocks live execution, and what action clears it."
      eyebrow="Automated trading"
      initialTab="risk"
      showTabs={false}
      title="Risk & Approval Gates"
    />
  );
}
