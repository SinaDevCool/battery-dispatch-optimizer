"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionSimulationPage() {
  return (
    <ExecutionPage
      description="Validate bids through paper trading and demo market lifecycle evidence before enabling live market connectivity."
      eyebrow="Trading operations"
      initialTab="simulation"
      showTabs={false}
      title="Simulation"
    />
  );
}
