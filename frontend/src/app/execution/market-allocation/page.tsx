"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionMarketAllocationPage() {
  return (
    <ExecutionPage
      description="Rank German market routes across EPEX and regelleistung, allocate capacity, and explain excluded markets with operator-ready evidence."
      eyebrow="Trading operations"
      initialTab="allocation"
      showTabs={false}
      title="Market allocation"
    />
  );
}
