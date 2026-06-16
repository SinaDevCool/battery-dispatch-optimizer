"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { ActionButton } from "@/components/action-button";
import {
  AssetDataProfileSection,
  buildAssetDataProfileEvidence,
  formatDataMode,
} from "@/components/asset-data-profile-section";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { EvidenceSourceSection } from "@/components/evidence-source-section";
import { ErrorState } from "@/components/error-state";
import {
  ExecutionAuditPanel,
  ExecutionOverviewPanel,
  ExecutionRiskApprovalPanel,
  ExecutionSettlementPanel,
  ExecutionSimulationPanel,
} from "@/components/execution/execution-workspace-panels";
import { ExecutionMissionSummary } from "@/components/execution/execution-mission-summary";
import { MarketAllocationPanel } from "@/components/execution/market-allocation-panel";
import {
  buildTradingAutomationPipelineStages,
  TradingAutomationPipeline,
} from "@/components/execution/trading-automation-pipeline";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type {
  AutomationControlStatusResponse,
  AutomationEventHistoryResponse,
  AutomationModeEscalation,
  AutomationGuardrailsResponse,
  AssetTelemetryResponse,
  AssetMarketAdapterStatusResponse,
  ExecutionApprovalResponse,
  ExecutionPaperTradeHistoryResponse,
  ExecutionPaperTradeResponse,
  ExecutionProposalHistoryResponse,
  ExecutionProposalResponse,
  ExecutionReadinessResponse,
  ExecutionSummaryResponse,
  LiveTradingReadinessResponse,
  ExecutionRecoveryPlanResponse,
  EpexDayAheadPreviewResponse,
  EpexIntradayAuctionPreviewResponse,
  EpexIntradayContinuousPreviewResponse,
  ForecastConfidenceResponse,
  LatestSignalResponse,
  MarketConnectorReadinessResponse,
  MarketSubmissionLifecycleResponse,
  MarketSubmissionResponse,
  MultiMarketAllocationResponse,
  RegelleistungAfrrPreviewResponse,
  RegelleistungFcrPreviewResponse,
  RegelleistungMfrrPreviewResponse,
  RouteAutomationCertification,
  SettlementResponse,
  StrategyIntentResponse,
  TableRow,
} from "@/types/api";

const executionTabs = [
  {
    id: "overview",
    label: "Control",
    helper: "Automation mode, next action, lifecycle status, and current engine state.",
  },
  {
    id: "golive",
    label: "Go-Live",
    helper: "Official API compliance, route certification, sandbox evidence, and supervised-live readiness.",
  },
  {
    id: "allocation",
    label: "Market Route",
    helper: "Ranked German market routes, capacity allocation, and excluded-market reasons.",
  },
  {
    id: "proposals",
    label: "Bid Engine",
    helper: "Automated bid packets, position limits, and proposal history.",
  },
  {
    id: "risk",
    label: "Risk Gates",
    helper: "Automation guardrails, forecast confidence, human gate policy, and blockers.",
  },
  {
    id: "simulation",
    label: "Paper Trading",
    helper: "Paper fills, paper PnL, and simulated market submission status.",
  },
  {
    id: "settlement",
    label: "Settlement",
    helper: "Reconciliation, variance drivers, and realized economics.",
  },
  {
    id: "audit",
    label: "Audit",
    helper: "Backend checks, lifecycle steps, and automation event trail.",
  },
] as const;

export type ExecutionTabId = (typeof executionTabs)[number]["id"];

const clientExecutionTabs = [
  {
    id: "overview",
    label: "Execution Summary",
    helper: "Approved route, current readiness, and the next execution decision.",
  },
  {
    id: "risk",
    label: "Approval Gates",
    helper: "Policy blockers, forecast confidence, and human approval evidence.",
  },
  {
    id: "settlement",
    label: "Settlement",
    helper: "Reconciliation, variance drivers, and realized economics.",
  },
  {
    id: "audit",
    label: "Audit Evidence",
    helper: "Backend checks, lifecycle steps, and evidence trail.",
  },
] as const satisfies readonly {
  helper: string;
  id: ExecutionTabId;
  label: string;
}[];

