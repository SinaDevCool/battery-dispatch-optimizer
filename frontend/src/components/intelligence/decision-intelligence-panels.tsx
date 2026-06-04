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
  return (
    <SectionCard
      action={<StatusPill tone="blue">{workflowRows.length} runs</StatusPill>}
      title="Workflow audit trail"
    >
      <DataTable
        columns={[
          "workflow_run_id",
          "completed_at",
          "forecast_snapshot_id",
          "signal_id",
          "revenue_stack_id",
          "decision_id",
          "recommendation_status",
          "expected_pnl_eur",
        ]}
        rows={workflowRows}
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
  return (
    <SectionCard title="Decision history">
      <DataTable
        columns={[
          "generated_at",
          "readiness",
          "recommendation_status",
          "expected_pnl_eur",
          "hedged_revenue_eur",
          "residual_exposure_eur",
          "forecast_provider",
        ]}
        rows={decisionTrend}
      />
      {decisionTrend.length ? (
        <div className="mt-5">
          <BarComparisonChart
            data={decisionTrend}
            xKey="generated_at"
            yKey="expected_pnl_eur"
          />
        </div>
      ) : null}
    </SectionCard>
  );
}

export function ForecastPerformanceEvidencePanel({
  performanceRows,
}: {
  performanceRows: TableRow[];
}) {
  return (
    <SectionCard title="Forecast performance history">
      <DataTable
        columns={[
          "target_date",
          "forecast_provider",
          "mae_eur_per_mwh",
          "rmse_eur_per_mwh",
          "bias_eur_per_mwh",
          "predicted_pnl_eur",
          "realized_pnl_eur",
          "revenue_delta_eur",
        ]}
        rows={performanceRows}
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
  return (
    <SectionCard title="Market product eligibility matrix">
      <DataTable
        columns={[
          "product_id",
          "product_name",
          "market",
          "eligibility_status",
          "blocking_reasons",
          "review_warnings",
        ]}
        rows={productMatrix}
      />
    </SectionCard>
  );
}
