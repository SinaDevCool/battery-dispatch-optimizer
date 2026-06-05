"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DispatchChart } from "@/components/charts/dispatch-chart";
import { CommandCenterHeader } from "@/components/cockpit/command-center-header";
import {
  EngineCard,
  EnterpriseMaturityPanel,
  EvidenceList,
  StatusRow,
} from "@/components/cockpit/control-room-panels";
import {
  DecisionBrief,
  type DecisionBriefTone,
} from "@/components/decision-brief";
import { DecisionSummary } from "@/components/cockpit/decision-summary";
import { RevenueStackOverview } from "@/components/cockpit/revenue-stack-overview";
import { RiskCompliancePanel } from "@/components/cockpit/risk-compliance-panel";
import { StrategyRecommendation } from "@/components/cockpit/strategy-recommendation";
import { TradingReadinessPanel } from "@/components/cockpit/trading-readiness-panel";
import { DataCompletenessPanel } from "@/components/data-completeness-panel";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  AncillaryEligibilityResponse,
  AssetMarketAdapterStatusResponse,
  AssetCockpitResponse,
  AssetTelemetryResponse,
  AutomationControlStatusResponse,
  AutomationGuardrailsResponse,
  BusinessDecision,
  BusinessDecisionResponse,
  DataCompletenessResponse,
  DatabaseStatusResponse,
  EegComplianceResponse,
  ExecutionApprovalResponse,
  ExecutionProposalResponse,
  ExecutionReadinessResponse,
  HealthResponse,
  HedgingRevenueResponse,
  LatestSignalResponse,
  RevenueStackResult,
  RevenueStackResponse,
  SettlementResponse,
  SignalSummary,
  StorageClassificationResponse,
  StrategyIntentResponse,
  WorkflowRunResponse,
} from "@/types/api";

const controlRoomTabs = [
  {
    id: "trading",
    label: "Trading Status",
    helper: "Latest signal, engine state, and current trade recommendation.",
  },
  {
    id: "readiness",
    label: "Portfolio Readiness",
    helper: "Data completeness, maturity, regulation, and automation blockers.",
  },
  {
    id: "commercial",
    label: "Commercial Decision",
    helper: "Revenue stack, hedging, allocation logic, and business value.",
  },
  {
    id: "execution",
    label: "Execution Readiness",
    helper: "Approval, telemetry, guardrails, settlement, and audit linkage.",
  },
  {
    id: "actions",
    label: "Next Actions",
    helper: "The shortest list of operator actions that move the asset forward.",
  },
] as const;

type ControlRoomTabId = (typeof controlRoomTabs)[number]["id"];