export default function ExecutionPage({
  description = "Monitor and run the automated battery trading lifecycle from signal to route selection, bid generation, paper validation, human gate, submission evidence, and settlement reconciliation.",
  eyebrow = "Automated trading",
  initialTab = "overview",
  showTabs = true,
  title = "Automated Trading Cockpit",
}: {
  description?: string;
  eyebrow?: string;
  initialTab?: ExecutionTabId;
  showTabs?: boolean;
  title?: string;
} = {}) {
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const isClientPersona = persona.layer === "client";
  const visibleExecutionTabs = isClientPersona ? clientExecutionTabs : executionTabs;
  const [requestedActiveTab, setActiveTab] = useState<ExecutionTabId>(initialTab);
  const activeTab = visibleExecutionTabs.some((tab) => tab.id === requestedActiveTab)
    ? requestedActiveTab
    : visibleExecutionTabs[0].id;
  const isOverviewTab = activeTab === "overview";
  const isGoLiveTab = activeTab === "golive";
  const isAllocationTab = activeTab === "allocation";
  const isProposalsTab = activeTab === "proposals";
  const isRiskTab = activeTab === "risk";
  const isSimulationTab = activeTab === "simulation";
  const isSettlementTab = activeTab === "settlement";
  const isAuditTab = activeTab === "audit";

  const executionSummary = useQuery({
    queryFn: () =>
      apiGet<ExecutionSummaryResponse>(
        `/assets/${selectedAssetId}/execution-summary`,
      ),
    queryKey: ["execution-summary", selectedAssetId],
  });

  const latestProposal = useQuery({
    enabled: isProposalsTab || isRiskTab,
    queryFn: () =>
      apiGet<ExecutionProposalResponse>(
        `/assets/${selectedAssetId}/execution/proposal/latest`,
      ),
    queryKey: ["execution-proposal-latest", selectedAssetId],
  });

  const automationControl = useQuery({
    enabled: isGoLiveTab || isAuditTab,
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["execution-automation-control", selectedAssetId],
  });

  const liveTradingReadiness = useQuery({
    enabled: isGoLiveTab,
    queryFn: () =>
      apiGet<LiveTradingReadinessResponse>(
        `/assets/${selectedAssetId}/execution/live-trading-readiness?country=Germany`,
      ),
    queryKey: ["execution-live-trading-readiness", selectedAssetId],
  });

  const automationEvents = useQuery({
    enabled: isAuditTab,
    queryFn: () =>
      apiGet<AutomationEventHistoryResponse>(
        `/assets/${selectedAssetId}/execution/automation-events?limit=12`,
      ),
    queryKey: ["execution-automation-events", selectedAssetId],
  });

  const strategyIntent = useQuery({
    queryFn: () =>
      apiGet<StrategyIntentResponse>(
        `/assets/${selectedAssetId}/execution/strategy-intent`,
      ),
    queryKey: ["execution-strategy-intent", selectedAssetId],
  });

  const proposalHistory = useQuery({
    enabled: isProposalsTab,
    queryFn: () =>
      apiGet<ExecutionProposalHistoryResponse>(
        `/assets/${selectedAssetId}/execution/proposals?limit=10`,
      ),
    queryKey: ["execution-proposal-history", selectedAssetId],
  });

  const latestPaperTrade = useQuery({
    enabled: isSimulationTab || isAuditTab,
    queryFn: () =>
      apiGet<ExecutionPaperTradeResponse>(
        `/assets/${selectedAssetId}/execution/paper-trade/latest`,
      ),
    queryKey: ["execution-paper-trade-latest", selectedAssetId],
  });

  const paperTradeHistory = useQuery({
    enabled: isSimulationTab,
    queryFn: () =>
      apiGet<ExecutionPaperTradeHistoryResponse>(
        `/assets/${selectedAssetId}/execution/paper-trades?limit=10`,
      ),
    queryKey: ["execution-paper-trade-history", selectedAssetId],
  });

  const signal = useQuery({
    enabled: isAllocationTab || isRiskTab,
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["execution-signal-latest", selectedAssetId],
  });

  const settlement = useQuery({
    enabled: isSettlementTab || isAuditTab,
    queryFn: () =>
      apiGet<SettlementResponse>(
        `/assets/${selectedAssetId}/settlement/latest`,
      ),
    queryKey: ["execution-settlement-latest", selectedAssetId],
  });

  const forecastConfidence = useQuery({
    enabled: isRiskTab,
    queryFn: () =>
      apiGet<ForecastConfidenceResponse>(
        `/assets/${selectedAssetId}/forecast-confidence`,
      ),
    queryKey: ["execution-forecast-confidence", selectedAssetId],
  });

  const automationGuardrails = useQuery({
    enabled: isRiskTab,
    queryFn: () =>
      apiGet<AutomationGuardrailsResponse>(
        `/assets/${selectedAssetId}/execution/automation-guardrails`,
      ),
    queryKey: ["execution-automation-guardrails", selectedAssetId],
  });

  const telemetry = useQuery({
    enabled: isAuditTab,
    queryFn: () =>
      apiGet<AssetTelemetryResponse>(
        `/assets/${selectedAssetId}/telemetry/latest`,
      ),
    queryKey: ["execution-telemetry-latest", selectedAssetId],
  });

  const marketSubmission = useQuery({
    enabled: isSimulationTab || isAuditTab,
    queryFn: () =>
      apiGet<MarketSubmissionResponse>(
        `/assets/${selectedAssetId}/execution/submissions/latest`,
      ),
    queryKey: ["execution-market-submission-latest", selectedAssetId],
  });

  const submissionLifecycle = useQuery({
    enabled: isSimulationTab || isAuditTab,
    queryFn: () =>
      apiGet<MarketSubmissionLifecycleResponse>(
        `/assets/${selectedAssetId}/execution/submission-lifecycle`,
      ),
    queryKey: ["execution-submission-lifecycle", selectedAssetId],
  });

  const recoveryPlan = useQuery({
    enabled: isRiskTab,
    queryFn: () =>
      apiGet<ExecutionRecoveryPlanResponse>(
        `/assets/${selectedAssetId}/execution/recovery-plan`,
      ),
    queryKey: ["execution-recovery-plan", selectedAssetId],
  });

  const approval = useQuery({
    enabled: isRiskTab || isAuditTab,
    queryFn: () =>
      apiGet<ExecutionApprovalResponse>(
        `/assets/${selectedAssetId}/execution/approval/latest`,
      ),
    queryKey: ["execution-approval-latest", selectedAssetId],
  });

  const readiness = useQuery({
    enabled: isGoLiveTab || isAllocationTab || isRiskTab,
    queryFn: () =>
      apiGet<ExecutionReadinessResponse>(
        `/assets/${selectedAssetId}/execution/readiness`,
      ),
    queryKey: ["execution-readiness", selectedAssetId],
  });

  const marketAdapterStatus = useQuery({
    enabled: isOverviewTab,
    queryFn: () =>
      apiGet<AssetMarketAdapterStatusResponse>(
        `/assets/${selectedAssetId}/execution/market-adapter/status`,
      ),
    queryKey: ["execution-market-adapter-status", selectedAssetId],
  });

  const marketConnectorReadiness = useQuery({
    enabled: isGoLiveTab,
    queryFn: () =>
      apiGet<MarketConnectorReadinessResponse>(
        `/execution/market-connectors/readiness?country=Germany&asset_id=${selectedAssetId}`,
      ),
    queryKey: ["execution-market-connectors-readiness", selectedAssetId],
  });

  const multiMarketAllocation = useQuery({
    enabled: isAllocationTab || isGoLiveTab,
    queryFn: () =>
      apiGet<MultiMarketAllocationResponse>(
        `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      ),
    queryKey: ["execution-multi-market-allocation", selectedAssetId],
  });

  const epexDayAheadPreview = useQuery({
    enabled: isAllocationTab,
    queryFn: () =>
      apiGet<EpexDayAheadPreviewResponse>(
        `/assets/${selectedAssetId}/execution/epex/day-ahead/preview`,
      ),
    queryKey: ["execution-epex-day-ahead-preview", selectedAssetId],
  });

  const epexIntradayAuctionPreview = useQuery({
    enabled: isAllocationTab,
    queryFn: () =>
      apiGet<EpexIntradayAuctionPreviewResponse>(
        `/assets/${selectedAssetId}/execution/epex/intraday-auction/preview`,
      ),
    queryKey: ["execution-epex-intraday-auction-preview", selectedAssetId],
  });

  const epexIntradayContinuousPreview = useQuery({
    enabled: isAllocationTab,
    queryFn: () =>
      apiGet<EpexIntradayContinuousPreviewResponse>(
        `/assets/${selectedAssetId}/execution/epex/intraday-continuous/preview`,
      ),
    queryKey: ["execution-epex-intraday-continuous-preview", selectedAssetId],
  });

  const regelleistungFcrPreview = useQuery({
    enabled: isAllocationTab,
    queryFn: () =>
      apiGet<RegelleistungFcrPreviewResponse>(
        `/assets/${selectedAssetId}/execution/regelleistung/fcr/preview`,
      ),
    queryKey: ["execution-regelleistung-fcr-preview", selectedAssetId],
  });

  const regelleistungAfrrPreview = useQuery({
    enabled: isAllocationTab,
    queryFn: () =>
      apiGet<RegelleistungAfrrPreviewResponse>(
        `/assets/${selectedAssetId}/execution/regelleistung/afrr/preview`,
      ),
    queryKey: ["execution-regelleistung-afrr-preview", selectedAssetId],
  });

  const regelleistungMfrrPreview = useQuery({
    enabled: isAllocationTab,
    queryFn: () =>
      apiGet<RegelleistungMfrrPreviewResponse>(
        `/assets/${selectedAssetId}/execution/regelleistung/mfrr/preview`,
      ),
    queryKey: ["execution-regelleistung-mfrr-preview", selectedAssetId],
  });

  const proposalData =
    latestProposal.data ?? executionSummary.data?.execution_proposal;
  const signalData = signal.data ?? executionSummary.data?.latest_signal;
  const automationControlData =
    automationControl.data ?? executionSummary.data?.automation_control;
  const automationGuardrailsData =
    automationGuardrails.data ?? executionSummary.data?.automation_guardrails;
  const readinessData =
    readiness.data ?? executionSummary.data?.execution_readiness;
  const latestPaperTradeData =
    latestPaperTrade.data ?? executionSummary.data?.paper_trade;
  const marketSubmissionData =
    marketSubmission.data ?? executionSummary.data?.market_submission;
  const approvalResponseData = approval.data ?? executionSummary.data?.approval;
  const marketAllocationData =
    multiMarketAllocation.data ?? executionSummary.data?.multi_market_allocation;
  const telemetryResponseData = telemetry.data ?? executionSummary.data?.telemetry;

  const proposal = proposalData?.proposal;
  const signalSummary = signalData?.data?.summary ?? {};
  const orders = proposal?.orders ?? [];
  const bids = proposal?.bids ?? orders;
  const riskChecks = proposal?.risk_checks ?? [];
  const auditRows = proposal?.audit ?? [];
  const automationBlockers = proposal?.automation_blockers ?? [];
  const hardBlockers = proposal?.blockers ?? [];
  const summary = proposal?.summary ?? {};
  const bidPackage = proposal?.bid_package;
  const bidPackageSummary = bidPackage?.summary ?? {};
  const expectedPnl = Number(
    summary.expected_pnl_eur ?? signalSummary.total_pnl_eur ?? 0,
  );
  const profitPerMwDay =
    summary.profit_per_mw_day ?? signalSummary.profit_per_mw_day;
  const paperTrade = latestPaperTradeData?.paper_trade;
  const paperTradeFills = paperTrade?.fills ?? [];
  const lifecycleRows =
    submissionLifecycle.data?.steps ??
    paperTrade?.bid_lifecycle ??
    proposal?.bid_lifecycle ??
    [];
  const settlementData = settlement.data?.settlement;
  const settlementSummary = settlementData?.summary ?? {};
  const varianceDrivers = settlementData?.variance_drivers ?? [];
  const confidence = proposal?.forecast_confidence ?? forecastConfidence.data;
  const automationStatus = automationGuardrailsData?.automation_status;
  const guardrailSummary = automationGuardrailsData?.summary ?? {};
  const guardrails = automationGuardrailsData?.guardrails ?? [];
  const telemetryData = telemetryResponseData?.telemetry;
  const submission = marketSubmissionData?.submission;
  const submissionSummary = submission?.summary ?? {};
  const approvalData = approvalResponseData?.approval;
  const marketAllocation = marketAllocationData;
  const connectorReadiness = marketConnectorReadiness.data;
  const connectorSummary = connectorReadiness?.summary ?? {};
  const routeCertifications = connectorReadiness?.route_certifications ?? [];
  const control = automationControlData;
  const eventRows = automationEvents.data?.events ?? [];
  const humanGate = control?.human_gate ?? {};
  const nextAutomationAction = control?.next_automation_action ?? {};
  const controlBlockers = control?.blockers ?? [];
  const freshnessGates = control?.freshness_gates ?? [];
  const modeEscalation = control?.mode_escalation;
  const remediationQueue = control?.remediation_queue ?? [];
  const recovery = recoveryPlan.data;
  const primaryMarket = control?.primary_market ?? marketAllocation?.primary_market;
  const intent = strategyIntent.data;
  const assetDataProfileEvidence = buildAssetDataProfileEvidence(selectedAsset);
  const assetProfile = selectedAsset?.data_profile ?? {};
  const executionAdapterMode = String(
    assetProfile.execution_adapter ?? "mock execution adapter",
  );
  const settlementMode = String(assetProfile.settlement_mode ?? "mock settlement");
  const dataMode = formatDataMode(selectedAsset?.data_mode);
  const executionSourceMetadata: TableRow = {
    ...(executionSummary.data?.metadata ?? {}),
    ...(latestProposal.data?.metadata ?? {}),
    ...(signalData?.data?.metadata ?? {}),
    asset_id: executionSummary.data?.metadata?.asset_id ?? selectedAssetId,
    asset_type: executionSummary.data?.metadata?.asset_type ?? selectedAsset?.asset_type,
    data_mode: executionSummary.data?.metadata?.data_mode ?? selectedAsset?.data_mode ?? "mock",
    generated_at:
      executionSummary.data?.metadata?.generated_at ??
      latestProposal.data?.metadata?.generated_at ??
      proposal?.generated_at ??
      signalData?.data?.metadata?.generated_at ??
      telemetryData?.captured_at,
    mock_or_production:
      executionSummary.data?.metadata?.mock_or_production ??
      selectedAsset?.data_mode ??
      "mock",
  };
  const backendExecutionKpis = normalizeProofKpis(
    executionSummary.data?.execution_proof?.kpis,
  );
  const visibleExecutionRows = executionSummary.data?.execution_proof?.rows ?? [];
  const pipelineStages = useMemo(
    () =>
      buildTradingAutomationPipelineStages({
        allocationReady: Boolean(primaryMarket),
        approvalStatus: String(humanGate.status ?? approvalData?.status ?? ""),
        eligibilityReady:
          readinessData?.readiness_status !== "blocked" &&
          Number(marketAllocation?.summary?.eligible_market_count ?? 0) > 0,
        paperTradeReady: Boolean(paperTrade),
        proposalReady: Boolean(proposal),
        settlementReady: Boolean(settlementData),
        signalReady: signalSummary.signal === "ACTION",
        submissionReady: Boolean(submission),
        values: {
          allocation: {
            blockerCount: marketAllocation?.excluded_markets?.length ?? 0,
            evidence: primaryMarket?.market_name ?? "No primary route",
            nextAction:
              primaryMarket?.operator_next_action ??
              marketAllocation?.recommended_actions?.[0],
          },
          approval: {
            blockerCount: approvalData?.status === "rejected" ? 1 : 0,
            evidence: String(humanGate.status ?? approvalData?.status ?? "not requested"),
            nextAction: String(nextAutomationAction.label ?? "Follow automation policy"),
          },
          eligibility: {
            blockerCount:
              Number(readinessData?.summary?.blocked ?? 0) +
              Number(automationGuardrailsData?.summary?.blocked ?? 0),
            evidence: readinessData?.readiness_status ?? "not evaluated",
            nextAction:
              readinessData?.recommended_actions?.[0] ??
              automationGuardrailsData?.recommended_actions?.[0],
          },
          paper: {
            blockerCount: paperTrade ? 0 : proposal ? 0 : 1,
            evidence: paperTrade
              ? `${formatCurrency(paperTrade.summary?.paper_pnl_eur)} paper PnL`
              : "No paper run",
            nextAction: proposal ? "Run automatic paper validation" : "Build proposal first",
          },
          proposal: {
            blockerCount: automationBlockers.length + hardBlockers.length,
            evidence: proposal
              ? `${bids.length} bid(s), ${formatCurrency(summary.expected_pnl_eur)} expected`
              : "No order package",
            nextAction: nextAutomationAction.message
              ? String(nextAutomationAction.message)
              : proposal
                ? "Progress order package"
                : "Build automated proposal",
          },
          settlement: {
            blockerCount: varianceDrivers.length,
            evidence: settlementData
              ? `${formatCurrency(settlementSummary.realized_pnl_eur)} realized`
              : "No settlement evidence",
            nextAction: settlementData
              ? "Use variance feedback"
              : "Reconcile after submission",
          },
          signal: {
            blockerCount: signalSummary.signal === "ACTION" ? 0 : 1,
            evidence: String(signalSummary.signal ?? "no signal"),
            nextAction:
              signalSummary.signal === "ACTION"
                ? "Route signal to allocation"
                : "Wait for tradable signal",
          },
          submission: {
            blockerCount: submission ? 0 : control?.live_trading_allowed ? 0 : 1,
            evidence: submission
              ? `${submissionSummary.submitted_bid_count ?? 0} submitted`
              : "No market submission",
            nextAction: control?.live_trading_allowed
              ? "Prepare supervised submission"
              : "Live submission gated",
          },
        },
      }),
    [
      approvalData?.status,
      automationBlockers.length,
      automationGuardrailsData?.recommended_actions,
      automationGuardrailsData?.summary?.blocked,
      bids.length,
      control?.live_trading_allowed,
      hardBlockers.length,
      humanGate.status,
      marketAllocation?.excluded_markets?.length,
      marketAllocation?.recommended_actions,
      marketAllocation?.summary?.eligible_market_count,
      nextAutomationAction.label,
      nextAutomationAction.message,
      paperTrade,
      primaryMarket,
      proposal,
      readinessData?.readiness_status,
      readinessData?.recommended_actions,
      readinessData?.summary?.blocked,
      settlementData,
      settlementSummary.realized_pnl_eur,
      signalSummary.signal,
      submission,
      submissionSummary.submitted_bid_count,
      summary.expected_pnl_eur,
      varianceDrivers.length,
    ],
  );
  const proposalFraming = getProposalPersonaFraming(personaId);

  const refetchExecution = () =>
    Promise.all([
      executionSummary.refetch(),
      latestProposal.refetch(),
      automationControl.refetch(),
      strategyIntent.refetch(),
      automationGuardrails.refetch(),
      readiness.refetch(),
      signal.refetch(),
      ...(isOverviewTab
        ? [
            latestPaperTrade.refetch(),
            telemetry.refetch(),
            marketSubmission.refetch(),
            approval.refetch(),
            marketAdapterStatus.refetch(),
            multiMarketAllocation.refetch(),
          ]
        : []),
      ...(isGoLiveTab
        ? [
            liveTradingReadiness.refetch(),
            marketConnectorReadiness.refetch(),
            multiMarketAllocation.refetch(),
          ]
        : []),
      ...(isAllocationTab
        ? [
            multiMarketAllocation.refetch(),
            epexDayAheadPreview.refetch(),
            epexIntradayAuctionPreview.refetch(),
            epexIntradayContinuousPreview.refetch(),
            regelleistungFcrPreview.refetch(),
            regelleistungAfrrPreview.refetch(),
            regelleistungMfrrPreview.refetch(),
          ]
        : []),
      ...(isProposalsTab ? [proposalHistory.refetch()] : []),
      ...(isRiskTab
        ? [
            forecastConfidence.refetch(),
            recoveryPlan.refetch(),
            approval.refetch(),
          ]
        : []),
      ...(isSimulationTab
        ? [
            latestPaperTrade.refetch(),
            paperTradeHistory.refetch(),
            marketSubmission.refetch(),
            submissionLifecycle.refetch(),
          ]
        : []),
      ...(isSettlementTab ? [settlement.refetch()] : []),
      ...(isAuditTab
        ? [
            automationEvents.refetch(),
            latestPaperTrade.refetch(),
            settlement.refetch(),
            submissionLifecycle.refetch(),
            marketSubmission.refetch(),
            approval.refetch(),
            telemetry.refetch(),
          ]
        : []),
    ]);

  return (
    <>
      <PageHeading
        description={description}
        eyebrow={eyebrow}
        title={title}
      />

      {proposalData?.status === "not_found" ? (
        <div className="mb-6">
          <ErrorState message="No backend execution proposal exists yet. Build a pre-trade proposal after generating a signal or audited workflow." />
        </div>
      ) : null}

      {!showTabs ? (
        <>
          <AssetDataProfileSection
            asset={selectedAsset}
            className="mb-6"
            title="Selected settlement asset profile"
          />

          <EvidenceSourceSection
            asset={selectedAsset}
            className="mb-6"
            metadata={executionSourceMetadata}
            title="Can settlement prove delivery?"
          />
        </>
      ) : null}

      {showTabs ? (
        <ExecutionMissionSummary
          automationStatus={automationStatus}
          blockers={controlBlockers.map((blocker) =>
            String(blocker.message ?? blocker.key ?? "Automation blocker"),
          )}
          control={control}
          decision={
            <>
              {intent?.strategy_mode?.replaceAll("_", " ") ?? "Strategy pending"}
              <span className="text-slate-500"> / </span>
              {intent?.dispatch_bias?.replaceAll("_", " ") ?? "hold"}
            </>
          }
          evidence={[
            ...(intent?.why ?? []).slice(0, 3),
            primaryMarket?.market_name
              ? `Primary route: ${primaryMarket.market_name}.`
              : "No primary market route is selected yet.",
            `${connectorSummary.official_api_compliant_route_count ?? 0}/${connectorSummary.official_api_route_count ?? 0} route(s) meet official API compliance gates.`,
            `${connectorSummary.paper_certified_count ?? 0} market route(s) are certified for automated paper execution.`,
            `${connectorSummary.certified_route_count ?? 0}/${connectorSummary.route_certification_count ?? 0} route(s) have route-level automation certification.`,
            `${connectorSummary.supervised_live_candidate_count ?? 0} route(s) clear supervised-live readiness.`,
            `${connectorSummary.handshake_ready_count ?? 0}/${connectorSummary.handshake_target_count ?? 0} live adapter handshakes are dry-run ready.`,
            ...assetDataProfileEvidence,
          ]}
          dataMode={dataMode}
          executionAdapterMode={executionAdapterMode}
          expectedPnl={expectedPnl}
          guardrailBlocked={Number(guardrailSummary.blocked ?? 0)}
          guardrailReview={Number(guardrailSummary.review ?? 0)}
          humanGateRequired={Boolean(humanGate.required)}
          humanGateStatus={humanGate.status}
          isClientPersona={isClientPersona}
          marketRoute={primaryMarket?.market_name ?? proposal?.market}
          nextAutomationAction={nextAutomationAction}
          primaryRouteHelper={primaryMarket?.adapter_id ?? selectedAsset?.market}
          profitPerMwDay={Number(profitPerMwDay ?? 0)}
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
          settlementMode={settlementMode}
        />
      ) : null}

      {showTabs ? (
        <WorkspaceTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={visibleExecutionTabs}
        />
      ) : null}

      {activeTab === "overview" ? (
        <div className="space-y-5">
          <TradingAutomationPipeline stages={pipelineStages} />
          <StrategyIntentPanel intent={intent} />
          <ExecutionOverviewPanel
            approvalData={approvalData}
            automationStatus={automationStatus}
            bids={bids}
            hardBlockers={hardBlockers}
            marketAdapterStatus={marketAdapterStatus.data}
            paperTrade={paperTrade}
            personaId={personaId}
            proposal={proposal}
            readiness={readinessData}
            refetchExecution={refetchExecution}
            selectedAssetId={selectedAssetId}
            submission={submission}
            telemetryData={telemetryData}
          />
        </div>
      ) : null}

      {activeTab === "golive" ? (
        <div className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <KpiCard
              accent={officialApiTone(connectorReadiness?.official_api_compliance_status)}
              label="Official API"
              value={connectorReadiness?.official_api_compliance_status ?? "-"}
              helper={`${connectorSummary.official_api_compliant_route_count ?? 0}/${connectorSummary.official_api_route_count ?? 0} compliant`}
            />
            <KpiCard
              accent={routeCertificationTone(connectorReadiness?.route_certification_status)}
              label="Route certification"
              value={connectorReadiness?.route_certification_status ?? "-"}
              helper={`${connectorSummary.certified_route_count ?? 0}/${connectorSummary.route_certification_count ?? 0} certified`}
            />
            <KpiCard
              accent={sandboxCertificationTone(connectorReadiness?.sandbox_certification_status)}
              label="Sandbox certification"
              value={connectorReadiness?.sandbox_certification_status ?? "-"}
              helper={`${connectorSummary.paper_certified_count ?? 0} paper / ${connectorSummary.supervised_live_certified_count ?? 0} supervised live`}
            />
            <KpiCard
              accent={supervisedLiveGateTone(connectorReadiness?.supervised_live_gate_status)}
              label="Supervised live gate"
              value={connectorReadiness?.supervised_live_gate_status ?? "-"}
              helper={`${connectorSummary.supervised_live_candidate_count ?? 0} candidate / ${connectorSummary.paper_ready_live_blocked_count ?? 0} blocked`}
            />
            <KpiCard
              accent={handshakeTone(connectorReadiness?.handshake_readiness_status)}
              label="Live handshake"
              value={connectorReadiness?.handshake_readiness_status ?? "-"}
              helper={`${connectorSummary.handshake_ready_count ?? 0}/${connectorSummary.handshake_target_count ?? 0} dry-run ready`}
            />
          </div>
          <GoLiveReadinessPanel
            data={liveTradingReadiness.data}
            refetchExecution={refetchExecution}
          />
          <RouteCertificationPanel
            routes={routeCertifications}
            status={connectorReadiness?.route_certification_status}
          />
        </div>
      ) : null}

      {activeTab === "allocation" ? (
        <MarketAllocationPanel
          allocation={marketAllocation}
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
        />
      ) : null}

      {activeTab === "proposals" ? (
        <div className="space-y-5">
          <DecisionBrief
            blockers={[
              ...automationBlockers.map(String),
              ...hardBlockers.map(String),
              ...controlBlockers.map((blocker) =>
                String(blocker.message ?? blocker.key ?? "Automation blocker"),
              ),
            ].slice(0, 4)}
            decision={
              proposal
                ? `${bids.length} bid package${bids.length === 1 ? "" : "s"} / ${proposal.approval_status ?? proposal.status ?? "draft"}`
                : "No automated bid package has been built yet."
            }
            evidence={[
              `Expected PnL ${formatCurrency(summary.expected_pnl_eur ?? expectedPnl)}.`,
              `Route ${primaryMarket?.market_name ?? proposal?.market ?? "not selected"}.`,
              `Gate ${String(summary.market_gate_closure ?? primaryMarket?.gate_closure_label ?? "not configured")}.`,
              `Order style ${String(summary.order_style ?? primaryMarket?.order_style ?? "not configured").replaceAll("_", " ")}.`,
              `Package ${String(summary.package_validation_status ?? bidPackage?.validation?.status ?? "not built")}.`,
              `Paper mode ${control?.paper_trading_allowed ? "allowed" : "gated"}.`,
              `Execution adapter: ${executionAdapterMode}.`,
              `Data mode: ${dataMode}.`,
            ]}
            eyebrow={proposalFraming.decisionEyebrow}
            nextAction={
              proposal
                ? nextAutomationAction.message ?? proposalFraming.nextActionBuilt
                : proposalFraming.nextActionMissing
            }
            title={proposalFraming.decisionTitle}
            tone={automationBlockers.length || hardBlockers.length ? "amber" : proposal ? "emerald" : "blue"}
          />
          <TradingAutomationPipeline
            currentStageId="proposal"
            stages={pipelineStages}
            title={proposalFraming.pipelineTitle}
          />
          <SectionCard
            action={<StatusPill tone={bidPackageTone(bidPackage?.package_status)}>{bidPackage?.package_status ?? "not built"}</StatusPill>}
            title={proposalFraming.packageTitle}
          >
            <div className="mb-4 grid gap-3 md:grid-cols-4">
              <KpiCard
                accent="blue"
                helper={String(bidPackage?.order_style ?? "-").replaceAll("_", " ")}
                label="Adapter"
                value={bidPackage?.adapter_id ?? "-"}
              />
              <KpiCard
                accent={bidPackageTone(bidPackage?.validation?.status)}
                helper="Package validation"
                label="Validation"
                value={bidPackage?.validation?.status ?? "-"}
              />
              <KpiCard
                accent="emerald"
                helper={`${formatNumber(bidPackageSummary.buy_order_count, 0)} buy / ${formatNumber(bidPackageSummary.sell_order_count, 0)} sell`}
                label="Energy orders"
                value={formatNumber(bidPackageSummary.order_count, 0)}
              />
              <KpiCard
                accent={Number(bidPackageSummary.reserve_order_count ?? 0) ? "emerald" : "slate"}
                helper={`${formatNumber(bidPackageSummary.total_reserve_mw, 2)} MW reserve`}
                label="Reserve orders"
                value={formatNumber(bidPackageSummary.reserve_order_count, 0)}
              />
            </div>
            <DataTable
              columns={["check", "status", "message"]}
              rows={(bidPackage?.validation?.checks ?? []).slice(0, 5)}
            />
          </SectionCard>
          <SectionCard
            action={
              <ActionButton
                endpoint={`/assets/${selectedAssetId}/execution/proposal/build`}
                label="Build pre-trade proposal"
                refetch={refetchExecution}
                variant="primary"
              />
            }
            title={proposalFraming.ordersTitle}
          >
            <DataTable
              columns={[
                "bid_id",
                "adapter_id",
                "market_product_id",
                "market_product",
                "package_order_type",
                "automation_lane",
                "gate_closure_label",
                "side",
                "bid_type",
                "volume_mw",
                "capacity_mw",
                "energy_mwh",
                "limit_price_eur_mwh",
                "risk_adjusted_limit_price_eur_mwh",
                "forecast_confidence_score",
                "automation_eligibility",
                "approval_status",
                "submission_status",
                "market_lifecycle_status",
                "lifecycle_status",
              ]}
              rows={bids.slice(0, 12)}
            />
          </SectionCard>

          <SectionCard title={proposalFraming.limitsTitle}>
            <DataTable
              columns={["limit", "value", "status"]}
              rows={[
                {
                  limit: "Total buy energy",
                  status: "draft",
                  value: `${formatNumber(
                    summary.total_buy_mwh ?? signalSummary.charged_mwh,
                    2,
                  )} MWh`,
                },
                {
                  limit: "Total sell energy",
                  status: "draft",
                  value: `${formatNumber(
                    summary.total_sell_mwh ?? signalSummary.discharged_mwh,
                    2,
                  )} MWh`,
                },
                {
                  limit: "Max loss per day",
                  status: expectedPnl > -Number(summary.max_daily_loss_eur ?? 0) ? "within limit" : "breach",
                  value: formatCurrency(summary.max_daily_loss_eur),
                },
                {
                  limit: "Linked workflow",
                  status: proposal?.workflow_run_id ? "linked" : "not linked",
                  value: proposal?.workflow_run_id ?? "-",
                },
              ]}
            />
          </SectionCard>
          <SectionCard title={proposalFraming.historyTitle}>
            <DataTable
              columns={[
                "execution_proposal_id",
                "generated_at",
                "status",
                "approval_status",
                "signal_id",
                "workflow_run_id",
                "order_count",
                "expected_pnl_eur",
              ]}
              rows={formatProposalHistory(proposalHistory.data?.proposals ?? []).slice(0, 8)}
            />
          </SectionCard>
        </div>
      ) : null}

      {activeTab === "risk" ? (
        <div className="space-y-5">
          <AutomationModeLadder escalation={modeEscalation} />
          <ExecutionRiskApprovalPanel
            approvalData={approvalData}
            automationBlockers={automationBlockers}
            automationStatus={automationStatus}
            confidence={confidence}
            freshnessGates={freshnessGates}
            guardrailSummary={guardrailSummary}
            guardrails={guardrails}
            hardBlockers={hardBlockers}
            personaId={personaId}
            refetchExecution={refetchExecution}
            recoveryPlan={recovery}
            remediationItems={remediationQueue}
            selectedAssetId={selectedAssetId}
          />
        </div>
      ) : null}

      {activeTab === "simulation" ? (
        <ExecutionSimulationPanel
          paperFills={formatPaperFills(paperTradeFills)}
          paperHistoryRows={formatPaperTradeHistory(paperTradeHistory.data?.paper_trades ?? [])}
          paperTrade={paperTrade}
          paperTradeRunCount={paperTradeHistory.data?.paper_trades?.length ?? 0}
          personaId={personaId}
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
          submission={submission}
          submissionLifecycle={submissionLifecycle.data}
          submissionSummary={submissionSummary}
        />
      ) : null}

      {activeTab === "settlement" ? (
        <ExecutionSettlementPanel
          personaId={personaId}
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
          assetProfileEvidence={assetDataProfileEvidence}
          settlementMode={settlementMode}
          settlementData={settlementData}
          settlementSummary={settlementSummary}
          varianceDrivers={varianceDrivers}
        />
      ) : null}

      {activeTab === "audit" ? (
        <div className="space-y-5">
          {showTabs ? (
            <>
              <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                <AssetDataProfileSection
                  asset={selectedAsset}
                  title="Selected execution asset profile"
                />
                <EvidenceSourceSection
                  asset={selectedAsset}
                  metadata={executionSourceMetadata}
                  title="Can this asset execute safely?"
                />
              </div>
              <SectionCard
                action={<StatusPill tone="blue">{selectedAsset?.data_mode ?? "mock"} execution proof</StatusPill>}
                title="Asset execution proof"
              >
                <div className="mb-4 grid gap-4 md:grid-cols-3">
                  {backendExecutionKpis.map((kpi) => (
                    <KpiCard
                      accent={kpi.accent}
                      helper={kpi.helper}
                      key={kpi.label}
                      label={kpi.label}
                      value={kpi.value}
                    />
                  ))}
                </div>
                <DataTable
                  columns={["execution_driver", "mock_evidence", "investor_meaning", "production_upgrade"]}
                  rows={visibleExecutionRows}
                />
              </SectionCard>
            </>
          ) : null}
          <ExecutionAuditPanel
            approvalData={approvalData}
            auditRows={auditRows}
            automationEvents={eventRows}
            lifecycleRows={lifecycleRows}
            personaId={personaId}
            personaLayer={persona.layer}
            paperTrade={paperTrade}
            proposal={proposal}
            settlementData={settlementData}
            submissionLifecycle={submissionLifecycle.data}
            submission={submission}
            riskChecks={riskChecks}
            telemetryData={telemetryData}
          />
        </div>
      ) : null}
    </>
  );
}

type ExecutionKpi = {
  accent: "amber" | "blue" | "emerald" | "red" | "slate";
  helper: string;
  label: string;
  value: React.ReactNode;
};

function normalizeProofKpis(rows?: TableRow[]): ExecutionKpi[] {
  return (rows ?? []).map((row) => ({
    accent: normalizeAccent(row.accent),
    helper: String(row.helper ?? ""),
    label: String(row.label ?? "Evidence"),
    value: normalizeKpiValue(row.value),
  }));
}

function normalizeAccent(value: unknown): ExecutionKpi["accent"] {
  if (
    value === "amber" ||
    value === "blue" ||
    value === "emerald" ||
    value === "red" ||
    value === "slate"
  ) {
    return value;
  }

  return "slate";
}

function normalizeKpiValue(value: TableRow[string]): React.ReactNode {
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  if (value === null || value === undefined) {
    return "-";
  }

  return JSON.stringify(value);
}

function getProposalPersonaFraming(personaId: string) {
  const defaults = {
    decisionEyebrow: "Bid proposal decision",
    decisionTitle: "Can the automated bid package advance?",
    historyTitle: "Proposal history",
    limitsTitle: "Position limits",
    nextActionBuilt: "Validate the package with paper trading before live submission.",
    nextActionMissing: "Build a pre-trade proposal from the selected market route.",
    ordersTitle: "Backend proposed market bids",
    packageTitle: "Market-native bid package",
    pipelineTitle: "Order package automation pipeline",
  };

  const frames: Record<string, typeof defaults> = {
    automation_operator: {
      decisionEyebrow: "Automation proposal decision",
      decisionTitle: "Can this proposal move to the next automation gate?",
      historyTitle: "Automation proposal history",
      limitsTitle: "Automation position limits",
      nextActionBuilt: "Run paper validation or clear the next automation gate before escalation.",
      nextActionMissing: "Build the order package from the selected route before automation can progress.",
      ordersTitle: "Automation-ready proposed bids",
      packageTitle: "Automation order package",
      pipelineTitle: "Proposal-to-automation pipeline",
    },
    trading_desk: {
      decisionEyebrow: "Desk proposal decision",
      decisionTitle: "Can the desk use this bid package?",
      historyTitle: "Desk proposal history",
      limitsTitle: "Desk position limits",
      nextActionBuilt: "Review order sizing, then run paper validation before supervised execution.",
      nextActionMissing: "Build the bid package from the selected route and dispatch schedule.",
      ordersTitle: "Desk proposed market bids",
      packageTitle: "Desk bid package",
      pipelineTitle: "Bid package desk pipeline",
    },
    risk_compliance: {
      decisionEyebrow: "Governance proposal decision",
      decisionTitle: "Is this bid package acceptable for risk review?",
      historyTitle: "Proposal governance history",
      limitsTitle: "Risk position limits",
      nextActionBuilt: "Validate risk limits, human gate status, and paper evidence before approval.",
      nextActionMissing: "Build the proposal before risk can review order limits and evidence.",
      ordersTitle: "Governed proposed market bids",
      packageTitle: "Governed bid package",
      pipelineTitle: "Proposal governance pipeline",
    },
    market_operations: {
      decisionEyebrow: "Market operations proposal decision",
      decisionTitle: "Is this order package ready for the selected market route?",
      historyTitle: "Route proposal history",
      limitsTitle: "Route position limits",
      nextActionBuilt: "Check adapter, gate closure, order style, and lifecycle status before validation.",
      nextActionMissing: "Build the route-specific proposal after allocation selects a market adapter.",
      ordersTitle: "Route-specific proposed bids",
      packageTitle: "Market-route bid package",
      pipelineTitle: "Route proposal pipeline",
    },
  };

  return frames[personaId] ?? defaults;
}

function formatProposalHistory(rows: NonNullable<ExecutionProposalHistoryResponse["proposals"]>) {
  return rows.map((row) => ({
    ...row,
    generated_at: formatDateTime(row.generated_at),
  }));
}

function formatPaperTradeHistory(rows: NonNullable<ExecutionPaperTradeHistoryResponse["paper_trades"]>) {
  return rows.map((row) => ({
    ...row,
    generated_at: formatDateTime(row.generated_at),
    paper_pnl_eur: formatCurrency(row.paper_pnl_eur),
    paper_vs_expected_delta_eur: formatCurrency(row.paper_vs_expected_delta_eur),
  }));
}

function formatPaperFills(
  rows: NonNullable<NonNullable<ExecutionPaperTradeResponse["paper_trade"]>["fills"]>,
) {
  return rows.map((row) => ({
    ...row,
    delivery_time: formatDateTime(row.delivery_time),
    fill_price_eur_mwh: formatNumber(row.fill_price_eur_mwh, 2),
    filled_volume_mwh: formatNumber(row.filled_volume_mwh, 4),
    notional_eur: formatCurrency(row.notional_eur),
  }));
}

function RouteCertificationPanel({
  routes,
  status,
}: {
  routes: RouteAutomationCertification[];
  status?: string;
}) {
  const rows = routes.slice(0, 6).map((route) => ({
    route: route.adapter_id,
    stage: route.route_certification_stage?.replaceAll("_", " ") ?? "-",
    score: `${formatNumber(route.route_certification_score, 1)}/100`,
    latest_drill: route.latest_route_drill_status ?? "-",
    paper: route.certified_for_paper ? "yes" : "no",
    supervised: route.certified_for_supervised ? "yes" : "no",
    next_action: route.route_certification_next_action ?? "-",
  }));

  const leader = routes
    .slice()
    .sort(
      (left, right) =>
        Number(right.route_certification_score ?? 0) -
        Number(left.route_certification_score ?? 0),
    )[0];

  return (
    <SectionCard
      action={
        <StatusPill tone={routeCertificationTone(status)}>
          {status?.replaceAll("_", " ") ?? "not evaluated"}
        </StatusPill>
      }
      className="mb-6"
      title="Route certification"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Best route
          </div>
          <div className="mt-2 text-sm font-semibold text-slate-100">
            {leader?.adapter_id ?? "-"}
          </div>
          <div className="mt-1 text-xs leading-5 text-slate-400">
            {leader?.route_certification_stage?.replaceAll("_", " ") ?? "No route certified"}
          </div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Certification score
          </div>
          <div className="mt-2 text-sm font-semibold text-slate-100">
            {formatNumber(leader?.route_certification_score, 1)}/100
          </div>
          <div className="mt-1 text-xs leading-5 text-slate-400">
            Latest drill {leader?.latest_route_drill_status ?? "-"}
          </div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Next certification action
          </div>
          <div className="mt-2 text-xs leading-5 text-slate-300">
            {leader?.route_certification_next_action ?? "Evaluate route certification."}
          </div>
        </div>
      </div>
      <DataTable
        columns={["route", "stage", "score", "latest_drill", "paper", "supervised", "next_action"]}
        rows={rows}
      />
    </SectionCard>
  );
}

function GoLiveReadinessPanel({
  data,
  refetchExecution,
}: {
  data?: LiveTradingReadinessResponse;
  refetchExecution: () => Promise<unknown>;
}) {
  const summary = data?.summary ?? {};
  const nextAction = data?.next_best_action;
  const runbookSteps = data?.runbook?.steps ?? [];
  const unlockQueue = (data?.route_readiness ?? [])
    .map((row) => row.unlock_action)
    .filter((action): action is NonNullable<typeof action> => Boolean(action))
    .slice(0, 4);
  const routeRows = (data?.route_readiness ?? []).slice(0, 6).map((row) => ({
    market_name: row.market_name,
    mode: row.mode?.replaceAll("_", " "),
    readiness_score: formatNumber(row.readiness_score, 1),
    expected_revenue_eur: formatCurrency(row.expected_revenue_eur),
    gate: row.market_gate_status,
    connector: row.connector_tier,
    blockers: row.blocker_count ?? 0,
    unlock: row.unlock_label ?? row.unlock_action?.label,
    owner: row.unlock_owner ?? row.unlock_action?.owner,
    severity: row.unlock_severity ?? row.unlock_action?.severity,
    auto_safe: row.unlock_action?.auto_resolvable ? "yes" : "manual",
  }));
  const runbookRows = runbookSteps.map((step) => ({
    step: step.label,
    status: step.status,
    next_action: step.next_action,
  }));

  return (
    <SectionCard
      action={
        <div className="flex flex-wrap gap-2">
          {nextAction?.auto_resolvable && nextAction.resolution_endpoint ? (
            <ActionButton
              endpoint={nextAction.resolution_endpoint}
              label="Run next unlock"
              refetch={refetchExecution}
              variant="primary"
            />
          ) : null}
          <StatusPill tone={goLiveTone(data?.go_live_status)}>
            {data?.go_live_status?.replaceAll("_", " ") ?? "Not evaluated"}
          </StatusPill>
        </div>
      }
      className="mb-6"
      title="Go-live readiness"
    >
      <div className="mb-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={goLiveTone(data?.go_live_status)}
          helper={data?.mode_recommendation?.replaceAll("_", " ") ?? "No mode recommendation"}
          label="Live readiness score"
          value={`${formatNumber(data?.live_trading_readiness_score, 1)}/100`}
        />
        <KpiCard
          accent={Number(summary.live_ready_route_count ?? 0) > 0 ? "emerald" : "amber"}
          helper={`${summary.supervised_ready_route_count ?? 0} supervised / ${summary.paper_ready_route_count ?? 0} paper`}
          label="Live-ready routes"
          value={summary.live_ready_route_count ?? 0}
        />
        <KpiCard
          accent={Number(summary.blocked_route_count ?? 0) > 0 ? "red" : "emerald"}
          helper={`${summary.route_count ?? 0} German routes evaluated`}
          label="Blocked routes"
          value={summary.blocked_route_count ?? 0}
        />
        <KpiCard
          accent={Number(summary.handshake_ready_count ?? 0) > 0 ? "emerald" : "amber"}
          helper={`${summary.handshake_ready_count ?? 0}/${summary.handshake_target_count ?? 0} dry-run ready`}
          label="Live handshake"
          value={summary.best_route_mode?.replaceAll("_", " ") ?? "-"}
        />
      </div>

      <div className="mb-5 rounded-lg border border-slate-800 bg-slate-900/45 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
          Next best action
        </div>
        <div className="mt-2 text-sm font-semibold text-slate-100">
          {nextAction?.label ?? "No next action evaluated."}
        </div>
        <div className="mt-1 text-xs leading-5 text-slate-400">
          Owner: {nextAction?.owner ?? "automation_control"} / Best route: {summary.best_route ?? "-"}
        </div>
      </div>

      <div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {unlockQueue.map((action, index) => (
          <div
            className="min-h-40 rounded-lg border border-slate-800 bg-slate-900/45 p-4"
            key={`${action.adapter_id ?? "route"}-${action.category ?? index}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-slate-100">
                  {action.label ?? "Review unlock"}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {String(action.category ?? "route").replaceAll("_", " ")}
                </div>
              </div>
              <StatusPill tone={unlockSeverityTone(action.severity)}>
                {String(action.severity ?? "review")}
              </StatusPill>
            </div>
            <div className="mt-4 text-xs leading-5 text-slate-400">
              {String(action.message ?? "Review this route before escalation.")}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {action.auto_resolvable && action.resolution_endpoint ? (
                <ActionButton
                  endpoint={String(action.resolution_endpoint)}
                  label="Run"
                  refetch={refetchExecution}
                  variant="primary"
                />
              ) : null}
              <StatusPill tone={action.auto_resolvable ? "emerald" : "blue"}>
                {action.auto_resolvable ? "auto-safe" : String(action.owner ?? "manual")}
              </StatusPill>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)]">
        <div>
          <div className="mb-3 text-sm font-semibold text-slate-100">
            Route-level readiness
          </div>
          <DataTable
            columns={["market_name", "mode", "readiness_score", "expected_revenue_eur", "gate", "connector", "blockers", "unlock", "owner", "severity", "auto_safe"]}
            rows={routeRows}
          />
        </div>
        <div>
          <div className="mb-3 text-sm font-semibold text-slate-100">
            Go-live runbook
          </div>
          <DataTable columns={["step", "status", "next_action"]} rows={runbookRows} />
        </div>
      </div>
    </SectionCard>
  );
}

