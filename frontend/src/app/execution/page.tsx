"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { ErrorState } from "@/components/error-state";
import {
  ExecutionAuditPanel,
  ExecutionOverviewPanel,
  ExecutionRiskApprovalPanel,
  ExecutionSettlementPanel,
  ExecutionSimulationPanel,
} from "@/components/execution/execution-workspace-panels";
import { MarketAllocationPanel } from "@/components/execution/market-allocation-panel";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type {
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
} from "@/types/api";

const executionTabs = [
  {
    id: "overview",
    label: "Overview",
    helper: "Live trading readiness, operator actions, and current execution state.",
  },
  {
    id: "allocation",
    label: "Market Allocation",
    helper: "Ranked German market routes, capacity allocation, and excluded-market reasons.",
  },
  {
    id: "proposals",
    label: "Proposals",
    helper: "Pre-trade bid packets, position limits, and proposal history.",
  },
  {
    id: "risk",
    label: "Risk & Approval",
    helper: "Guardrails, forecast confidence, approval policy, and blockers.",
  },
  {
    id: "simulation",
    label: "Paper Market",
    helper: "Paper fills, paper PnL, and demo market submission status.",
  },
  {
    id: "settlement",
    label: "Settlement",
    helper: "Reconciliation, variance drivers, and realized economics.",
  },
  {
    id: "audit",
    label: "Audit",
    helper: "Backend checks, lifecycle steps, and execution event trail.",
  },
] as const;

export type ExecutionTabId = (typeof executionTabs)[number]["id"];

export default function ExecutionPage({
  description = "Operate supervised battery trading from proposal creation through approval, paper market validation, submission evidence, and settlement reconciliation.",
  eyebrow = "Trading control plane",
  initialTab = "overview",
  showTabs = true,
  title = "Execution",
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
  const paperTradeSummary = paperTrade?.summary ?? {};
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

  const refetchExecution = () =>
    Promise.all([
      latestProposal.refetch(),
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

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <KpiCard
          accent={proposal?.status === "draft" ? "emerald" : "amber"}
          label="Proposal status"
          value={proposal?.status ?? "-"}
          helper={
            proposal?.approval_status ??
            (signal.data?.status === "ok"
              ? "Signal ready for proposal"
              : "No approval state")
          }
        />
        <KpiCard
          accent={bids.length ? "blue" : "slate"}
          label="Draft bids"
          value={bids.length}
          helper="Generated by backend pre-trade engine"
        />
        <KpiCard
          accent={expectedPnl >= 0 ? "emerald" : "red"}
          label="Expected PnL"
          value={formatCurrency(expectedPnl)}
          helper={`${formatNumber(profitPerMwDay, 2)} EUR/MW-day`}
        />
        <KpiCard
          accent="blue"
          label="Asset"
          value={selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId}
          helper={proposal?.market ?? selectedAsset?.market ?? "DE-LU day-ahead"}
        />
        <KpiCard
          accent={paperTrade ? "emerald" : "slate"}
          label="Paper PnL"
          value={paperTrade ? formatCurrency(paperTradeSummary.paper_pnl_eur) : "-"}
          helper={
            paperTrade
              ? `${paperTradeSummary.filled_order_count ?? 0} simulated fill(s)`
              : "Run paper trade after a proposal"
          }
        />
        <KpiCard
          accent={automationTone(automationStatus)}
          label="Automation"
          value={automationStatus ?? "-"}
          helper={`${guardrailSummary.blocked ?? 0} blocked / ${guardrailSummary.review ?? 0} review`}
        />
      </div>

      {showTabs ? (
        <WorkspaceTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={executionTabs}
        />
      ) : null}

      {activeTab === "overview" ? (
        <ExecutionOverviewPanel
          approvalData={approvalData}
          automationStatus={automationStatus}
          bids={bids}
          epexDayAheadPreview={epexDayAheadPreview.data?.preview}
          epexIntradayAuctionPreview={epexIntradayAuctionPreview.data?.preview}
          epexIntradayContinuousPreview={epexIntradayContinuousPreview.data?.preview}
          hardBlockers={hardBlockers}
          marketAdapterStatus={marketAdapterStatus.data}
          paperTrade={paperTrade}
          proposal={proposal}
          readiness={readiness.data}
          refetchExecution={refetchExecution}
          regelleistungAfrrPreview={regelleistungAfrrPreview.data?.preview}
          regelleistungFcrPreview={regelleistungFcrPreview.data?.preview}
          regelleistungMfrrPreview={regelleistungMfrrPreview.data?.preview}
          selectedAssetId={selectedAssetId}
          submission={submission}
          telemetryData={telemetryData}
        />
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
                "risk_adjusted_volume_mw",
                "risk_adjusted_limit_price_eur_mwh",
                "forecast_confidence_score",
                "automation_eligibility",
                "approval_status",
                "submission_status",
                "lifecycle_status",
              ]}
              rows={bids}
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
              rows={formatProposalHistory(proposalHistory.data?.proposals ?? [])}
            />
          </SectionCard>
        </div>
      ) : null}

      {activeTab === "risk" ? (
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

function automationTone(value: unknown) {
  if (value === "supervised_live_candidate") {
    return "emerald";
  }

  if (value === "human_approval_required") {
    return "blue";
  }

  if (value === "paper_only") {
    return "amber";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}
