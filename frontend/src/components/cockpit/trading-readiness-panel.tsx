"use client";

import { Cable, CirclePause, LockKeyhole, UserCheck } from "lucide-react";

import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";

export function TradingReadinessPanel() {
  return (
    <SectionCard title="Trading readiness">
      <div className="grid gap-3 md:grid-cols-2">
        <ReadinessItem
          icon={<Cable className="h-4 w-4" />}
          label="Market API"
          tone="amber"
          value="Not connected"
        />
        <ReadinessItem
          icon={<CirclePause className="h-4 w-4" />}
          label="Auto execution"
          tone="amber"
          value="Disabled"
        />
        <ReadinessItem
          icon={<UserCheck className="h-4 w-4" />}
          label="Approval mode"
          tone="blue"
          value="Human required"
        />
        <ReadinessItem
          icon={<LockKeyhole className="h-4 w-4" />}
          label="Execution guardrails"
          tone="emerald"
          value="Design ready"
        />
      </div>

      <div className="mt-4 rounded-lg border border-sky-400/20 bg-sky-400/10 p-4 text-sm leading-6 text-sky-100">
        Future trading mode should require market connectivity, position limits,
        asset telemetry, schedule nomination, settlement reconciliation, and a
        human approval policy before orders are sent automatically.
      </div>
    </SectionCard>
  );
}

function ReadinessItem({
  icon,
  label,
  tone,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  tone: "amber" | "blue" | "emerald" | "red" | "slate";
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        <span className="text-slate-400">{icon}</span>
        {label}
      </div>
      <div className="mt-3">
        <StatusPill tone={tone}>{value}</StatusPill>
      </div>
    </div>
  );
}
