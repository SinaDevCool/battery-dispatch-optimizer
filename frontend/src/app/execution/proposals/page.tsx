"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionProposalsPage() {
  return (
    <ExecutionPage
      description="Review backend-generated bid proposals, position limits, risk-adjusted order sizing, and proposal history before approval."
      eyebrow="Trading operations"
      initialTab="proposals"
      showTabs={false}
      title="Bid proposals"
    />
  );
}
