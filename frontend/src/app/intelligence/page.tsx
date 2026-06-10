"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
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
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
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

type DecisionEvidencePersonaFraming = {
  briefEyebrow: string;
  briefTitle: string;
  description: string;
  emptyMessage: string;
  eyebrow: string;
  gapTitle: string;
  readyLabel: string;
  scorecardTitle: string;
  title: string;
  workflowActionLabel?: string;
};

export default function DecisionIntelligencePage() {
  const { selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();
  const framing = getDecisionEvidencePersonaFraming(personaId);

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
  const evidenceDecision = buildEvidenceDecision({
    blockedCount,
    latestDecision,
    latestPerformance,
    latestRun,
    reviewCount,
  });
  const evidenceScorecard = buildEvidenceScorecard({
    blockedCount,
    eligibleCount,
    latestDecision,
    latestPerformance,
    latestRun,
    productCount: productRows.length,
    reviewCount,
  });
  const evidenceGapRows = buildEvidenceGapRows({
    blockedCount,
    latestDecision,
    latestPerformance,
    latestRun,
    productRows,
    reviewCount,
  });

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
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
      />

      {framing.workflowActionLabel ? (
        <div className="mb-6 flex flex-wrap gap-3">
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/workflow-runs/run`}
            label={framing.workflowActionLabel}
            refetch={refetchIntelligence}
            variant="primary"
          />
        </div>
      ) : null}

      {latestWorkflow.data?.status === "not_found" ? (
        <div className="mb-6">
          <ErrorState message={framing.emptyMessage} />
        </div>
      ) : null}

      <DecisionBrief
        blockers={evidenceDecision.blockers}
        className="mb-6"
        decision={evidenceDecision.decision}
        evidence={evidenceDecision.evidence}
        eyebrow={framing.briefEyebrow}
        nextAction={evidenceDecision.nextAction}
        title={framing.briefTitle}
        tone={evidenceDecision.tone}
      />

      <SectionCard
        action={<StatusPill tone={evidenceDecision.tone}>{evidenceDecision.tone === "emerald" ? framing.readyLabel : "Needs evidence"}</StatusPill>}
        className="mb-6"
        title={framing.scorecardTitle}
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            accent={latestRun?.status === "ok" ? "emerald" : "amber"}
            label="Evidence chain"
            value={evidenceScorecard.evidenceChain}
            helper={latestRun?.completed_at ? `Audited ${formatDateTime(latestRun.completed_at)}` : "No completed audit run"}
          />
          <KpiCard
            accent={latestDecision?.recommendation_status === "advisory_ready" ? "emerald" : "amber"}
            label="Commercial posture"
            value={latestDecision?.readiness ?? "-"}
            helper={latestDecision?.recommendation_status ?? "No decision history"}
          />
          <KpiCard
            accent="emerald"
            label="Defensible value"
            value={formatCurrency(latestDecision?.expected_pnl_eur)}
            helper={`${formatNumber(latestDecision?.profit_per_mw_day, 2)} EUR/MW-day`}
          />
          <KpiCard
            accent={latestPerformance ? "blue" : "amber"}
            label="Forecast proof"
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
      </SectionCard>

      <SectionCard
        action={<StatusPill tone={evidenceGapRows.length ? "amber" : "emerald"}>{evidenceGapRows.length} gap(s)</StatusPill>}
        className="mb-6"
        title={framing.gapTitle}
      >
        <DataTable
          columns={[
            "product_id",
            "product_name",
            "market",
            "eligibility_status",
            "automation_gate",
            "blocking_reasons",
          ]}
          rows={evidenceGapRows}
        />
      </SectionCard>

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
        <ForecastPerformanceEvidencePanel
          emptyAction={
            <ActionButton
              endpoint={`/backtesting/forecast-actual/run?asset_id=${selectedAssetId}`}
              label="Run forecast backtest"
              refetch={refetchIntelligence}
              variant="secondary"
            />
          }
          performanceRows={performanceRows}
        />
      </div>

      <div className="mt-5">
        <ProductEligibilityMatrixPanel productMatrix={productMatrix} />
      </div>
    </>
  );
}

function getDecisionEvidencePersonaFraming(
  personaId: PersonaId,
): DecisionEvidencePersonaFraming {
  const defaults: DecisionEvidencePersonaFraming = {
    briefEyebrow: "Audit evidence decision",
    briefTitle: "Can this recommendation be trusted?",
    description:
      "Prove whether a trading recommendation is client-defensible by linking forecast, dispatch, revenue, product eligibility, and audit evidence.",
    emptyMessage:
      "No audited workflow exists yet. Run the audited workflow to connect forecast, dispatch, revenue, and business decision evidence.",
    eyebrow: "Decision intelligence",
    gapTitle: "Evidence gaps to close",
    readyLabel: "Client-ready",
    scorecardTitle: "Client defensibility scorecard",
    title: "Decision evidence",
    workflowActionLabel: "Run audited workflow",
  };

  const frames: Partial<Record<PersonaId, DecisionEvidencePersonaFraming>> = {
    client_success: {
      briefEyebrow: "Client explanation decision",
      briefTitle: "Can client success explain this recommendation?",
      description:
        "Turn optimizer, forecast, revenue, eligibility, and audit records into a client-ready explanation with open gaps and next actions made explicit.",
      emptyMessage:
        "No client evidence chain exists yet. Ask the internal team to refresh the audited workflow before using this in a client conversation.",
      eyebrow: "Client delivery",
      gapTitle: "Client explanation gaps",
      readyLabel: "Explainable",
      scorecardTitle: "Client explanation scorecard",
      title: "Decision explanation",
      workflowActionLabel: "Refresh client evidence",
    },
    executive: {
      briefEyebrow: "Executive trust decision",
      briefTitle: "Is this recommendation board-defensible?",
      description:
        "Summarize whether the commercial recommendation is supported by enough forecast, dispatch, revenue, eligibility, and audit evidence for management review.",
      emptyMessage:
        "No audited decision chain is available yet. The recommendation should not be used for executive review until the evidence chain exists.",
      eyebrow: "Executive view",
      gapTitle: "Board-readiness gaps",
      readyLabel: "Board-ready",
      scorecardTitle: "Executive evidence scorecard",
      title: "Executive decision evidence",
    },
    risk_compliance: {
      briefEyebrow: "Governance evidence decision",
      briefTitle: "Can risk approve the decision trail?",
      description:
        "Validate that the recommendation has a governed evidence chain across forecast, dispatch, revenue, product eligibility, workflow audit, and decision history.",
      emptyMessage:
        "No governed workflow exists yet. Run the audited workflow before approving or escalating the recommendation.",
      eyebrow: "Risk & compliance",
      gapTitle: "Governance gaps to close",
      readyLabel: "Governed",
      scorecardTitle: "Governance evidence scorecard",
      title: "Decision governance evidence",
      workflowActionLabel: "Run governed workflow",
    },
    forecast_quant: {
      briefEyebrow: "Model evidence decision",
      briefTitle: "Does the model evidence support the recommendation?",
      description:
        "Trace the recommendation back to forecast quality, signal reliability, optimizer evidence, revenue impact, and product eligibility so model issues are visible before execution.",
      emptyMessage:
        "No model-linked workflow exists yet. Run the audited workflow and forecast backtest to connect model evidence to the commercial decision.",
      eyebrow: "Model quality OS",
      gapTitle: "Model evidence gaps",
      readyLabel: "Model-backed",
      scorecardTitle: "Model evidence scorecard",
      title: "Model-backed decision evidence",
      workflowActionLabel: "Run model evidence workflow",
    },
  };

  return frames[personaId] ?? defaults;
}

function buildWorkflowAuditRows(rows: TableRow[]) {
  return rows.map((row) => ({
    ...row,
    completed_at: formatDateTime(row.completed_at),
  }));
}

function buildDecisionTrend(rows: BusinessDecision[]) {
  const grouped = new Map<string, TableRow>();

  rows.forEach((row) => {
    const key = [
      row.readiness ?? "-",
      row.recommendation_status ?? "-",
      row.expected_pnl_eur ?? "-",
      row.residual_exposure_eur ?? "-",
      row.forecast_provider ?? "-",
      row.forecast_model ?? "-",
    ].join("|");
    const existing = grouped.get(key);

    if (existing) {
      existing.repeated_runs = Number(existing.repeated_runs ?? 1) + 1;
      existing.first_at = formatDateTime(row.generated_at);
      return;
    }

    grouped.set(key, {
      expected_pnl_eur: row.expected_pnl_eur,
      first_at: formatDateTime(row.generated_at),
      forecast_provider: row.forecast_provider,
      hedged_revenue_eur: row.hedged_revenue_eur,
      latest_at: formatDateTime(row.generated_at),
      readiness: row.readiness,
      recommendation_status: row.recommendation_status,
      repeated_runs: 1,
      residual_exposure_eur: row.residual_exposure_eur,
    });
  });

  return Array.from(grouped.values());
}

function buildProductMatrix(rows: EligibleProductResult[]) {
  return rows.map((row) => ({
    automation_gate:
      row.eligibility_status === "eligible"
        ? "can feed revenue allocation"
        : row.eligibility_status === "review_required"
          ? "needs commercial review"
          : summarizeIssues(row.blocking_reasons),
    blocking_reasons: summarizeIssues(row.blocking_reasons),
    eligibility_status: row.eligibility_status,
    market: row.product?.market ?? "-",
    product_id: row.product?.product_id ?? "-",
    product_name: row.product?.product_name ?? "-",
    review_warnings: summarizeIssues(row.review_warnings),
  }));
}

function buildEvidenceScorecard({
  blockedCount,
  eligibleCount,
  latestDecision,
  latestPerformance,
  latestRun,
  productCount,
  reviewCount,
}: {
  blockedCount: number;
  eligibleCount: number;
  latestDecision?: BusinessDecision;
  latestPerformance?: TableRow;
  latestRun?: TableRow | null;
  productCount: number;
  reviewCount: number;
}) {
  const linkedEvidenceCount = latestRun ? countLinkedEvidence(latestRun) : 0;

  return {
    evidenceChain: latestRun
      ? `${linkedEvidenceCount}/4 linked`
      : "not linked",
    posture: latestDecision?.recommendation_status ?? "not generated",
    productCoverage: `${eligibleCount}/${productCount} eligible`,
    trustState:
      blockedCount || reviewCount || !latestPerformance
        ? "needs evidence"
        : "client-ready",
  };
}

function buildEvidenceGapRows({
  blockedCount,
  latestDecision,
  latestPerformance,
  latestRun,
  productRows,
  reviewCount,
}: {
  blockedCount: number;
  latestDecision?: BusinessDecision;
  latestPerformance?: TableRow;
  latestRun?: TableRow | null;
  productRows: EligibleProductResult[];
  reviewCount: number;
}) {
  const rows: TableRow[] = [];

  if (!latestRun) {
    rows.push({
      automation_gate: "Run audited workflow",
      blocking_reasons: "No workflow links forecast, dispatch, revenue, and decision evidence.",
      eligibility_status: "missing",
      market: "audit",
      product_id: "workflow_chain",
      product_name: "Evidence chain",
    });
  }

  if (!latestPerformance) {
    rows.push({
      automation_gate: "Add actual price evidence",
      blocking_reasons: "Forecast-vs-actual performance has not been tested.",
      eligibility_status: "missing",
      market: "forecast",
      product_id: "forecast_performance",
      product_name: "Forecast proof",
    });
  }

  if (!latestDecision) {
    rows.push({
      automation_gate: "Generate business decision",
      blocking_reasons: "No commercial recommendation is available for audit.",
      eligibility_status: "missing",
      market: "commercial",
      product_id: "business_decision",
      product_name: "Decision evidence",
    });
  }

  if (blockedCount || reviewCount) {
    productRows
      .filter((row) => row.eligibility_status !== "eligible")
      .slice(0, 6)
      .forEach((row) => {
        rows.push({
          automation_gate:
            row.eligibility_status === "review_required"
              ? "Commercial review"
              : "Product blocked",
          blocking_reasons: summarizeIssues(
            row.blocking_reasons?.length
              ? row.blocking_reasons
              : row.review_warnings,
          ),
          eligibility_status: row.eligibility_status,
          market: row.product?.market ?? "-",
          product_id: row.product?.product_id ?? "-",
          product_name: row.product?.product_name ?? "-",
        });
      });
  }

  return rows;
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

function countLinkedEvidence(row: TableRow) {
  return [
    row.forecast_snapshot_id,
    row.signal_id,
    row.revenue_stack_id,
    row.decision_id,
  ].filter((value) => value !== null && value !== undefined && value !== "-").length;
}

function buildEvidenceDecision({
  blockedCount,
  latestDecision,
  latestPerformance,
  latestRun,
  reviewCount,
}: {
  blockedCount: number;
  latestDecision?: BusinessDecision;
  latestPerformance?: TableRow;
  latestRun?: TableRow | null;
  reviewCount: number;
}) {
  const blockers = [
    !latestRun ? "No audited workflow has linked the evidence chain yet." : null,
    blockedCount ? `${blockedCount} product(s) are blocked from commercial use.` : null,
    reviewCount ? `${reviewCount} product(s) still need review evidence.` : null,
    !latestPerformance ? "Forecast-vs-actual performance has not been tested yet." : null,
  ].filter(Boolean) as string[];

  return {
    blockers,
    decision: latestDecision?.recommendation_title
      ? latestDecision.recommendation_title
      : blockers.length
        ? "Recommendation evidence is not enterprise-ready yet."
        : "Recommendation evidence is ready for commercial and audit review.",
    evidence: [
      `Workflow ${latestRun?.workflow_run_id ?? "not linked"}`,
      `Decision posture ${latestDecision?.recommendation_status ?? "not generated"}`,
      `Expected PnL ${formatCurrency(latestDecision?.expected_pnl_eur)}`,
      latestPerformance
        ? `Forecast MAE ${formatNumber(latestPerformance.mae_eur_per_mwh, 2)} EUR/MWh`
        : "No forecast performance evidence",
    ],
    nextAction: blockers.length
      ? blockers[0]
      : "Use this evidence chain in client reporting and automated trading audit trails.",
    tone: blockers.length ? "amber" as const : "emerald" as const,
  };
}
