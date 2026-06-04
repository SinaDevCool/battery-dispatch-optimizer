import type { MultiMarketAllocationResponse } from "@/types/api";

import { DataTable } from "@/components/data-table";
import { ExecutionMetric } from "@/components/execution/execution-metric";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency, formatNumber } from "@/lib/format";

type MarketAllocationPanelProps = {
  allocation?: MultiMarketAllocationResponse;
  refetchExecution: () => Promise<unknown>;
  selectedAssetId: string;
};

export function MarketAllocationPanel({
  allocation,
  refetchExecution,
  selectedAssetId,
}: MarketAllocationPanelProps) {
  const summary = allocation?.summary ?? {};
  const primary = allocation?.primary_market;
  const secondary = allocation?.secondary_market;
  const rows = allocation?.allocation ?? [];
  const excludedRows = allocation?.excluded_markets ?? [];
  const actions = allocation?.recommended_actions ?? [];

  return (
    <div className="space-y-5">
      <SectionCard
        action={
          <button
            className="inline-flex items-center justify-center rounded-md border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-xs font-semibold text-sky-100 transition hover:bg-sky-400/20"
            onClick={() => {
              void refetchExecution();
            }}
            type="button"
          >
            Refresh allocation
          </button>
        }
        title="Execution market allocation"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-4">
          <ExecutionMetric
            label="Allocation status"
            value={allocation?.allocation_status ?? "-"}
          />
          <ExecutionMetric
            label="Eligible markets"
            value={formatNumber(summary.eligible_market_count, 0)}
          />
          <ExecutionMetric
            label="Allocated power"
            value={`${formatNumber(summary.total_allocated_power_mw, 2)} MW`}
          />
          <ExecutionMetric
            label="Expected revenue"
            value={formatCurrency(summary.total_expected_revenue_eur)}
          />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <MarketRouteCard label="Primary route" route={primary} />
          <MarketRouteCard label="Secondary route" route={secondary} />
        </div>
      </SectionCard>

      <SectionCard
        action={
          <StatusPill tone={readinessTone(summary.readiness_status)}>
            {summary.readiness_status ?? "not evaluated"}
          </StatusPill>
        }
        title="Ranked market candidates"
      >
        <DataTable
          columns={[
            "adapter_id",
            "market_name",
            "recommendation_status",
            "allocation_score",
            "risk_score",
            "allocated_power_mw",
            "allocated_energy_mwh",
            "expected_revenue_eur",
            "preview_status",
            "preview_validation_status",
            "adapter_connection_status",
            "operator_next_action",
          ]}
          rows={formatMarketAllocationRows(rows)}
        />
      </SectionCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <SectionCard
          action={<StatusPill tone="amber">{excludedRows.length}</StatusPill>}
          title="Excluded markets"
        >
          <DataTable
            columns={[
              "adapter_id",
              "market_name",
              "commercial_product_id",
              "blocking_reasons",
              "operator_next_action",
            ]}
            rows={formatExcludedMarketRows(excludedRows)}
          />
        </SectionCard>

        <SectionCard
          action={<StatusPill tone="blue">{selectedAssetId}</StatusPill>}
          title="Operator next actions"
        >
          <DataTable
            columns={["action"]}
            rows={actions.map((action) => ({ action }))}
          />
        </SectionCard>
      </div>
    </div>
  );
}

function MarketRouteCard({
  label,
  route,
}: {
  label: string;
  route?: MultiMarketAllocationResponse["primary_market"];
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
            {label}
          </div>
          <div className="mt-2 text-lg font-semibold text-white">
            {route?.market_name ?? "-"}
          </div>
        </div>
        <StatusPill tone={candidateTone(route?.recommendation_status)}>
          {route?.recommendation_status ?? "missing"}
        </StatusPill>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Score"
          value={formatNumber(route?.allocation_score, 1)}
        />
        <ExecutionMetric
          label="Power"
          value={`${formatNumber(route?.allocated_power_mw, 2)} MW`}
        />
        <ExecutionMetric
          label="Revenue"
          value={formatCurrency(route?.expected_revenue_eur)}
        />
      </div>
      <div className="mt-4 text-sm leading-6 text-slate-300">
        {route?.operator_next_action ?? "No execution route selected yet."}
      </div>
    </div>
  );
}

function formatMarketAllocationRows(
  rows: NonNullable<MultiMarketAllocationResponse["allocation"]>,
) {
  return rows.map((row) => ({
    ...row,
    allocated_energy_mwh: formatNumber(row.allocated_energy_mwh, 2),
    allocated_power_mw: formatNumber(row.allocated_power_mw, 2),
    allocation_score: formatNumber(row.allocation_score, 1),
    expected_revenue_eur: formatCurrency(row.expected_revenue_eur),
    risk_score: formatNumber(row.risk_score, 1),
  }));
}

function formatExcludedMarketRows(
  rows: NonNullable<MultiMarketAllocationResponse["excluded_markets"]>,
) {
  return rows.map((row) => ({
    ...row,
    blocking_reasons: (row.blocking_reasons ?? []).join(" | "),
  }));
}

function readinessTone(value: unknown) {
  if (value === "supervised_ready") {
    return "emerald";
  }

  if (value === "operator_review_required") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function candidateTone(value: unknown) {
  if (value === "recommended") {
    return "emerald";
  }

  if (value === "operator_review") {
    return "blue";
  }

  if (value === "excluded") {
    return "red";
  }

  if (value === "watchlist") {
    return "amber";
  }

  return "slate";
}
