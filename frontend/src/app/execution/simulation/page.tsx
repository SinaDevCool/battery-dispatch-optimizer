"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionSimulationPage() {
  return (
    <ExecutionPage
      description="Validate automated bids through paper trading and simulated market lifecycle evidence before enabling higher automation modes."
      eyebrow="Automated trading"
      initialTab="simulation"
      showTabs={false}
      title="Paper Trading"
    />
  );
}
