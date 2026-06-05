"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionSettlementPage() {
  return (
    <ExecutionPage
      description="Reconcile expected, paper, and realized economics so the automation engine can learn from variance and settlement evidence."
      eyebrow="Automated trading"
      initialTab="settlement"
      showTabs={false}
      title="Settlement"
    />
  );
}
