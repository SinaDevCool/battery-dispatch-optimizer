"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { ErrorState } from "@/components/error-state";
import {
  DecisionHistoryPanel,
  ForecastPerformanceEvidencePanel,
  ProductEligibilityMatrixPanel,
  ProductEligibilitySummaryPanel,
  WorkflowAuditTrailPanel,
} from "@/components/intelligence/decision-intelligence-panels";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type {
  BusinessDecision,
  BusinessDecisionHistoryResponse,
  EligibleProductResult,
  EligibleProductsResponse,
  ForecastPerformanceHistoryResponse,
  TableRow,
  WorkflowRunHistoryResponse,
  WorkflowRunResponse,
} from "@/types/api";

export default function DecisionIntelligencePage() {
  const { selectedAssetId } = useAssetContext();

  const latestWorkflow = useQuery({
    queryFn: () =>
      apiGet<WorkflowRunResponse>(
        `/assets/${selectedAssetId}/workflow-runs/latest`,
      ),
    queryKey: ["intelligence-latest-workflow", selectedAssetId],
  });

  const workflowHistory = useQuery({
    queryFn: () =>
      apiGet<WorkflowRunHistoryResponse>(
        `/assets/${selectedAssetId}/workflow-runs?limit=25`,
      ),
    queryKey: ["intelligence-workflow-history", selectedAssetId],
  });

  const decisionHistory = useQuery({
    queryFn: () =>
      apiGet<BusinessDecisionHistoryResponse>(
        `/assets/${selectedAssetId}/business-decision/history?limit=25`,
      ),
    queryKey: ["intelligence-decision-history", selectedAssetId],
  });

  const forecastPerformance = useQuery({
    queryFn: () =>
      apiGet<ForecastPerformanceHistoryResponse>(
        `/assets/${selectedAssetId}/forecast-performance?limit=25`,
      ),
    queryKey: ["intelligence-forecast-performance", selectedAssetId],
  });

  const eligibleProducts = useQuery({
    queryFn: () =>
      apiGet<EligibleProductsResponse>(
        `/assets/${selectedAssetId}/eligible-products`,
      ),
    queryKey: ["intelligence-eligible-products", selectedAssetId],
  });

  const workflowRows = useMemo(
    () => workflowHistory.data?.workflow_runs ?? [],
    [workflowHistory.data?.workflow_runs],
  );
  const decisionRows = useMemo(
    () => decisionHistory.data?.decisions ?? [],
    [decisionHistory.data?.decisions],
  );
  const performanceRows = forecastPerformance.data?.runs ?? [];
  const productRows = useMemo(
    () => eligibleProducts.data?.products ?? [],
    [eligibleProducts.data?.products],
  );
  const latestRun = latestWorkflow.data?.workflow_run;
  const latestDecision = decisionRows[0];
  const productMatrix = useMemo(() => buildProductMatrix(productRows), [productRows]);
  const decisionTrend = useMemo(() => buildDecisionTrend(decisionRows), [decisionRows]);
  const workflowAuditRows = useMemo(
    () => buildWorkflowAuditRows(workflowRows),
    [workflowRows],
  );

  const eligibleCount = productRows.filter((row) => row.eligible).length;
  const reviewCount = productRows.filter(
    (row) => row.eligibility_status === "review_required",
  ).length;
  const blockedCount = productRows.filter(
    (row) => row.eligibility_status === "not_eligible",
  ).length;
  const latestPerformance = performanceRows[0];

  const refetchIntelligence = () =>
    Promise.all([
      latestWorkflow.refetch(),
      workflowHistory.refetch(),
      decisionHistory.refetch(),
      forecastPerformance.refetch(),
      eligibleProducts.refetch(),
    ]);

  return (
    <>
      <PageHeading
        description="Trace every commercial recommendation back to forecast, optimizer, revenue stack, regulation, product eligibility, and forecast performance evidence."
        eyebrow="Decision intelligence"
        title="Audit and business evidence"
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/workflow-runs/run`}
          label="Run audited workflow"
          refetch={refetchIntelligence}
          variant="primary"
        />
      </div>

      {latestWorkflow.data?.status === "not_found" ? (
        <div className="mb-6">
          <ErrorState message="No audited workflow exists yet. Run the audited workflow to connect forecast, dispatch, revenue, and business decision evidence." />
        </div>
      ) : null}

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={latestRun?.status === "ok" ? "emerald" : "slate"}
          label="Latest workflow"
          value={latestRun?.workflow_run_id ?? "-"}
          helper={latestRun?.completed_at ? formatDateTime(latestRun.completed_at) : "No completed audit run"}
        />
        <KpiCard
          accent={latestDecision?.recommendation_status === "advisory_ready" ? "emerald" : "amber"}
          label="Decision posture"
          value={latestDecision?.readiness ?? "-"}
          helper={latestDecision?.recommendation_status ?? "No decision history"}
        />
        <KpiCard
          accent="emerald"
          label="Expected PnL"
          value={formatCurrency(latestDecision?.expected_pnl_eur)}
          helper={`${formatNumber(latestDecision?.profit_per_mw_day, 2)} EUR/MW-day`}
        />
        <KpiCard
          accent={latestPerformance ? "blue" : "amber"}
          label="Forecast trust"
          value={
            latestPerformance
              ? `${formatNumber(latestPerformance.mae_eur_per_mwh, 2)} MAE`
              : "Not tested"
          }
          helper={
            latestPerformance
              ? `${formatCurrency(latestPerformance.revenue_delta_eur)} revenue delta`
              : "Run forecast-vs-actual when actual prices exist"
          }
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(420px,0.75fr)]">
        <WorkflowAuditTrailPanel workflowRows={workflowAuditRows} />
        <ProductEligibilitySummaryPanel
          blockedCount={blockedCount}
          eligibleCount={eligibleCount}
          reviewCount={reviewCount}
        />
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <DecisionHistoryPanel decisionTrend={decisionTrend} />
        <ForecastPerformanceEvidencePanel performanceRows={performanceRows} />
      </div>

      <div className="mt-5">
        <ProductEligibilityMatrixPanel productMatrix={productMatrix} />
      </div>
    </>
  );
}

function buildWorkflowAuditRows(rows: TableRow[]) {
  return rows.map((row) => ({
    ...row,
    completed_at: formatDateTime(row.completed_at),
  }));
}

function buildDecisionTrend(rows: BusinessDecision[]) {
  return rows.map((row) => ({
    expected_pnl_eur: row.expected_pnl_eur,
    forecast_provider: row.forecast_provider,
    generated_at: formatDateTime(row.generated_at),
    hedged_revenue_eur: row.hedged_revenue_eur,
    readiness: row.readiness,
    recommendation_status: row.recommendation_status,
    residual_exposure_eur: row.residual_exposure_eur,
  }));
}

function buildProductMatrix(rows: EligibleProductResult[]) {
  return rows.map((row) => ({
    blocking_reasons: summarizeIssues(row.blocking_reasons),
    eligibility_status: row.eligibility_status,
    market: row.product?.market ?? "-",
    product_id: row.product?.product_id ?? "-",
    product_name: row.product?.product_name ?? "-",
    review_warnings: summarizeIssues(row.review_warnings),
  }));
}

function summarizeIssues(value: unknown) {
  if (!Array.isArray(value) || value.length === 0) {
    return "-";
  }

  return value
    .map((item) => {
      if (item && typeof item === "object" && "message" in item) {
        return String(item.message);
      }

      return String(item);
    })
    .join(" | ");
}
