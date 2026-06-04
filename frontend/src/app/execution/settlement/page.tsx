"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionSettlementPage() {
  return (
    <ExecutionPage
      description="Reconcile expected, paper, and realized economics with variance drivers and settlement evidence."
      eyebrow="Trading operations"
      initialTab="settlement"
      showTabs={false}
      title="Settlement"
    />
  );
}
