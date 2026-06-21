"use client";

import { useMemo, useState } from "react";
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
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type {
  ApiEnvelope,
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

const intelligenceTabs = [
  {
    id: "scorecard",
    label: "Scorecard",
    helper: "Evidence scorecard and open gaps for the current recommendation.",
  },
  {
    id: "audit",
    label: "Audit Chain",
    helper: "Workflow audit trail and product eligibility summary.",
  },
  {
    id: "history",
    label: "History",
    helper: "Decision trend and forecast performance evidence.",
  },
  {
    id: "matrix",
    label: "Eligibility Matrix",
    helper: "Product-level eligibility matrix and blockers.",
  },
] as const;

type IntelligenceTabId = (typeof intelligenceTabs)[number]["id"];

type PriorityGap = TableRow & {
  business_impact?: string;
  current_evidence?: string[];
  domain?: string;
  gap_id?: string;
  missing_evidence?: string[];
  next_action?: string;
  severity?: "high" | "medium" | "low" | string;
  source_page?: string;
  source_route?: string;
  status?: string;
  title?: string;
  why_it_matters?: string;
};

type PriorityGapsResponse = ApiEnvelope<{
  connector_onboarding?: {
    business_answer?: string;
    rows?: TableRow[];
    status?: string;
  };
  evidence_modes?: TableRow[];
  gaps?: PriorityGap[];
  persona_playbooks?: TableRow[];
  revenue_opportunities?: {
    business_answer?: string;
    highest_value_product?: TableRow | null;
    rows?: TableRow[];
    status?: string;
  };
  settlement_explainer?: TableRow & {
    human_variance_explanation?: string;
    next_action?: string;
    production_record_needed?: string[];
    short_answer?: string;
  };
  summary?: {
    business_answer?: string;
    highest_severity?: string;
    open_gap_count?: number;
    ready_domain_count?: number;
    top_gap_id?: string;
    top_gap_title?: string;
  };
}>;

export default function DecisionIntelligencePage() {
  const { aiEvidenceMode, selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();
  const [activeTab, setActiveTab] = useState<IntelligenceTabId>("scorecard");
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

  const priorityGaps = useQuery({
    queryFn: () =>
      apiGet<PriorityGapsResponse>(
        `/assets/${selectedAssetId}/intelligence/priority-gaps?evidence_mode=${aiEvidenceMode}`,
      ),
    queryKey: ["intelligence-priority-gaps", selectedAssetId, aiEvidenceMode],
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
  const priorityGapRows = buildPriorityGapRows(priorityGaps.data?.gaps ?? []);
  const evidenceModeRows = priorityGaps.data?.evidence_modes ?? [];
  const revenueOpportunityRows = buildRevenueOpportunityRows(
    priorityGaps.data?.revenue_opportunities?.rows ?? [],
  );
  const connectorRows = buildConnectorRows(
    priorityGaps.data?.connector_onboarding?.rows ?? [],
  );
  const playbookRows = buildPlaybookRows(priorityGaps.data?.persona_playbooks ?? []);
  const settlementExplainer = priorityGaps.data?.settlement_explainer;

  const refetchIntelligence = () =>
    Promise.all([
      latestWorkflow.refetch(),
      workflowHistory.refetch(),
      decisionHistory.refetch(),
      forecastPerformance.refetch(),
      eligibleProducts.refetch(),
      priorityGaps.refetch(),
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

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={intelligenceTabs}
      />

      {activeTab === "scorecard" ? (
        <div className="space-y-5">
          <SectionCard
            action={
              <div className="flex flex-wrap gap-2">
                <StatusPill tone={aiEvidenceMode === "mock" ? "emerald" : "blue"}>
                  {aiEvidenceMode === "mock" ? "Mock data mode" : "Live data mode"}
                </StatusPill>
                <StatusPill tone={gapSeverityTone(priorityGaps.data?.summary?.highest_severity)}>
                  {priorityGaps.data?.summary?.open_gap_count ?? 0} priority gap(s)
                </StatusPill>
              </div>
            }
            title="Priority gap diagnosis"
          >
            <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Business answer
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-200">
                  {priorityGaps.data?.summary?.business_answer ??
                    "Priority gap analysis has not loaded yet."}
                </p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <KpiCard
                    accent={gapSeverityAccent(priorityGaps.data?.summary?.highest_severity)}
                    label="Top blocker"
                    value={priorityGaps.data?.summary?.top_gap_title ?? "-"}
                    helper={priorityGaps.data?.summary?.top_gap_id ?? "Waiting for evidence"}
                  />
                  <KpiCard
                    accent={(priorityGaps.data?.summary?.open_gap_count ?? 0) ? "amber" : "emerald"}
                    label="Ready domains"
                    value={formatNumber(priorityGaps.data?.summary?.ready_domain_count, 0)}
                    helper="Revenue, settlement, market readiness, forecast trust"
                  />
                </div>
              </div>

              <DataTable
                columns={[
                  "domain",
                  "status",
                  "severity",
                  "title",
                  "missing_evidence",
                  "next_action",
                  "source_page",
                ]}
                rows={priorityGapRows}
              />
            </div>
          </SectionCard>

          <SectionCard
            action={<StatusPill tone="blue">mock to production</StatusPill>}
            title="Production evidence switch"
          >
            <DataTable
              columns={[
                "domain",
                "current_mode",
                "status",
                "production_state",
                "production_upgrade",
                "source_page",
              ]}
              rows={evidenceModeRows}
            />
          </SectionCard>

          <SectionCard
            action={
              <StatusPill tone={priorityGaps.data?.revenue_opportunities?.status === "ok" ? "emerald" : "amber"}>
                revenue stack
              </StatusPill>
            }
            title="Revenue opportunity explainer"
          >
            <div className="mb-4 grid gap-3 xl:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)]">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-sm leading-6 text-slate-200">
                {priorityGaps.data?.revenue_opportunities?.business_answer ??
                  "Revenue opportunity analysis has not loaded yet."}
              </div>
              <DataTable
                columns={[
                  "product_id",
                  "allocation_status",
                  "evidence_mode",
                  "estimated_revenue_eur",
                  "allocated_revenue_eur",
                  "business_meaning",
                  "next_action",
                ]}
                rows={revenueOpportunityRows}
              />
            </div>
          </SectionCard>

          <SectionCard
            action={<StatusPill tone={settlementExplainer?.status === "settled" ? "emerald" : "amber"}>{String(settlementExplainer?.status ?? "pending")}</StatusPill>}
            title="Settlement explainer"
          >
            <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-sm leading-6 text-slate-200">
                  {settlementExplainer?.short_answer ?? "Settlement explainer has not loaded yet."}
                </p>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {settlementExplainer?.human_variance_explanation ?? "-"}
                </p>
                <div className="mt-4 rounded-md border border-sky-400/20 bg-sky-400/10 px-3 py-2 text-sm leading-5 text-sky-100">
                  {settlementExplainer?.next_action ?? "Attach production settlement records."}
                </div>
              </div>
              <DataTable
                columns={["field", "value"]}
                rows={[
                  { field: "Expected PnL", value: settlementExplainer?.expected_pnl_eur },
                  { field: "Paper PnL", value: settlementExplainer?.paper_pnl_eur },
                  { field: "Realized PnL", value: settlementExplainer?.realized_pnl_eur },
                  { field: "Paper delta", value: settlementExplainer?.paper_delta_eur },
                  { field: "Production records", value: settlementExplainer?.production_record_needed },
                ]}
              />
            </div>
          </SectionCard>

          <SectionCard
            action={<StatusPill tone="amber">connector onboarding</StatusPill>}
            title="Market connector onboarding"
          >
            <div className="mb-4 rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-sm leading-6 text-slate-200">
              {priorityGaps.data?.connector_onboarding?.business_answer ??
                "Connector onboarding guidance has not loaded yet."}
            </div>
            <DataTable
              columns={[
                "adapter_name",
                "current_mode",
                "production_readiness_tier",
                "readiness_score",
                "first_credential",
                "business_value",
                "next_action",
              ]}
              rows={connectorRows}
            />
          </SectionCard>

          <SectionCard
            action={<StatusPill tone="emerald">persona-aware</StatusPill>}
            title="Persona agent playbooks"
          >
            <DataTable
              columns={[
                "persona_id",
                "question",
                "default_short_answer",
                "answer_strategy",
                "evidence_to_use",
              ]}
              rows={playbookRows}
            />
          </SectionCard>

          <SectionCard
            action={<StatusPill tone={evidenceDecision.tone}>{evidenceDecision.tone === "emerald" ? framing.readyLabel : "Needs evidence"}</StatusPill>}
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
        </div>
      ) : null}

      {activeTab === "audit" ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(420px,0.75fr)]">
          <WorkflowAuditTrailPanel workflowRows={workflowAuditRows} />
          <ProductEligibilitySummaryPanel
            blockedCount={blockedCount}
            eligibleCount={eligibleCount}
            reviewCount={reviewCount}
          />
        </div>
      ) : null}

      {activeTab === "history" ? (
        <div className="grid gap-5 xl:grid-cols-2">
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
      ) : null}

      {activeTab === "matrix" ? (
        <ProductEligibilityMatrixPanel productMatrix={productMatrix} />
      ) : null}
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

function buildPriorityGapRows(gaps: PriorityGap[]) {
  return gaps.map((gap) => ({
    domain: gap.domain ?? "-",
    status: gap.status ?? "-",
    severity: gap.severity ?? "-",
    title: gap.title ?? "-",
    missing_evidence: formatList(gap.missing_evidence),
    next_action: gap.next_action ?? "-",
    source_page: gap.source_page
      ? `${gap.source_page} (${gap.source_route ?? "/"})`
      : "-",
    why_it_matters: gap.why_it_matters ?? "-",
    business_impact: gap.business_impact ?? "-",
  }));
}

function buildRevenueOpportunityRows(rows: TableRow[]) {
  return rows.map((row) => ({
    product_id: row.product_id,
    allocation_status: row.allocation_status,
    evidence_mode: row.evidence_mode,
    estimated_revenue_eur: row.estimated_revenue_eur,
    allocated_revenue_eur: row.allocated_revenue_eur,
    business_meaning: row.business_meaning,
    next_action: row.next_action,
  }));
}

function buildConnectorRows(rows: TableRow[]) {
  return rows.map((row) => ({
    adapter_name: row.adapter_name,
    current_mode: row.current_mode,
    production_readiness_tier: row.production_readiness_tier,
    readiness_score: row.readiness_score,
    first_credential: row.first_credential,
    business_value: row.business_value,
    next_action: row.next_action,
  }));
}

function buildPlaybookRows(rows: TableRow[]) {
  return rows.map((row) => ({
    persona_id: row.persona_id,
    question: row.question,
    default_short_answer: row.default_short_answer,
    answer_strategy: row.answer_strategy,
    evidence_to_use: Array.isArray(row.evidence_to_use)
      ? row.evidence_to_use.join("; ")
      : row.evidence_to_use,
  }));
}

function formatList(values?: string[]) {
  if (!values?.length) {
    return "-";
  }

  return values.slice(0, 3).join("; ");
}

function gapSeverityTone(severity?: string) {
  if (severity === "high") {
    return "red" as const;
  }

  if (severity === "medium") {
    return "amber" as const;
  }

  return "emerald" as const;
}

function gapSeverityAccent(severity?: string) {
  if (severity === "high") {
    return "red" as const;
  }

  if (severity === "medium") {
    return "amber" as const;
  }

  return "emerald" as const;
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
