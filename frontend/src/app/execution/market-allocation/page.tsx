"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief, type DecisionBriefTone } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  AutomationControlStatusResponse,
  MultiMarketAllocationCandidate,
  MultiMarketAllocationResponse,
  StrategyIntentResponse,
  TableRow,
} from "@/types/api";

export default function ExecutionMarketAllocationPage() {
  const { selectedAssetId } = useAssetContext();

  const allocation = useQuery({
    queryFn: () =>
      apiGet<MultiMarketAllocationResponse>(
        `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      ),
    queryKey: ["market-allocation-allocation", selectedAssetId],
  });

  const automationControl = useQuery({
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["market-allocation-automation-control", selectedAssetId],
  });

  const strategyIntent = useQuery({
    queryFn: () =>
      apiGet<StrategyIntentResponse>(
        `/assets/${selectedAssetId}/execution/strategy-intent`,
      ),
    queryKey: ["market-allocation-strategy-intent", selectedAssetId],
  });

  const summary = allocation.data?.summary ?? {};
  const primary = allocation.data?.primary_market;
  const secondary = allocation.data?.secondary_market;
  const candidateRows = allocation.data?.allocation ?? [];
  const excludedRows = allocation.data?.excluded_markets ?? [];
  const liveRows = candidateRows.filter((row) => row.live_submission === true);
  const paperRows = candidateRows.filter((row) => row.live_submission !== true);
  const decisionBrief = useMemo(
    () =>
      buildAllocationDecisionBrief({
        allocation: allocation.data,
        automationControl: automationControl.data,
        primary,
        secondary,
        strategyIntent: strategyIntent.data,
      }),
    [allocation.data, automationControl.data, primary, secondary, strategyIntent.data],
  );

  const refetchAllocation = () =>
    Promise.all([
      allocation.refetch(),
      automationControl.refetch(),
      strategyIntent.refetch(),
    ]);

  return (
    <>
      <PageHeading
        description="Rank eligible EPEX and regelleistung routes, select primary and secondary execution paths, and feed the bid proposal engine with automation-ready market intent."
        eyebrow="Automated trading"
        title="Market allocation"
      />

      <div className="mb-6">
        <DecisionBrief
          action={<AllocationAction assetId={selectedAssetId} decision={decisionBrief} refetch={refetchAllocation} />}
          blockers={decisionBrief.blockers}
          decision={decisionBrief.decision}
          evidence={decisionBrief.evidence}
          eyebrow="Route allocation decision"
          nextAction={decisionBrief.nextAction}
          tone={decisionBrief.tone}
          title="Where should automation trade now?"
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={allocationTone(allocation.data?.allocation_status)}
          helper="Backend allocator status"
          label="Allocation"
          value={allocation.data?.allocation_status ?? "-"}
        />
        <KpiCard
          accent={primary ? routeTone(primary) : "amber"}
          helper={primary?.market_segment ?? "No primary market selected"}
          label="Primary route"
          value={primary?.market_name ?? "-"}
        />
        <KpiCard
          accent="blue"
          helper={`${formatNumber(summary.total_allocated_power_mw, 2)} MW allocated`}
          label="Expected revenue"
          value={formatCurrency(summary.total_expected_revenue_eur)}
        />
        <KpiCard
          accent={excludedRows.length ? "amber" : "emerald"}
          helper={`${liveRows.length} live / ${paperRows.length} paper or preview`}
          label="Excluded routes"
          value={excludedRows.length}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <RouteDecisionCard label="Primary route" route={primary} />
        <RouteDecisionCard label="Secondary route" route={secondary} />
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={allocationTone(allocation.data?.allocation_status)}>{candidateRows.length}</StatusPill>}
          title="Ranked candidate routes"
        >
          <DataTable
            columns={[
              "rank",
              "market_group",
              "adapter_id",
              "market_name",
              "execution_mode",
              "recommendation_status",
              "allocation_score",
              "allocated_power_mw",
              "expected_revenue_eur",
              "automation_blocking_level",
              "operator_next_action",
            ]}
            rows={formatCandidateRows(candidateRows).slice(0, 8)}
          />
        </SectionCard>

        <SectionCard title="Strategy intent and control gates">
          <div className="space-y-3">
            <AllocationGateRow
              label="Strategy mode"
              tone={strategyTone(strategyIntent.data?.strategy_mode)}
              value={strategyIntent.data?.strategy_mode ?? "-"}
            />
            <AllocationGateRow
              label="Automation mode"
              tone={automationTone(automationControl.data)}
              value={automationControl.data?.automation_status ?? automationControl.data?.automation_mode ?? "-"}
            />
            <AllocationGateRow
              label="Live trading"
              tone={automationControl.data?.live_trading_allowed ? "emerald" : "amber"}
              value={automationControl.data?.live_trading_allowed ? "allowed" : "gated"}
            />
            <AllocationGateRow
              label="Allowed markets"
              tone="blue"
              value={(automationControl.data?.allowed_markets ?? []).length || "-"}
            />
          </div>
          <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/45 p-4 text-sm leading-6 text-slate-300">
            {(strategyIntent.data?.why ?? []).slice(0, 3).join(" ") ||
              "Strategy intent has not returned explanatory evidence yet."}
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={excludedRows.length ? "amber" : "emerald"}>{excludedRows.length}</StatusPill>}
          title="Excluded or blocked routes"
        >
          <DataTable
            columns={[
              "market_group",
              "adapter_id",
              "market_name",
              "automation_blocking_level",
              "blocking_reasons",
              "operator_next_action",
            ]}
            rows={formatExcludedRows(excludedRows).slice(0, 8)}
          />
        </SectionCard>

        <SectionCard title="Allocation workflow links">
          <div className="space-y-3">
            <WorkflowLink href="/market-signals" label="Market Signals" value={String(strategyIntent.data?.dispatch_bias ?? "signal")} />
            <WorkflowLink href="/market-rules" label="Market Rules" value={String(allocation.data?.summary?.readiness_status ?? "-")} />
            <WorkflowLink href="/execution/market-connectors" label="Market Access & Data" value={String(automationControl.data?.connector_status ?? "-")} />
            <WorkflowLink href="/execution/proposals" label="Bid Proposals" value={primary ? "route selected" : "waiting"} />
            <WorkflowLink href="/execution/orchestrator" label="Trading Orchestrator" value={String(automationControl.data?.next_automation_action?.label ?? "-")} />
          </div>
        </SectionCard>
      </div>
    </>
  );
}

function AllocationAction({
  assetId,
  decision,
  refetch,
}: {
  assetId: string;
  decision: ReturnType<typeof buildAllocationDecisionBrief>;
  refetch: () => Promise<unknown>;
}) {
  if (decision.actionKind === "build_proposal") {
    return (
      <ActionButton
        endpoint={`/assets/${assetId}/execution/proposal/build`}
        label="Build proposal"
        refetch={refetch}
        variant="primary"
      />
    );
  }

  return (
    <Link
      className="rounded-md border border-sky-400/35 bg-sky-400/10 px-3 py-2 text-sm font-semibold text-sky-100 transition hover:border-sky-300 hover:bg-sky-400/20"
      href={decision.actionHref}
    >
      {decision.actionLabel}
    </Link>
  );
}

function buildAllocationDecisionBrief({
  allocation,
  automationControl,
  primary,
  secondary,
  strategyIntent,
}: {
  allocation?: MultiMarketAllocationResponse;
  automationControl?: AutomationControlStatusResponse;
  primary?: MultiMarketAllocationCandidate | null;
  secondary?: MultiMarketAllocationCandidate | null;
  strategyIntent?: StrategyIntentResponse;
}) {
  const blockers = [
    ...(allocation?.excluded_markets ?? []).flatMap((row) => row.blocking_reasons ?? []),
    ...(automationControl?.blockers ?? []).map((row) =>
      String(row.message ?? row.required_action ?? row.label ?? "Automation blocker"),
    ),
    ...(strategyIntent?.blocking_evidence ?? []).map((row) =>
      String(row.message ?? row.blocker ?? row.label ?? "Strategy blocker"),
    ),
  ].filter(Boolean);
  const canBuildProposal =
    Boolean(primary) &&
    allocation?.allocation_status !== "blocked" &&
    Boolean(automationControl?.paper_trading_allowed || automationControl?.supervised_trading_allowed || automationControl?.live_trading_allowed);
  const tone: DecisionBriefTone = automationControl?.live_trading_allowed
    ? "emerald"
    : canBuildProposal
      ? "blue"
      : blockers.length
        ? "amber"
        : "slate";

  return {
    actionHref: blockers.length ? "/execution/market-connectors" : "/market-rules",
    actionKind: canBuildProposal ? "build_proposal" : "open_link",
    actionLabel: blockers.length ? "Open market access" : "Review market rules",
    blockers: blockers.slice(0, 4).map(String),
    decision: primary
      ? `Allocate primary trading route to ${primary.market_name ?? primary.adapter_id}.`
      : "No eligible primary market route is ready for automated trading.",
    evidence: [
      `Allocation status ${allocation?.allocation_status ?? "not evaluated"}`,
      `Primary ${primary?.market_name ?? "none"}${secondary?.market_name ? `, secondary ${secondary.market_name}` : ""}`,
      `Expected route revenue ${formatCurrency(allocation?.summary?.total_expected_revenue_eur)}`,
      `Automation ${automationControl?.automation_status ?? automationControl?.automation_mode ?? "not evaluated"}`,
    ],
    nextAction:
      automationControl?.next_automation_action?.message ??
      primary?.operator_next_action ??
      allocation?.recommended_actions?.[0] ??
      blockers[0] ??
      "Clear market and connector gates before proposal generation.",
    tone,
  };
}

function RouteDecisionCard({
  label,
  route,
}: {
  label: string;
  route?: MultiMarketAllocationCandidate | null;
}) {
  return (
    <SectionCard
      action={<StatusPill tone={route ? routeTone(route) : "amber"}>{route?.recommendation_status ?? "missing"}</StatusPill>}
      title={label}
    >
      <div className="flex flex-col gap-4">
        <div>
          <div className="text-xl font-semibold text-white">
            {route?.market_name ?? "No route selected"}
          </div>
          <div className="mt-1 text-sm text-slate-400">
            {route?.adapter_id ?? "Allocator has not selected this route."}
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <RouteMetric label="Mode" value={route ? executionMode(route) : "-"} />
          <RouteMetric label="Score" value={formatNumber(route?.allocation_score, 1)} />
          <RouteMetric label="Revenue" value={formatCurrency(route?.expected_revenue_eur)} />
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4 text-sm leading-6 text-slate-300">
          {route?.operator_next_action ?? "No allocator action is available yet."}
        </div>
      </div>
    </SectionCard>
  );
}

function RouteMetric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/45 p-3">
      <div className="text-xs uppercase tracking-[0.12em] text-slate-500">{label}</div>
      <div className="mt-2 text-sm font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function AllocationGateRow({
  label,
  tone,
  value,
}: {
  label: string;
  tone: DecisionBriefTone;
  value: React.ReactNode;
}) {
  return (
    <div className="flex min-h-14 items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3">
      <span className="text-sm text-slate-300">{label}</span>
      <StatusPill tone={tone}>{value}</StatusPill>
    </div>
  );
}

function WorkflowLink({
  href,
  label,
  value,
}: {
  href: string;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <Link
      className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3 transition hover:border-sky-400/40 hover:bg-sky-950/20"
      href={href}
    >
      <span className="text-sm font-medium text-slate-200">{label}</span>
      <span className="text-xs text-sky-200">{value}</span>
    </Link>
  );
}

function formatCandidateRows(rows: MultiMarketAllocationCandidate[]): TableRow[] {
  return rows.map((row, index) => ({
    ...row,
    allocated_power_mw: formatNumber(row.allocated_power_mw, 2),
    allocation_score: formatNumber(row.allocation_score, 1),
    expected_revenue_eur: formatCurrency(row.expected_revenue_eur),
    execution_mode: executionMode(row),
    market_group: marketGroup(row),
    missing_credentials: row.missing_credentials?.join(" | ") ?? "-",
    rank: index + 1,
    risk_score: formatNumber(row.risk_score, 1),
  }));
}

function formatExcludedRows(rows: MultiMarketAllocationCandidate[]): TableRow[] {
  return rows.map((row) => ({
    ...row,
    blocking_reasons: row.blocking_reasons?.join(" | ") ?? "-",
    market_group: marketGroup(row),
    missing_connector_controls: row.missing_connector_controls?.join(" | ") ?? "-",
    missing_credentials: row.missing_credentials?.join(" | ") ?? "-",
  }));
}

function marketGroup(row: MultiMarketAllocationCandidate) {
  const adapterId = String(row.adapter_id ?? "");

  if (adapterId.startsWith("epex_") || row.connector_family === "wholesale") {
    return "EPEX wholesale";
  }

  if (adapterId.startsWith("regelleistung_") || row.connector_family === "ancillary") {
    return "Ancillary services";
  }

  return row.connector_family ?? "Other";
}

function executionMode(row: MultiMarketAllocationCandidate) {
  if (row.live_submission) {
    return "live";
  }

  if (row.automation_blocking_level === "supervised_auto") {
    return "supervised";
  }

  if (row.recommendation_status === "excluded") {
    return "blocked";
  }

  return "paper";
}

function allocationTone(value: unknown): DecisionBriefTone {
  if (value === "recommended") {
    return "emerald";
  }

  if (value === "operator_review_required" || value === "watchlist") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function routeTone(route: MultiMarketAllocationCandidate): DecisionBriefTone {
  if (route.live_submission) {
    return "emerald";
  }

  if (route.recommendation_status === "recommended") {
    return "blue";
  }

  if (route.recommendation_status === "excluded") {
    return "red";
  }

  return "amber";
}

function automationTone(data?: AutomationControlStatusResponse): DecisionBriefTone {
  if (data?.live_trading_allowed) {
    return "emerald";
  }

  if (data?.supervised_trading_allowed || data?.paper_trading_allowed) {
    return "blue";
  }

  if (data?.automation_status === "blocked" || data?.automation_mode === "blocked") {
    return "red";
  }

  return "amber";
}

function strategyTone(value: unknown): DecisionBriefTone {
  if (value === "arbitrage" || value === "hybrid_stack" || value === "ancillary_priority") {
    return "emerald";
  }

  if (value) {
    return "blue";
  }

  return "slate";
}