function StrategyIntentPanel({ intent }: { intent?: StrategyIntentResponse }) {
  const targetMarkets = intent?.target_markets ?? [];
  const blockers = intent?.blocking_evidence ?? [];
  const reasons = intent?.why ?? [];
  const nextAction = intent?.recommended_next_action;

  return (
    <SectionCard
      action={
        <StatusPill tone={intentTone(intent?.strategy_mode)}>
          {intent?.confidence?.band ?? "Intent"}
        </StatusPill>
      }
      className="mb-6"
      title="Automated strategy intent"
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)]">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Strategy
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {intent?.strategy_mode?.replaceAll("_", " ") ?? "-"}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              Bias: {intent?.dispatch_bias?.replaceAll("_", " ") ?? "-"}
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Confidence
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {formatNumber(intent?.confidence?.score, 1)}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              {intent?.confidence?.automation_eligible ? "Eligible for automation" : "Keep gated"}
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4 sm:col-span-2">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Recommended next action
            </div>
            <div className="mt-2 text-sm font-semibold text-slate-100">
              {nextAction?.label ?? "-"}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              {nextAction?.message ?? "No strategy action evaluated."}
            </div>
          </div>
        </div>

        <div className="grid gap-4">
          <DataTable
            columns={[
              "rank",
              "role",
              "market_name",
              "market_segment",
              "allocated_power_mw",
              "expected_revenue_eur",
              "status",
            ]}
            rows={targetMarkets.slice(0, 8)}
          />
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
              <div className="mb-3 text-sm font-semibold text-slate-100">
                Strategy reasons
              </div>
              <div className="space-y-2">
                {reasons.length ? reasons.map((reason) => (
                  <div className="text-xs leading-5 text-slate-400" key={reason}>
                    {reason}
                  </div>
                )) : (
                  <div className="text-xs text-slate-500">
                    No strategy reasons available yet.
                  </div>
                )}
              </div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="text-sm font-semibold text-slate-100">
                  Blocking evidence
                </div>
                <StatusPill tone={blockers.length ? "amber" : "emerald"}>
                  {blockers.length}
                </StatusPill>
              </div>
              <div className="space-y-2">
                {blockers.slice(0, 4).map((blocker) => (
                  <div
                    className="rounded-md border border-slate-800 bg-slate-950/60 p-3 text-xs leading-5 text-slate-400"
                    key={`${blocker.source}-${blocker.message}`}
                  >
                    <span className="font-semibold text-slate-200">
                      {String(blocker.source ?? "blocker")}
                    </span>
                    : {String(blocker.required_action ?? blocker.message ?? "-")}
                  </div>
                ))}
                {!blockers.length ? (
                  <div className="text-xs text-slate-500">
                    No strategy blockers returned by the backend.
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

function AutomationModeLadder({
  escalation,
}: {
  escalation?: AutomationModeEscalation;
}) {
  const ladder = escalation?.ladder ?? [];
  const blockers = escalation?.escalation_blockers ?? [];

  if (!ladder.length) {
    return null;
  }

  return (
    <SectionCard
      action={
        <StatusPill tone={escalation?.can_escalate ? "emerald" : "amber"}>
          {escalation?.can_escalate ? "Can escalate" : "Gated"}
        </StatusPill>
      }
      className="mb-6"
      title="Automation mode ladder"
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {ladder.map((step) => (
          <div
            className="min-h-40 rounded-lg border border-slate-800 bg-slate-900/45 p-4"
            key={step.mode}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-slate-100">
                  {step.label}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {step.mode?.replaceAll("_", " ")}
                </div>
              </div>
              <StatusPill tone={ladderTone(step.status)}>
                {step.status ?? "-"}
              </StatusPill>
            </div>
            <div className="mt-4 text-xs leading-5 text-slate-400">
              {step.description}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,0.7fr)_minmax(0,1.3fr)]">
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Next eligible mode
          </div>
          <div className="mt-2 text-lg font-semibold text-white">
            {escalation?.next_eligible_mode?.replaceAll("_", " ") ?? "Max mode reached"}
          </div>
          <div className="mt-1 text-xs leading-5 text-slate-400">
            Current mode: {escalation?.current_mode?.replaceAll("_", " ") ?? "-"}
          </div>
        </div>
        <DataTable
          columns={["label", "status", "message"]}
          rows={blockers.length ? blockers : escalation?.required_evidence ?? []}
        />
      </div>
    </SectionCard>
  );
}

function goLiveTone(value: unknown) {
  if (value === "go_live_ready" || value === "supervised_ready") {
    return "emerald";
  }

  if (value === "paper_ready" || value === "advisory_only") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function unlockSeverityTone(value: unknown) {
  if (value === "critical" || value === "high") {
    return "red";
  }

  if (value === "medium") {
    return "amber";
  }

  if (value === "low") {
    return "emerald";
  }

  return "slate";
}

function ladderTone(value: unknown) {
  if (value === "passed" || value === "current") {
    return "emerald";
  }

  if (value === "next") {
    return "blue";
  }

  if (value === "locked") {
    return "slate";
  }

  return "amber";
}

function sandboxCertificationTone(value: unknown) {
  if (value === "live_certified_route_available" || value === "supervised_live_certified_route_available") {
    return "emerald";
  }

  if (value === "paper_certified_routes_available") {
    return "blue";
  }

  if (value === "sandbox_blocked") {
    return "red";
  }

  return "slate";
}

function officialApiTone(value: unknown) {
  if (value === "official_api_compliant" || value === "compliant") {
    return "emerald";
  }

  if (value === "partial_official_api_compliance") {
    return "amber";
  }

  if (value === "official_api_blocked" || value === "blocked") {
    return "red";
  }

  return "slate";
}

function routeCertificationTone(value: unknown) {
  if (
    value === "certified_for_live" ||
    value === "live_certified_route_available" ||
    value === "certified_for_supervised" ||
    value === "supervised_certified_route_available"
  ) {
    return "emerald";
  }

  if (
    value === "certified_for_paper" ||
    value === "paper_certified_route_available" ||
    value === "routes_ready_for_drill" ||
    value === "ready_for_drill"
  ) {
    return "blue";
  }

  if (value === "route_drill_failed" || value === "drill_failed") {
    return "red";
  }

  if (value === "routes_not_configured" || value === "not_configured") {
    return "amber";
  }

  return "slate";
}

function supervisedLiveGateTone(value: unknown) {
  if (value === "supervised_live_candidate_available") {
    return "emerald";
  }

  if (value === "paper_ready_live_blocked") {
    return "blue";
  }

  if (value === "supervised_live_blocked") {
    return "red";
  }

  return "slate";
}

function handshakeTone(value: unknown) {
  if (value === "handshake_ready") {
    return "emerald";
  }

  if (value === "partial_handshake_ready") {
    return "blue";
  }

  if (value === "handshake_blocked" || value === "handshake_disabled") {
    return "amber";
  }

  return "slate";
}

function bidPackageTone(value: unknown) {
  if (value === "draft_ready" || value === "passed") {
    return "emerald";
  }

  if (value === "draft_blocked" || value === "blocked") {
    return "red";
  }

  if (value === "review") {
    return "amber";
  }

  return "slate";
}

function intentTone(value: unknown) {
  if (value === "arbitrage" || value === "hybrid_stack" || value === "ancillary_priority") {
    return "emerald";
  }

  if (value === "data_recovery") {
    return "amber";
  }

  if (value === "risk_off") {
    return "red";
  }

  return "slate";
}
