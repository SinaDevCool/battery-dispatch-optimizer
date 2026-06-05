"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionProposalsPage() {
  return (
    <ExecutionPage
      description="Inspect automated bid proposals, position limits, risk-adjusted order sizing, and proposal history before the next automation gate."
      eyebrow="Automated trading"
      initialTab="proposals"
      showTabs={false}
      title="Bid Engine"
    />
  );
}