export default function OverviewPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { persona } = usePersona();
  const [activeTabByPersona, setActiveTabByPersona] = useState<
    Partial<Record<string, ControlRoomTabId>>
  >({});
  const activeTab =
    activeTabByPersona[persona.id] ?? persona.defaultControlRoomTab;
  const setActiveTab = (tab: ControlRoomTabId) =>
    setActiveTabByPersona((current) => ({
      ...current,
      [persona.id]: tab,
    }));

  const health = useQuery({
    queryFn: () => apiGet<HealthResponse>("/health"),
    queryKey: ["health"],
  });

  const databaseStatus = useQuery({
    queryFn: () => apiGet<DatabaseStatusResponse>("/database/status"),
    queryKey: ["database-status"],
  });

  const cockpit = useQuery({
    queryFn: () =>
      apiGet<AssetCockpitResponse>(`/assets/${selectedAssetId}/cockpit`),
    queryKey: ["asset-cockpit", selectedAssetId],
  });

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["asset-signal-latest", selectedAssetId],
  });

  const revenue = useQuery({
    queryFn: () =>
      apiGet<RevenueStackResponse>(
        `/assets/${selectedAssetId}/revenue-stack/latest`,
      ),
    queryKey: ["revenue-stack-latest", selectedAssetId],
  });

  const hedging = useQuery({
    queryFn: () =>
      apiGet<HedgingRevenueResponse>(
        `/assets/${selectedAssetId}/hedging/revenue`,
      ),
    queryKey: ["overview-hedging", selectedAssetId],
  });

  const eeg = useQuery({
    queryFn: () =>
      apiGet<EegComplianceResponse>(
        `/assets/${selectedAssetId}/eeg-compliance/latest`,
      ),
    queryKey: ["overview-eeg-compliance", selectedAssetId],
  });

  const classification = useQuery({
    queryFn: () =>
      apiGet<StorageClassificationResponse>(
        `/assets/${selectedAssetId}/storage-classification`,
      ),
    queryKey: ["overview-storage-classification", selectedAssetId],
  });

  const ancillary = useQuery({
    queryFn: () =>
      apiGet<AncillaryEligibilityResponse>(
        `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
      ),
    queryKey: ["overview-ancillary", selectedAssetId],
  });

  const businessDecision = useQuery({
    queryFn: () =>
      apiGet<BusinessDecisionResponse>(
        `/assets/${selectedAssetId}/business-decision/latest`,
      ),
    queryKey: ["overview-business-decision", selectedAssetId],
  });

  const workflowRun = useQuery({
    queryFn: () =>
      apiGet<WorkflowRunResponse>(
        `/assets/${selectedAssetId}/workflow-runs/latest`,
      ),
    queryKey: ["overview-workflow-run", selectedAssetId],
  });

  const completeness = useQuery({
    queryFn: () =>
      apiGet<DataCompletenessResponse>(
        `/assets/${selectedAssetId}/data-completeness`,
      ),
    queryKey: ["overview-data-completeness", selectedAssetId],
  });

  const executionProposal = useQuery({
    queryFn: () =>
      apiGet<ExecutionProposalResponse>(
        `/assets/${selectedAssetId}/execution/proposal/latest`,
      ),
    queryKey: ["overview-execution-proposal", selectedAssetId],
  });

  const approval = useQuery({
    queryFn: () =>
      apiGet<ExecutionApprovalResponse>(
        `/assets/${selectedAssetId}/execution/approval/latest`,
      ),
    queryKey: ["overview-execution-approval", selectedAssetId],
  });

  const guardrails = useQuery({
    queryFn: () =>
      apiGet<AutomationGuardrailsResponse>(
        `/assets/${selectedAssetId}/execution/automation-guardrails`,
      ),
    queryKey: ["overview-automation-guardrails", selectedAssetId],
  });

  const automationControl = useQuery({
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["overview-automation-control", selectedAssetId],
  });

  const strategyIntent = useQuery({
    queryFn: () =>
      apiGet<StrategyIntentResponse>(
        `/assets/${selectedAssetId}/execution/strategy-intent`,
      ),
    queryKey: ["overview-strategy-intent", selectedAssetId],
  });

  const telemetry = useQuery({
    queryFn: () =>
      apiGet<AssetTelemetryResponse>(
        `/assets/${selectedAssetId}/telemetry/latest`,
      ),
    queryKey: ["overview-telemetry", selectedAssetId],
  });

  const settlement = useQuery({
    queryFn: () =>
      apiGet<SettlementResponse>(`/assets/${selectedAssetId}/settlement/latest`),
    queryKey: ["overview-settlement", selectedAssetId],
  });

  const readiness = useQuery({
    queryFn: () =>
      apiGet<ExecutionReadinessResponse>(
        `/assets/${selectedAssetId}/execution/readiness`,
      ),
    queryKey: ["overview-execution-readiness", selectedAssetId],
  });

  const marketAdapterStatus = useQuery({
    queryFn: () =>
      apiGet<AssetMarketAdapterStatusResponse>(
        `/assets/${selectedAssetId}/execution/market-adapter/status`,
      ),
    queryKey: ["overview-market-adapter-status", selectedAssetId],
  });

  const cockpitData = cockpit.data?.cockpit;
  const signalPayload = cockpitData?.latest_signal ?? signal.data;
  const revenuePayload = cockpitData?.revenue_stack ?? revenue.data;
  const businessDecisionPayload =
    cockpitData?.business_decision ?? businessDecision.data;
  const workflowRunPayload = cockpitData?.workflow_run
    ? { status: "ok", workflow_run: cockpitData.workflow_run }
    : workflowRun.data;
  const completenessPayload = cockpitData?.data_completeness ?? completeness.data;
  const enterpriseMaturity = cockpitData?.enterprise_maturity;
  const metadata = cockpitData?.signal_metadata ?? signalPayload?.data?.metadata ?? {};
  const summary = cockpitData?.signal_summary ?? signalPayload?.data?.summary ?? {};
  const dispatch = cockpitData?.dispatch ?? signalPayload?.data?.dispatch ?? [];
  const revenueRows = cockpitData?.revenue_products?.length
    ? cockpitData.revenue_products
    : revenuePayload?.results?.length
      ? revenuePayload.results
      : revenuePayload?.products ?? [];
  const hedgeSummary = hedging.data?.summary ?? {};
  const activeDispatchRows = dispatch.filter((row) => row.action !== "idle");
  const totalRevenue =
    cockpitData?.business_kpis?.modelled_revenue_eur ??
    revenueRows.reduce(
      (sum, row) =>
        sum +
        Number(
          row.estimated_revenue_eur ??
            row.revenue_eur ??
            row.total_revenue_eur ??
            0,
        ),
      0,
    );
  const isBackendDown = Boolean(health.error);
  const personaDecision = buildPersonaDecisionBrief({
    activeDispatchCount: activeDispatchRows.length,
    automationControl: automationControl.data,
    businessDecision: businessDecisionPayload?.decision,
    completeness: completenessPayload,
    enterpriseMaturity,
    guardrails: guardrails.data,
    marketAdapterStatus: marketAdapterStatus.data,
    personaId: persona.id,
    readiness: readiness.data,
    revenueRows,
    settlement: settlement.data,
    signalSummary: summary,
    strategyIntent: strategyIntent.data,
    totalRevenue,
  });

  const refetchCockpit = () =>
    Promise.all([
      health.refetch(),
      databaseStatus.refetch(),
      cockpit.refetch(),
      signal.refetch(),
      revenue.refetch(),
      hedging.refetch(),
      eeg.refetch(),
      classification.refetch(),
      ancillary.refetch(),
      businessDecision.refetch(),
      workflowRun.refetch(),
      completeness.refetch(),
      executionProposal.refetch(),
      approval.refetch(),
      automationControl.refetch(),
      strategyIntent.refetch(),
      guardrails.refetch(),
      telemetry.refetch(),
      settlement.refetch(),
      readiness.refetch(),
      marketAdapterStatus.refetch(),
    ]);

  return (
    <>
      <CommandCenterHeader
        asset={selectedAsset}
        assetId={selectedAssetId}
        healthStatus={health.data?.status}
        metadata={metadata}
        onRun={refetchCockpit}
        summary={summary}
      />

      {isBackendDown ? (
        <div className="mb-6">
          <ErrorState message="The FastAPI backend is not reachable. Start it with: python -m uvicorn src.api.main:app --reload --port 8000" />
        </div>
      ) : null}

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={summary.signal === "ACTION" ? "emerald" : "slate"}
          label="Trade signal"
          value={String(summary.signal ?? "-")}
          helper={String(summary.opportunity_level ?? "No opportunity level")}
        />
        <KpiCard
          accent="emerald"
          label="Expected PnL"
          value={formatCurrency(summary.total_pnl_eur)}
          helper={`${formatNumber(summary.profit_per_mw_day, 2)} EUR/MW-day`}
        />
        <KpiCard
          accent="blue"
          label="Revenue stack"
          value={formatCurrency(totalRevenue)}
          helper={`${revenueRows.length} market product(s) assessed`}
        />
        <KpiCard
          accent={readiness.data?.readiness_status === "blocked" ? "red" : "blue"}
          label="Execution readiness"
          value={readiness.data?.readiness_status ?? "not evaluated"}
          helper={`${readiness.data?.summary?.blocked ?? 0} blocked / ${readiness.data?.summary?.review ?? 0} review`}
        />
      </div>

      <DecisionBrief
        blockers={personaDecision.blockers}
        className="mb-6"
        decision={personaDecision.decision}
        evidence={personaDecision.evidence}
        eyebrow={persona.label}
        nextAction={personaDecision.nextAction}
        title={personaDecision.title}
        tone={personaDecision.tone}
      />

      <SectionCard
        action={<StatusPill tone="blue">{persona.defaultNavigationLabel}</StatusPill>}
        className="mb-6"
        title="Persona operating lens"
      >
        <div className="grid gap-5 xl:grid-cols-3">
          <div>
            <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              Decisions
            </div>
            <EvidenceList items={persona.priorityActions} tone="blue" />
          </div>
          <div>
            <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              KPI lens
            </div>
            <EvidenceList
              items={persona.priorityKpis.map((item) =>
                item.replaceAll("_", " "),
              )}
              tone="emerald"
            />
          </div>
          <div>
            <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              Automation scope
            </div>
            <EvidenceList
              items={persona.allowedAutomationActions.map((item) =>
                item.replaceAll("_", " "),
              )}
              tone="blue"
            />
          </div>
        </div>
      </SectionCard>

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={controlRoomTabs}
      />

      {activeTab === "trading" ? (
        <div className="space-y-5">
          <div className="grid gap-4 xl:grid-cols-3">
            <EngineCard
              href="/forecasts"
              label="Market Intelligence"
              status={displayValue(
                metadata.forecast_model ?? metadata.forecast_provider,
                "Forecast source pending",
              )}
              title="Forecast workbench"
              value={displayValue(
                metadata.forecast_provider ?? metadata.source,
                "No active forecast",
              )}
            />
            <EngineCard
              href="/revenue"
              label="Commercial Optimization"
              status={`${activeDispatchRows.length} active dispatch interval(s)`}
              title="Revenue stack"
              value={formatCurrency(totalRevenue)}
            />
            <EngineCard
              href="/execution"
              label="Trading Operations"
              status={displayValue(
                approval.data?.approval?.status ??
                  executionProposal.data?.proposal?.approval_status,
                "Approval evidence pending",
              )}
              title="Execution control"
              value={displayValue(
                readiness.data?.readiness_status ?? guardrails.data?.automation_status,
                "Advisory mode",
              )}
            />
          </div>
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
            <DecisionSummary metadata={metadata} summary={summary} />
            <SectionCard
              action={
                <StatusPill tone={activeDispatchRows.length ? "emerald" : "slate"}>
                  {activeDispatchRows.length} active intervals
                </StatusPill>
              }
              title="Optimization timeline"
            >
              {dispatch.length ? (
                <DispatchChart rows={dispatch} />
              ) : (
                <ErrorState message="No dispatch schedule is available yet. Run optimization to generate a signal." />
              )}
            </SectionCard>
          </div>
        </div>
      ) : null}

      {activeTab === "readiness" ? (
        <div className="space-y-5">
          {enterpriseMaturity ? (
            <EnterpriseMaturityPanel enterpriseMaturity={enterpriseMaturity} />
          ) : null}
          <div className="grid gap-5 xl:grid-cols-2">
            <DataCompletenessPanel
              data={completenessPayload}
              title="Decision evidence completeness"
            />
            <RiskCompliancePanel
              ancillary={ancillary.data}
              classification={classification.data}
              eeg={eeg.data}
              signal={signalPayload}
            />
          </div>
        </div>
      ) : null}

      {activeTab === "commercial" ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(380px,0.8fr)]">
          <StrategyRecommendation
            ancillary={ancillary.data}
            businessDecision={businessDecisionPayload?.decision}
            eeg={eeg.data}
            hedgingSummary={hedgeSummary}
            metadata={metadata}
            revenueRows={revenueRows}
            summary={summary}
          />
          <RevenueStackOverview hedgingSummary={hedgeSummary} rows={revenueRows} />
        </div>
      ) : null}

      {activeTab === "execution" ? (
        <div className="space-y-5">
          <div className="grid gap-5 xl:grid-cols-2">
            <SectionCard title="Execution readiness">
              <div className="space-y-3">
                <StatusRow
                  label="Germany market adapters"
                  tone={marketAdapterStatus.data?.live_submission_enabled ? "emerald" : "blue"}
                  value={marketAdapterStatus.data?.market_adapter_status ?? "not evaluated"}
                />
                <StatusRow
                  label="Proposal"
                  tone={executionProposal.data?.proposal ? "emerald" : "amber"}
                  value={executionProposal.data?.proposal?.status ?? "missing"}
                />
                <StatusRow
                  label="Operator approval"
                  tone={approvalTone(approval.data?.approval?.status)}
                  value={approval.data?.approval?.status ?? "missing"}
                />
                <StatusRow
                  label="Telemetry"
                  tone={telemetry.data?.telemetry ? "emerald" : "amber"}
                  value={telemetry.data?.telemetry?.availability_status ?? "missing"}
                />
                <StatusRow
                  label="Settlement"
                  tone={settlement.data?.settlement ? "emerald" : "slate"}
                  value={settlement.data?.settlement?.status ?? "not reconciled"}
                />
              </div>
            </SectionCard>
            <TradingReadinessPanel readiness={readiness.data} />
          </div>

          <SectionCard
            action={
              <StatusPill tone={workflowRunPayload?.workflow_run ? "emerald" : "amber"}>
                {workflowRunPayload?.workflow_run ? "Audit linked" : "Audit pending"}
              </StatusPill>
            }
            title="Decision audit trail"
          >
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                accent="blue"
                label="Workflow run"
                value={workflowRunPayload?.workflow_run?.workflow_run_id ?? "-"}
                helper={workflowRunPayload?.workflow_run?.status ?? "No audit run yet"}
              />
              <KpiCard
                accent="blue"
                label="Forecast snapshot"
                value={workflowRunPayload?.workflow_run?.forecast_snapshot_id ?? "-"}
                helper={workflowRunPayload?.workflow_run?.forecast_provider ?? "-"}
              />
              <KpiCard
                accent="emerald"
                label="Linked signal"
                value={workflowRunPayload?.workflow_run?.signal_id ?? "-"}
                helper={workflowRunPayload?.workflow_run?.target_date ?? "-"}
              />
              <KpiCard
                accent="emerald"
                label="Linked decision"
                value={workflowRunPayload?.workflow_run?.decision_id ?? "-"}
                helper={
                  workflowRunPayload?.workflow_run?.recommendation_status ??
                  "Decision pending"
                }
              />
            </div>
          </SectionCard>
        </div>
      ) : null}

      {activeTab === "actions" ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <SectionCard title="Operator actions">
            <div className="grid gap-3 md:grid-cols-2">
              <ActionButton
                endpoint={`/demo/portfolio/run?asset_id=${selectedAssetId}`}
                label="Populate demo evidence"
                refetch={refetchCockpit}
                variant="primary"
              />
              <ActionButton
                endpoint={`/assets/${selectedAssetId}/workflow-runs/run`}
                label="Run audited workflow"
                refetch={refetchCockpit}
                variant="secondary"
              />
            </div>
          </SectionCard>
          <SectionCard
            action={<StatusPill tone="blue">Priority queue</StatusPill>}
            title="Next actions"
          >
            <EvidenceList
              items={
                enterpriseMaturity?.next_moat_actions ??
                businessDecisionPayload?.decision?.recommended_actions ??
                [
                  "Run audited workflow to refresh decision evidence.",
                  "Open Forecasts to validate trading confidence.",
                  "Open Execution to request approval before demo submission.",
                ]
              }
              tone="blue"
            />
          </SectionCard>
        </div>
      ) : null}
    </>
  );
}

function approvalTone(value?: string) {
  if (value === "approved") {
    return "emerald";
  }

  if (value === "rejected") {
    return "red";
  }

  if (value === "requested") {
    return "blue";
  }

  return "amber";
}

function buildPersonaDecisionBrief({
  activeDispatchCount,
  automationControl,
  businessDecision,
  completeness,
  enterpriseMaturity,
  guardrails,
  marketAdapterStatus,
  personaId,
  readiness,
  revenueRows,
  settlement,
  signalSummary,
  strategyIntent,
  totalRevenue,
}: {
  activeDispatchCount: number;
  automationControl?: AutomationControlStatusResponse;
  businessDecision?: BusinessDecision;
  completeness?: DataCompletenessResponse;
  enterpriseMaturity?: NonNullable<AssetCockpitResponse["cockpit"]>["enterprise_maturity"];
  guardrails?: AutomationGuardrailsResponse;
  marketAdapterStatus?: AssetMarketAdapterStatusResponse;
  personaId: string;
  readiness?: ExecutionReadinessResponse;
  revenueRows: RevenueStackResult[];
  settlement?: SettlementResponse;
  signalSummary: SignalSummary;
  strategyIntent?: StrategyIntentResponse;
  totalRevenue: number;
}): {
  blockers: string[];
  decision: React.ReactNode;
  evidence: string[];
  nextAction: string;
  title: string;
  tone: DecisionBriefTone;
} {
  const automationMode = automationControl?.automation_mode ?? "not evaluated";
  const strategyMode = strategyIntent?.strategy_mode?.replaceAll("_", " ") ?? "strategy pending";
  const dispatchBias = strategyIntent?.dispatch_bias?.replaceAll("_", " ") ?? "hold";
  const blockerCount = automationControl?.blockers?.length ?? readiness?.summary?.blocked ?? 0;
  const topBlockers = [
    ...(automationControl?.blockers ?? []).map((blocker) =>
      String(blocker.message ?? blocker.key ?? "Automation blocker"),
    ),
    ...(businessDecision?.blockers ?? []),
  ].slice(0, 4);
  const evidence = [
    `${String(signalSummary?.signal ?? "No signal")} trading signal with ${formatCurrency(signalSummary?.total_pnl_eur)} expected PnL.`,
    `${formatCurrency(totalRevenue)} modelled revenue across ${revenueRows?.length ?? 0} product(s).`,
    `Automation mode is ${String(automationMode).replaceAll("_", " ")}.`,
  ];

  if (personaId === "asset_owner") {
    return {
      blockers: topBlockers,
      decision: (
        <>
          {formatCurrency(totalRevenue)}
          <span className="text-slate-500"> / </span>
          revenue assurance
        </>
      ),
      evidence: [
        `${revenueRows?.length ?? 0} market product(s) assessed for owner value.`,
        businessDecision?.recommendation_status
          ? `Commercial decision is ${businessDecision.recommendation_status}.`
          : "Commercial decision evidence is pending.",
        enterpriseMaturity?.display_level
          ? `Enterprise maturity: ${enterpriseMaturity.display_level}.`
          : "Enterprise maturity is not scored yet.",
      ],
      nextAction:
        blockerCount > 0
          ? "Resolve the top commercial or automation blocker before presenting revenue as production-ready."
          : "Use the revenue assurance view for owner reporting and next market allocation.",
      title: "Owner value decision",
      tone: blockerCount ? "amber" : "emerald",
    };
  }

  if (personaId === "trader") {
    return {
      blockers: topBlockers,
      decision: (
        <>
          {strategyMode}
          <span className="text-slate-500"> / </span>
          {automationControl?.primary_market?.market_name ?? "route pending"}
        </>
      ),
      evidence: [
        `Dispatch bias is ${dispatchBias}.`,
        automationControl?.next_automation_action?.message ??
          "No next automation action has been evaluated.",
        marketAdapterStatus?.market_adapter_status
          ? `Market access: ${marketAdapterStatus.market_adapter_status}.`
          : "Market access is not evaluated.",
      ],
      nextAction:
        automationControl?.next_automation_action?.message ??
        "Open Mission Control to build proposal or run paper validation.",
      title: "Trading desk decision",
      tone: blockerCount ? "amber" : "emerald",
    };
  }

  if (personaId === "automation_manager") {
    return {
      blockers: topBlockers,
      decision: (
        <>
          {String(automationMode).replaceAll("_", " ")}
          <span className="text-slate-500"> / </span>
          {automationControl?.mode_escalation?.next_eligible_mode?.replaceAll("_", " ") ?? "gated"}
        </>
      ),
      evidence: [
        `${blockerCount} automation blocker(s) currently detected.`,
        automationControl?.mode_escalation?.can_escalate
          ? "Mode escalation evidence is clear."
          : "Mode escalation is gated by evidence.",
        `${automationControl?.remediation_queue?.length ?? 0} remediation item(s) queued.`,
      ],
      nextAction:
        automationControl?.next_automation_action?.message ??
        "Clear remediation and evidence blockers before increasing autonomy.",
      title: "Automation escalation decision",
      tone: automationControl?.mode_escalation?.can_escalate ? "emerald" : "amber",
    };
  }

  if (personaId === "optimizer") {
    return {
      blockers: topBlockers,
      decision: (
        <>
          {String(signalSummary?.signal ?? "No signal")}
          <span className="text-slate-500"> / </span>
          {activeDispatchCount} active intervals
        </>
      ),
      evidence: [
        `${formatNumber(signalSummary?.profit_per_mw_day, 2)} EUR/MW-day expected from latest dispatch.`,
        `${formatCurrency(totalRevenue)} modelled revenue stack.`,
        `${completeness?.score ?? 0}/100 evidence completeness score.`,
      ],
      nextAction:
        activeDispatchCount > 0
          ? "Use Trading Schedule and Forecast Trust to validate bid conversion."
          : "Run optimization to generate a tradable schedule.",
      title: "Optimization decision",
      tone: activeDispatchCount > 0 ? "emerald" : "amber",
    };
  }

  if (personaId === "risk_compliance") {
    return {
      blockers: topBlockers,
      decision: (
        <>
          {guardrails?.automation_status ?? "not evaluated"}
          <span className="text-slate-500"> / </span>
          {settlement?.settlement?.status ?? "settlement pending"}
        </>
      ),
      evidence: [
        `${guardrails?.summary?.blocked ?? 0} blocked guardrail(s), ${guardrails?.summary?.review ?? 0} review item(s).`,
        readiness?.readiness_status
          ? `Execution readiness is ${readiness.readiness_status}.`
          : "Execution readiness is not evaluated.",
        settlement?.settlement
          ? "Settlement evidence exists."
          : "Settlement evidence is not reconciled yet.",
      ],
      nextAction:
        blockerCount > 0
          ? "Review Automation Gates and Audit Evidence before approving automation."
          : "Keep audit and settlement evidence attached to the trading packet.",
      title: "Governance decision",
      tone: blockerCount ? "amber" : "emerald",
    };
  }

  if (personaId === "executive") {
    return {
      blockers: topBlockers,
      decision: (
        <>
          {enterpriseMaturity?.display_level ?? "maturity pending"}
          <span className="text-slate-500"> / </span>
          {formatCurrency(totalRevenue)}
        </>
      ),
      evidence: [
        `${formatCurrency(signalSummary?.total_pnl_eur)} expected PnL from latest signal.`,
        `${enterpriseMaturity?.differentiation_score ?? 0}/100 differentiation score.`,
        `${blockerCount} blocker(s) separating demo evidence from production automation.`,
      ],
      nextAction:
        blockerCount > 0
          ? "Focus the team on the top blocker before promising production-grade automated trading."
          : "Use Reports and Revenue Assurance for stakeholder communication.",
      title: "Executive operating decision",
      tone: blockerCount ? "amber" : "emerald",
    };
  }

  return {
    blockers: topBlockers,
    decision: (
      <>
        {strategyMode}
        <span className="text-slate-500"> / </span>
        {dispatchBias}
      </>
    ),
    evidence,
    nextAction:
      automationControl?.next_automation_action?.message ??
      "Use the workspace tabs below to validate trading, readiness, commercial value, and execution evidence.",
    title: "Platform decision",
    tone: blockerCount ? "amber" : "emerald",
  };
}

function displayValue(value: unknown, fallback: string) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  return fallback;
}
