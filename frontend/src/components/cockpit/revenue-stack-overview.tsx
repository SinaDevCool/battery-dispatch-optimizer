"use client";

import { DataTable } from "@/components/data-table";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency } from "@/lib/format";
import type { HedgingSummary, RevenueStackResult } from "@/types/api";

export function RevenueStackOverview({
  hedgingSummary,
  rows,
}: {
  hedgingSummary: HedgingSummary;
  rows: RevenueStackResult[];
}) {
  const totalRevenue = rows.reduce(
    (sum, row) => sum + Number(row.revenue_eur ?? row.total_revenue_eur ?? 0),
    0,
  );
  const available = rows.filter((row) => row.status === "ok").length;

  return (
    <SectionCard
      action={<StatusPill tone="emerald">{available}/{rows.length} modelled</StatusPill>}
      title="Revenue stack"
    >
      <div className="grid gap-3 md:grid-cols-3">
        <StackMetric label="Merchant revenue" value={formatCurrency(totalRevenue)} />
        <StackMetric
          label="Hedged revenue"
          value={formatCurrency(hedgingSummary.hedged_revenue_eur)}
        />
        <StackMetric
          label="Residual exposure"
          value={formatCurrency(hedgingSummary.residual_exposure_eur)}
        />
      </div>

      <div className="mt-4">
        <DataTable
          columns={["market", "revenue_eur", "risk_adjusted_revenue_eur", "status"]}
          rows={rows.slice(0, 6)}
        />
      </div>
    </SectionCard>
  );
}

function StackMetric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}
