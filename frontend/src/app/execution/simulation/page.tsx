"use client";

import ExecutionPage from "@/app/execution/page";

export default function ExecutionSimulationPage() {
  return (
    <ExecutionPage
      description="Prove that proposed orders survive paper fills, market lifecycle checks, and validation evidence before supervised or live escalation."
      eyebrow="Automated trading"
      initialTab="simulation"
      showTabs={false}
      title="Paper trading validation"
    />
  );
}
