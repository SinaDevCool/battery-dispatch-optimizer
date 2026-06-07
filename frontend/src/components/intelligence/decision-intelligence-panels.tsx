import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type { TableRow } from "@/types/api";

export function WorkflowAuditTrailPanel({
  workflowRows,
}: {
  workflowRows: TableRow[];
}) {
  const latestRows = workflowRows.slice(0, 10);

  return (
    <SectionCard
      action={<StatusPill tone="blue">{workflowRows.length} runs</StatusPill>}
      title="Workflow audit trail"
    >
      {workflowRows[0] ? (
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <KpiCard
            accent={workflowRows[0].status === "ok" ? "emerald" : "amber"}
            helper="Most recent audited run"
            label="Latest status"
            value={String(workflowRows[0].status ?? "-")}
          />
          <KpiCard
            accent="blue"
            helper="Forecast, signal, revenue, and decision linkage"
            label="Evidence links"
            value={countEvidenceLinks(workflowRows[0])}
          />
          <KpiCard
            accent="emerald"
            helper="Commercial recommendation evidence"
            label="Decision"
            value={String(workflowRows[0].recommendation_status ?? "-")}
          />
        </div>
      ) : null}
      <DataTable
        columns={[
          "workflow_run_id",
          "completed_at",
          "signal_id",
          "revenue_stack_id",
          "decision_id",
          "recommendation_status",
          "expected_pnl_eur",
        ]}
        rows={latestRows}
      />
    </SectionCard>
  );
}

export function ProductEligibilitySummaryPanel({
  blockedCount,
  eligibleCount,
  reviewCount,
}: {
  blockedCount: number;
  eligibleCount: number;
  reviewCount: number;
}) {
  return (
    <SectionCard
      action={<StatusPill tone="emerald">{eligibleCount} eligible</StatusPill>}
      title="Product eligibility summary"
    >
      <div className="grid gap-3">
        <KpiCard
          accent="emerald"
          helper="Can be modelled commercially"
          label="Eligible"
          value={eligibleCount}
        />
        <KpiCard
          accent="amber"
          helper="Commercial or regulatory evidence needed"
          label="Review required"
          value={reviewCount}
        />
        <KpiCard
          accent="red"
          helper="Minimum capability or prequalification gap"
          label="Blocked"
          value={blockedCount}
        />
      </div>
    </SectionCard>
  );
}

export function DecisionHistoryPanel({
  decisionTrend,
}: {
  decisionTrend: TableRow[];
}) {
  const latestRows = decisionTrend.slice(0, 8);

  return (
    <SectionCard
      action={<StatusPill tone="blue">{decisionTrend.length} decision state(s)</StatusPill>}
      title="Decision history"
    >
      <DataTable
        columns={[
          "latest_at",
          "repeated_runs",
          "readiness",
          "recommendation_status",
          "expected_pnl_eur",
          "residual_exposure_eur",
        ]}
        rows={latestRows}
      />
      {decisionTrend.length ? (
        <div className="mt-5">
          <BarComparisonChart
            data={decisionTrend}
            xKey="latest_at"
            yKey="expected_pnl_eur"
          />
        </div>
      ) : null}
    </SectionCard>
  );
}

export function ForecastPerformanceEvidencePanel({
  emptyAction,
  performanceRows,
}: {
  emptyAction?: React.ReactNode;
  performanceRows: TableRow[];
}) {
  const latestRows = performanceRows.slice(0, 8);

  return (
    <SectionCard
      action={
        <StatusPill tone={performanceRows.length ? "emerald" : "amber"}>
          {performanceRows.length ? `${performanceRows.length} test(s)` : "Not tested"}
        </StatusPill>
      }
      title="Forecast performance history"
    >
      {!performanceRows.length ? (
        <div className="mb-4 rounded-lg border border-amber-400/25 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100">
          Forecast performance is empty because no forecast-vs-actual backtest
          has been saved for this asset yet. Upload or provide actual prices,
          then run the backtest to create MAE, bias, and revenue-delta evidence.
          {emptyAction ? <div className="mt-3">{emptyAction}</div> : null}
        </div>
      ) : null}
      <DataTable
        columns={[
          "target_date",
          "forecast_provider",
          "mae_eur_per_mwh",
          "bias_eur_per_mwh",
          "revenue_delta_eur",
        ]}
        rows={latestRows}
      />
      {performanceRows.length ? (
        <div className="mt-5">
          <BarComparisonChart
            data={performanceRows}
            xKey="target_date"
            yKey="revenue_delta_eur"
          />
        </div>
      ) : null}
    </SectionCard>
  );
}

export function ProductEligibilityMatrixPanel({
  productMatrix,
}: {
  productMatrix: TableRow[];
}) {
  const productRows = productMatrix.slice(0, 10);

  return (
    <SectionCard title="Market product eligibility matrix">
      <DataTable
        columns={[
          "product_id",
          "product_name",
          "market",
          "eligibility_status",
          "automation_gate",
        ]}
        rows={productRows}
      />
    </SectionCard>
  );
}

function countEvidenceLinks(row: TableRow) {
  return [
    row.forecast_snapshot_id,
    row.signal_id,
    row.revenue_stack_id,
    row.decision_id,
  ].filter((value) => value !== null && value !== undefined && value !== "-").length;
}
