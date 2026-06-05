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
  AutomationFreshnessGate,
  AutomationModeEscalation,
  AutomationRemediationItem,
  AutomationGuardrailsResponse,
  AssetTelemetryResponse,
  AssetMarketAdapterStatusResponse,
  ExecutionApprovalResponse,
  ExecutionPaperTradeHistoryResponse,
  ExecutionPaperTradeResponse,
  ExecutionProposalHistoryResponse,
  ExecutionProposalResponse,
  ExecutionReadinessResponse,
  EpexDayAheadPreviewResponse,
  EpexIntradayAuctionPreviewResponse,
  EpexIntradayContinuousPreviewResponse,
  ForecastConfidenceResponse,
  LatestSignalResponse,
  MarketSubmissionResponse,
  MultiMarketAllocationResponse,
  RegelleistungAfrrPreviewResponse,
  RegelleistungFcrPreviewResponse,
  RegelleistungMfrrPreviewResponse,
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
  const expectedPnl = Number(
    summary.expected_pnl_eur ?? signalSummary.total_pnl_eur ?? 0,
  );
  const profitPerMwDay =
    summary.profit_per_mw_day ?? signalSummary.profit_per_mw_day;
  const paperTrade = latestPaperTrade.data?.paper_trade;
  const paperTradeFills = paperTrade?.fills ?? [];
  const lifecycleRows = paperTrade?.bid_lifecycle ?? proposal?.bid_lifecycle ?? [];
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
  const control = automationControl.data;
  const eventRows = automationEvents.data?.events ?? [];
  const humanGate = control?.human_gate ?? {};
  const nextAutomationAction = control?.next_automation_action ?? {};
  const controlBlockers = control?.blockers ?? [];
  const freshnessGates = control?.freshness_gates ?? [];
  const modeEscalation = control?.mode_escalation;
  const remediationQueue = control?.remediation_queue ?? [];
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
      approval.refetch(),
      readiness.refetch(),
      marketAdapterStatus.refetch(),
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
                "market_product_id",
                "side",
                "volume_mw",
                "energy_mwh",
                "limit_price_eur_mwh",
                "risk_adjusted_limit_price_eur_mwh",
                "forecast_confidence_score",
                "automation_eligibility",
                "approval_status",
                "submission_status",
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
          <AutomationRemediationQueue
            items={remediationQueue}
            refetchExecution={refetchExecution}
          />
          <FreshnessTrustGates gates={freshnessGates} />
          <ExecutionRiskApprovalPanel
            approvalData={approvalData}
            automationBlockers={automationBlockers}
            automationStatus={automationStatus}
            confidence={confidence}
            guardrailSummary={guardrailSummary}
            guardrails={guardrails}
            hardBlockers={hardBlockers}
            refetchExecution={refetchExecution}
            selectedAssetId={selectedAssetId}
          />
        </div>
      ) : null}

      {activeTab === "simulation" ? (
        <ExecutionSimulationPanel
          paperFills={formatPaperFills(paperTradeFills)}
          paperHistoryRows={formatPaperTradeHistory(paperTradeHistory.data?.paper_trades ?? [])}
          paperTradeRunCount={paperTradeHistory.data?.paper_trades?.length ?? 0}
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
          submission={submission}
          submissionSummary={submissionSummary}
        />
      ) : null}

      {activeTab === "settlement" ? (
        <ExecutionSettlementPanel
          refetchExecution={refetchExecution}
          selectedAssetId={selectedAssetId}
          settlementSummary={settlementSummary}
          varianceDrivers={varianceDrivers}
        />
      ) : null}

      {activeTab === "audit" ? (
        <ExecutionAuditPanel
          auditRows={auditRows}
          automationEvents={eventRows}
          lifecycleRows={lifecycleRows}
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

function AutomationRemediationQueue({
  items,
  refetchExecution,
}: {
  items: AutomationRemediationItem[];
  refetchExecution: () => Promise<unknown>;
}) {
  if (!items.length) {
    return (
      <SectionCard
        action={<StatusPill tone="emerald">Clear</StatusPill>}
        className="mb-6"
        title="Automation remediation queue"
      >
        <div className="rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">
          No remediation items are blocking the automation engine.
        </div>
      </SectionCard>
    );
  }

  const queueRows = items.slice(0, 8).map((item) => ({
    action:
      item.auto_resolvable && item.resolution_endpoint
        ? "auto-fix available"
        : item.evidence_link
          ? "open evidence"
          : "review",
    category: item.category?.replaceAll("_", " ") ?? "remediation",
    required_action: item.required_action ?? item.message ?? "Resolve blocker",
    severity: item.severity ?? "medium",
    source: item.source ?? item.blocker_id,
  }));

  return (
    <SectionCard
      action={<StatusPill tone={items.some((item) => item.severity === "critical") ? "red" : "amber"}>{items.length} item(s)</StatusPill>}
      className="mb-6"
      title="Automation remediation queue"
    >
      <div className="mb-4 flex flex-wrap gap-3">
        {items.find((item) => item.auto_resolvable && item.resolution_endpoint) ? (
          <ActionButton
            endpoint={items.find((item) => item.auto_resolvable && item.resolution_endpoint)?.resolution_endpoint ?? ""}
            label="Fix next automatically"
            refetch={refetchExecution}
            variant="primary"
          />
        ) : null}
      </div>
      <DataTable
        columns={["severity", "category", "source", "action", "required_action"]}
        rows={queueRows}
      />
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

function FreshnessTrustGates({ gates }: { gates: AutomationFreshnessGate[] }) {
  if (!gates.length) {
    return null;
  }

  return (
    <SectionCard
      action={
        <StatusPill
          tone={gates.some((gate) => gate.freshness_status !== "fresh") ? "amber" : "emerald"}
        >
          Freshness & trust
        </StatusPill>
      }
      className="mb-6"
      title="Freshness & trust gates"
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {gates.map((gate) => (
          <div
            className="min-h-44 rounded-lg border border-slate-800 bg-slate-900/45 p-4"
            key={gate.gate_id}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-slate-100">
                  {gate.label}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Blocks {gate.blocks_mode?.replaceAll("_", " ") ?? "automation"}
                </div>
              </div>
              <StatusPill tone={freshnessTone(gate.freshness_status)}>
                {gate.freshness_status ?? "-"}
              </StatusPill>
            </div>
            <div className="mt-4 grid gap-2 text-xs text-slate-300">
              <div className="flex justify-between gap-3">
                <span className="text-slate-500">Age</span>
                <span>{formatFreshnessAge(gate.age_minutes)}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-slate-500">Max age</span>
                <span>{formatFreshnessAge(gate.max_age_minutes)}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-slate-500">Last seen</span>
                <span>{formatDateTime(gate.last_seen_at)}</span>
              </div>
            </div>
            <div className="mt-4 text-xs leading-5 text-slate-400">
              {gate.required_action}
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function freshnessTone(value: unknown) {
  if (value === "fresh") {
    return "emerald";
  }

  if (value === "stale") {
    return "amber";
  }

  if (value === "missing") {
    return "red";
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

function formatFreshnessAge(value: unknown) {
  const minutes = Number(value);

  if (!Number.isFinite(minutes)) {
    return "-";
  }

  if (minutes >= 1440) {
    return `${formatNumber(minutes / 1440, 1)} d`;
  }

  if (minutes >= 60) {
    return `${formatNumber(minutes / 60, 1)} h`;
  }

  return `${formatNumber(minutes, 0)} min`;
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
