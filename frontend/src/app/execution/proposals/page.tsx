"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionProposalsPage() {
  return (
    <ExecutionPage
      description="Review whether the selected route and dispatch schedule have produced a complete, risk-aware order package that can move to paper validation, approval, or supervised submission."
      eyebrow="Automated trading"
      initialTab="proposals"
      showTabs={false}
      title="Bid proposals"
    />
  );
}
