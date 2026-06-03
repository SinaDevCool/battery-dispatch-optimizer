"use client";

import { ArrowDownToLine, ArrowUpFromLine, CircleDot, ShieldAlert } from "lucide-react";

import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type { SignalMetadata, SignalSummary } from "@/types/api";

export function DecisionSummary({
  metadata,
  summary,
}: {
  metadata: SignalMetadata;
  summary: SignalSummary;
}) {
  const opportunity = String(summary.opportunity_level ?? "unknown");
  const signal = String(summary.signal ?? "-");
  const confidenceTone =
    opportunity === "high" ? "emerald" : opportunity === "medium" ? "blue" : "amber";

  return (
    <SectionCard
      action={<StatusPill tone={confidenceTone}>Opportunity {opportunity}</StatusPill>}
      title="Decision summary"
    >
      <div className="grid gap-3 md:grid-cols-2">
        <KpiCard
          accent={signal === "ACTION" ? "emerald" : "slate"}
          label="Recommendation"
          value={signal}
          helper={buildRecommendation(summary)}
        />
        <KpiCard
          accent="emerald"
          label="Expected PnL"
          value={formatCurrency(summary.total_pnl_eur)}
          helper={`${formatNumber(summary.profit_per_mw_day, 2)} EUR/MW-day`}
        />
        <KpiCard
          accent="blue"
          label="Forecast source"
          value={String(metadata.source ?? "-")}
          helper={String(metadata.forecast_model ?? "-")}
        />
        <KpiCard
          accent="amber"
          label="Target delivery"
          value={String(metadata.target_date ?? "-")}
          helper={`Generated ${formatDateTime(metadata.generated_at)}`}
        />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <DecisionChip
          icon={<ArrowDownToLine className="h-4 w-4" />}
          label="Charge window"
          value={summary.first_charge_timestamp ?? "-"}
        />
        <DecisionChip
          icon={<ArrowUpFromLine className="h-4 w-4" />}
          label="Discharge window"
          value={summary.first_discharge_timestamp ?? "-"}
        />
        <DecisionChip
          icon={<CircleDot className="h-4 w-4" />}
          label="Throughput"
          value={`${formatNumber(summary.throughput_mwh, 2)} MWh`}
        />
        <DecisionChip
          icon={<ShieldAlert className="h-4 w-4" />}
          label="Cycle exposure"
          value={`${formatNumber(summary.equivalent_full_cycles, 2)} EFC`}
        />
      </div>
    </SectionCard>
  );
}

function buildRecommendation(summary: SignalSummary) {
  if (summary.signal !== "ACTION") {
    return "No executable arbitrage action selected.";
  }

  return `${summary.charge_hours ?? "-"}h charge, ${summary.discharge_hours ?? "-"}h discharge`;
}

function DecisionChip({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 px-3 py-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        <span className="text-sky-300">{icon}</span>
        {label}
      </div>
      <div className="mt-2 truncate text-sm font-semibold text-slate-100">
        {value}
      </div>
    </div>
  );
}
