"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ErrorState } from "@/components/error-state";
import {
  ExecutionAuditPanel,
  ExecutionOverviewPanel,
  ExecutionRiskApprovalPanel,
  ExecutionSettlementPanel,
  ExecutionSimulationPanel,
} from "@/components/execution/execution-workspace-panels";
import { MarketAllocationPanel } from "@/components/execution/market-allocation-panel";
import {
  buildTradingAutomationPipelineStages,
  TradingAutomationPipeline,
} from "@/components/execution/trading-automation-pipeline";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
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
  const [activeTab, setActiveTab] = useState<ExecutionTabId>(initialTab);

  const latestProposal = useQuery({
    queryFn: () =>
      apiGet<ExecutionProposalResponse>(
        `/assets/${selectedAssetId}/execution/proposal/latest`,
      ),
    queryKey: ["execution-proposal-latest", selectedAssetId],
  });

  const automationControl = useQuery({
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["execution-automation-control", selectedAssetId],
  });

  const liveTradingReadiness = useQuery({
    queryFn: () =>
      apiGet<LiveTradingReadinessResponse>(
        `/assets/${selectedAssetId}/execution/live-trading-readiness?country=Germany`,
      ),
    queryKey: ["execution-live-trading-readiness", selectedAssetId],
  });

  const automationEvents = useQuery({
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
    queryFn: () =>
      apiGet<ExecutionProposalHistoryResponse>(
        `/assets/${selectedAssetId}/execution/proposals?limit=10`,
      ),
    queryKey: ["execution-proposal-history", selectedAssetId],
  });

  const latestPaperTrade = useQuery({
    queryFn: () =>
      apiGet<ExecutionPaperTradeResponse>(
        `/assets/${selectedAssetId}/execution/paper-trade/latest`,
      ),
    queryKey: ["execution-paper-trade-latest", selectedAssetId],
  });

  const paperTradeHistory = useQuery({
    queryFn: () =>
      apiGet<ExecutionPaperTradeHistoryResponse>(
        `/assets/${selectedAssetId}/execution/paper-trades?limit=10`,
      ),
    queryKey: ["execution-paper-trade-history", selectedAssetId],
  });

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["execution-signal-latest", selectedAssetId],
  });

  const settlement = useQuery({
    queryFn: () =>
      apiGet<SettlementResponse>(
        `/assets/${selectedAssetId}/settlement/latest`,
      ),
    queryKey: ["execution-settlement-latest", selectedAssetId],
  });

  const forecastConfidence = useQuery({
    queryFn: () =>
      apiGet<ForecastConfidenceResponse>(
        `/assets/${selectedAssetId}/forecast-confidence`,
      ),
    queryKey: ["execution-forecast-confidence", selectedAssetId],
  });

  const automationGuardrails = useQuery({
    queryFn: () =>
      apiGet<AutomationGuardrailsResponse>(
        `/assets/${selectedAssetId}/execution/automation-guardrails`,
      ),
    queryKey: ["execution-automation-guardrails", selectedAssetId],
  });

  const telemetry = useQuery({
    queryFn: () =>
      apiGet<AssetTelemetryResponse>(
        `/assets/${selectedAssetId}/telemetry/latest`,
      ),
    queryKey: ["execution-telemetry-latest", selectedAssetId],
  });

  const marketSubmission = useQuery({
    queryFn: () =>
      apiGet<MarketSubmissionResponse>(
        `/assets/${selectedAssetId}/execution/submissions/latest`,
      ),
    queryKey: ["execution-market-submission-latest", selectedAssetId],
  });

  const submissionLifecycle = useQuery({
    queryFn: () =>
      apiGet<MarketSubmissionLifecycleResponse>(
        `/assets/${selectedAssetId}/execution/submission-lifecycle`,
      ),
    queryKey: ["execution-submission-lifecycle", selectedAssetId],
  });

  const recoveryPlan = useQuery({
    queryFn: () =>
      apiGet<ExecutionRecoveryPlanResponse>(
        `/assets/${selectedAssetId}/execution/recovery-plan`,
      ),
    queryKey: ["execution-recovery-plan", selectedAssetId],
  });

  const approval = useQuery({
    queryFn: () =>
      apiGet<ExecutionApprovalResponse>(
        `/assets/${selectedAssetId}/execution/approval/latest`,
      ),
    queryKey: ["execution-approval-latest", selectedAssetId],
  });

  const readiness = useQuery({
    queryFn: () =>
      apiGet<ExecutionReadinessResponse>(
        `/assets/${selectedAssetId}/execution/readiness`,
      ),
    queryKey: ["execution-readiness", selectedAssetId],
  });

  const marketAdapterStatus = useQuery({
    queryFn: () =>
      apiGet<AssetMarketAdapterStatusResponse>(
        `/assets/${selectedAssetId}/execution/market-adapter/status`,
      ),
    queryKey: ["execution-market-adapter-status", selectedAssetId],
  });

  const marketConnectorReadiness = useQuery({
    queryFn: () =>
      apiGet<MarketConnectorReadinessResponse>(
        `/execution/market-connectors/readiness?country=Germany&asset_id=${selectedAssetId}`,
      ),
    queryKey: ["execution-market-connectors-readiness", selectedAssetId],
  });

  const multiMarketAllocation = useQuery({
    queryFn: () =>
      apiGet<MultiMarketAllocationResponse>(
        `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      ),
    queryKey: ["execution-multi-market-allocation", selectedAssetId],
  });

  const epexDayAheadPreview = useQuery({
    queryFn: () =>
      apiGet<EpexDayAheadPreviewResponse>(
        `/assets/${selectedAssetId}/execution/epex/day-ahead/preview`,
      ),
    queryKey: ["execution-epex-day-ahead-preview", selectedAssetId],
  });

  const epexIntradayAuctionPreview = useQuery({
    queryFn: () =>
      apiGet<EpexIntradayAuctionPreviewResponse>(
        `/assets/${selectedAssetId}/execution/epex/intraday-auction/preview`,
      ),
    queryKey: ["execution-epex-intraday-auction-preview", selectedAssetId],
  });

  const epexIntradayContinuousPreview = useQuery({
    queryFn: () =>
      apiGet<EpexIntradayContinuousPreviewResponse>(
        `/assets/${selectedAssetId}/execution/epex/intraday-continuous/preview`,
      ),
    queryKey: ["execution-epex-intraday-continuous-preview", selectedAssetId],
  });

  const regelleistungFcrPreview = useQuery({
    queryFn: () =>
      apiGet<RegelleistungFcrPreviewResponse>(
        `/assets/${selectedAssetId}/execution/regelleistung/fcr/preview`,
      ),
    queryKey: ["execution-regelleistung-fcr-preview", selectedAssetId],
  });

  const regelleistungAfrrPreview = useQuery({
    queryFn: () =>
      apiGet<RegelleistungAfrrPreviewResponse>(
        `/assets/${selectedAssetId}/execution/regelleistung/afrr/preview`,
      ),
    queryKey: ["execution-regelleistung-afrr-preview", selectedAssetId],
  });

  const regelleistungMfrrPreview = useQuery({
    queryFn: () =>
      apiGet<RegelleistungMfrrPreviewResponse>(
        `/assets/${selectedAssetId}/execution/regelleistung/mfrr/preview`,
      ),
    queryKey: ["execution-regelleistung-mfrr-preview", selectedAssetId],
  });

  const proposal = latestProposal.data?.proposal;
  const signalSummary = signal.data?.data?.summary ?? {};
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
  const paperTrade = latestPaperTrade.data?.paper_trade;
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
  const automationStatus = automationGuardrails.data?.automation_status;
  const guardrailSummary = automationGuardrails.data?.summary ?? {};
  const guardrails = automationGuardrails.data?.guardrails ?? [];
  const telemetryData = telemetry.data?.telemetry;
  const submission = marketSubmission.data?.submission;
  const submissionSummary = submission?.summary ?? {};
  const approvalData = approval.data?.approval;
  const marketAllocation = multiMarketAllocation.data;
  const connectorReadiness = marketConnectorReadiness.data;
  const connectorSummary = connectorReadiness?.summary ?? {};
  const routeCertifications = connectorReadiness?.route_certifications ?? [];
  const control = automationControl.data;
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
  const pipelineStages = useMemo(
    () =>
      buildTradingAutomationPipelineStages({
        allocationReady: Boolean(primaryMarket),
        approvalStatus: String(humanGate.status ?? approvalData?.status ?? ""),
        eligibilityReady:
          readiness.data?.readiness_status !== "blocked" &&
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
              Number(readiness.data?.summary?.blocked ?? 0) +
              Number(automationGuardrails.data?.summary?.blocked ?? 0),
            evidence: readiness.data?.readiness_status ?? "not evaluated",
            nextAction:
              readiness.data?.recommended_actions?.[0] ??
              automationGuardrails.data?.recommended_actions?.[0],
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
      automationGuardrails.data?.recommended_actions,
      automationGuardrails.data?.summary?.blocked,
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
      readiness.data?.readiness_status,
      readiness.data?.recommended_actions,
      readiness.data?.summary?.blocked,
      settlementData,
      settlementSummary.realized_pnl_eur,
      signalSummary.signal,
      submission,
      submissionSummary.submitted_bid_count,
      summary.expected_pnl_eur,
      varianceDrivers.length,
    ],
  );

  const refetchExecution = () =>
    Promise.all([
      latestProposal.refetch(),
      automationControl.refetch(),
      liveTradingReadiness.refetch(),
      automationEvents.refetch(),
      strategyIntent.refetch(),
      proposalHistory.refetch(),
      latestPaperTrade.refetch(),
      paperTradeHistory.refetch(),
      settlement.refetch(),
      forecastConfidence.refetch(),
      automationGuardrails.refetch(),
      telemetry.refetch(),
      marketSubmission.refetch(),
      submissionLifecycle.refetch(),
      recoveryPlan.refetch(),
      approval.refetch(),
      readiness.refetch(),
      marketAdapterStatus.refetch(),
      marketConnectorReadiness.refetch(),
      multiMarketAllocation.refetch(),
      epexDayAheadPreview.refetch(),
      epexIntradayAuctionPreview.refetch(),
      epexIntradayContinuousPreview.refetch(),
      regelleistungFcrPreview.refetch(),
      regelleistungAfrrPreview.refetch(),
      regelleistungMfrrPreview.refetch(),
    ]);

  return (
    <>
      <PageHeading
        description={description}
        eyebrow={eyebrow}
        title={title}
      />

      {latestProposal.data?.status === "not_found" ? (
        <div className="mb-6">
          <ErrorState message="No backend execution proposal exists yet. Build a pre-trade proposal after generating a signal or audited workflow." />
        </div>
      ) : null}

      {showTabs ? (
        <>
          <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
            <KpiCard
              accent={controlModeTone(control?.automation_mode)}
              label="Automation mode"
              value={control?.automation_mode ?? automationStatus ?? "-"}
              helper={control?.live_trading_allowed ? "Limited live auto allowed" : "Live auto gated"}
            />
            <KpiCard
              accent={actionTone(nextAutomationAction.action)}
              label="Next auto action"
              value={nextAutomationAction.label ?? "-"}
              helper={nextAutomationAction.owner ?? "Automation control"}
            />
            <KpiCard
              accent={expectedPnl >= 0 ? "emerald" : "red"}
              label="Expected PnL"
              value={formatCurrency(expectedPnl)}
              helper={`${formatNumber(profitPerMwDay, 2)} EUR/MW-day`}
            />
            <KpiCard
              accent="blue"
              label="Market route"
              value={primaryMarket?.market_name ?? proposal?.market ?? "-"}
              helper={primaryMarket?.adapter_id ?? selectedAsset?.market ?? "No route selected"}
            />
            <KpiCard
              accent={humanGateTone(humanGate.status)}
              label="Human gate"
              value={String(humanGate.status ?? "-")}
              helper={humanGate.required ? "Required by automation policy" : "Not required"}
            />
            <KpiCard
              accent={controlBlockers.length ? "red" : "emerald"}
              label="Blockers"
              value={controlBlockers.length}
              helper={`${guardrailSummary.blocked ?? 0} guardrail / ${guardrailSummary.review ?? 0} review`}
            />
          </div>

          <DecisionBrief
            blockers={controlBlockers
              .map((blocker) => String(blocker.message ?? blocker.key ?? "Automation blocker"))
              .slice(0, 4)}
            className="mb-6"
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
            ]}
            eyebrow="Mission control"
            nextAction={
              nextAutomationAction.message ??
              intent?.recommended_next_action?.message ??
              "No automated action has been evaluated yet."
            }
            title="Autonomous trading mission control"
            tone={controlBlockers.length ? "amber" : "emerald"}
          />

          <SectionCard
            action={
              <div className="flex flex-wrap gap-2">
                <ActionButton
                  endpoint={`/assets/${selectedAssetId}/execution/remediation/run-next`}
                  label="Run next remediation"
                  refetch={refetchExecution}
                  variant="primary"
                />
                <ActionButton
                  endpoint={`/assets/${selectedAssetId}/execution/orchestrator/run`}
                  label="Run next auto action"
                  refetch={refetchExecution}
                />
              </div>
            }
            className="mb-6"
            title="Automation engine"
          >
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Next action
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-100">
                  {nextAutomationAction.label ?? "-"}
                </div>
                <div className="mt-1 text-xs leading-5 text-slate-400">
                  {nextAutomationAction.message ?? "No automation action evaluated."}
                </div>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Mode permissions
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <StatusPill tone={control?.paper_trading_allowed ? "emerald" : "slate"}>
                    Paper
                  </StatusPill>
                  <StatusPill tone={control?.supervised_trading_allowed ? "emerald" : "slate"}>
                    Supervised
                  </StatusPill>
                  <StatusPill tone={control?.live_trading_allowed ? "emerald" : "red"}>
                    Live
                  </StatusPill>
                </div>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Evidence
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-100">
                  Proposal {control?.evidence?.execution_proposal_id ?? "-"} / Paper {control?.evidence?.paper_trade_id ?? "-"}
                </div>
                <div className="mt-1 text-xs leading-5 text-slate-400">
                  Human gate {String(humanGate.status ?? "-")} / Submission {control?.evidence?.market_submission_id ?? "-"}
                </div>
              </div>
            </div>
          </SectionCard>
        </>
      ) : null}

      {showTabs ? (
        <WorkspaceTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={executionTabs}
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
            proposal={proposal}
            readiness={readiness.data}
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
            ]}
            eyebrow="Bid proposal decision"
            nextAction={
              proposal
                ? nextAutomationAction.message ?? "Validate the package with paper trading before live submission."
                : "Build a pre-trade proposal from the selected market route."
            }
            title="Can the automated bid package advance?"
            tone={automationBlockers.length || hardBlockers.length ? "amber" : proposal ? "emerald" : "blue"}
          />
          <TradingAutomationPipeline
            currentStageId="proposal"
            stages={pipelineStages}
            title="Order package automation pipeline"
          />
          <SectionCard
            action={<StatusPill tone={bidPackageTone(bidPackage?.package_status)}>{bidPackage?.package_status ?? "not built"}</StatusPill>}
            title="Market-native bid package"
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
            title="Backend proposed market bids"
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

          <SectionCard title="Position limits">
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
          <SectionCard title="Proposal history">
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
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
          submission={submission}
          submissionLifecycle={submissionLifecycle.data}
          submissionSummary={submissionSummary}
        />
      ) : null}

      {activeTab === "settlement" ? (
        <ExecutionSettlementPanel
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
          settlementData={settlementData}
          settlementSummary={settlementSummary}
          varianceDrivers={varianceDrivers}
        />
      ) : null}

      {activeTab === "audit" ? (
        <ExecutionAuditPanel
          approvalData={approvalData}
          auditRows={auditRows}
          automationEvents={eventRows}
          lifecycleRows={lifecycleRows}
          paperTrade={paperTrade}
          proposal={proposal}
          settlementData={settlementData}
          submissionLifecycle={submissionLifecycle.data}
          submission={submission}
          riskChecks={riskChecks}
          telemetryData={telemetryData}
        />
      ) : null}
    </>
  );
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

function controlModeTone(value: unknown) {
  if (value === "live_auto_limited" || value === "supervised_auto") {
    return "emerald";
  }

  if (value === "paper_trading") {
    return "blue";
  }

  if (value === "live_auto_blocked") {
    return "red";
  }

  return "slate";
}

function humanGateTone(value: unknown) {
  if (value === "passed" || value === "not_required" || value === "approved") {
    return "emerald";
  }

  if (value === "pending" || value === "required" || value === "requested") {
    return "blue";
  }

  if (value === "blocked" || value === "rejected") {
    return "red";
  }

  return "slate";
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

function actionTone(value: unknown) {
  if (value === "submit_with_limits" || value === "monitor_and_reoptimize") {
    return "emerald";
  }

  if (
    value === "build_proposal" ||
    value === "run_paper_trade" ||
    value === "wait_for_supervised_gate" ||
    value === "clear_review_items"
  ) {
    return "blue";
  }

  if (value === "clear_blockers") {
    return "red";
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
