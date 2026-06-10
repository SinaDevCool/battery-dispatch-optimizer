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
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type {
  AutomationControlStatusResponse,
  MarketAdapterReadinessGateResponse,
  MarketAdapterRouteGate,
  MultiMarketAllocationCandidate,
  MultiMarketAllocationResponse,
  StrategyIntentResponse,
  TableRow,
} from "@/types/api";

type AllocationPersonaFraming = {
  blockedTitle: string;
  candidatesTitle: string;
  controlsTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  eyebrow: string;
  gateTitle: string;
  linksTitle: string;
  primaryLabel: string;
  secondaryLabel: string;
  title: string;
};

export default function ExecutionMarketAllocationPage() {
  const { selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();
  const framing = getAllocationPersonaFraming(personaId);

  const allocation = useQuery({
    queryFn: () =>
      apiGet<MultiMarketAllocationResponse>(
        `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      ),
    queryKey: ["market-allocation-allocation", selectedAssetId],
  });

  const readinessGate = useQuery({
    queryFn: () =>
      apiGet<MarketAdapterReadinessGateResponse>(
        `/assets/${selectedAssetId}/execution/market-adapter/readiness-gate`,
      ),
    queryKey: ["market-allocation-readiness-gate", selectedAssetId],
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
  const gateSummary = readinessGate.data?.summary ?? {};
  const primary = allocation.data?.primary_market;
  const secondary = allocation.data?.secondary_market;
  const candidateRows = allocation.data?.allocation ?? [];
  const excludedRows = allocation.data?.excluded_markets ?? [];
  const routeGateRows = readinessGate.data?.route_gates ?? [];
  const liveRows = candidateRows.filter((row) => row.live_submission === true);
  const paperRows = candidateRows.filter((row) => row.live_submission !== true);
  const decisionBrief = useMemo(
    () =>
      buildAllocationDecisionBrief({
        allocation: allocation.data,
        automationControl: automationControl.data,
        primary,
        readinessGate: readinessGate.data,
        secondary,
        strategyIntent: strategyIntent.data,
      }),
    [allocation.data, automationControl.data, primary, readinessGate.data, secondary, strategyIntent.data],
  );

  const refetchAllocation = () =>
    Promise.all([
      allocation.refetch(),
      readinessGate.refetch(),
      automationControl.refetch(),
      strategyIntent.refetch(),
    ]);

  return (
    <>
      <PageHeading
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
      />

      <div className="mb-6">
        <DecisionBrief
          action={<AllocationAction assetId={selectedAssetId} decision={decisionBrief} refetch={refetchAllocation} />}
          blockers={decisionBrief.blockers}
          decision={decisionBrief.decision}
          evidence={decisionBrief.evidence}
          eyebrow={framing.decisionEyebrow}
          nextAction={decisionBrief.nextAction}
          tone={decisionBrief.tone}
          title={framing.decisionTitle}
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <KpiCard
          accent={allocationTone(allocation.data?.allocation_status)}
          helper="Backend allocator status"
          label="Allocation"
          value={allocation.data?.allocation_status ?? "-"}
        />
        <KpiCard
          accent={primary ? routeTone(primary) : "amber"}
          helper={primary?.gate_closure_label ?? "No primary market selected"}
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
        <KpiCard
          accent={gateTone(readinessGate.data?.gate_status)}
          helper={`${gateSummary.supervised_ready_count ?? 0} supervised / ${gateSummary.live_ready_count ?? 0} live`}
          label="Market gate"
          value={readinessGate.data?.gate_status ?? "-"}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <RouteDecisionCard label={framing.primaryLabel} route={primary} />
        <RouteDecisionCard label={framing.secondaryLabel} route={secondary} />
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={allocationTone(allocation.data?.allocation_status)}>{candidateRows.length}</StatusPill>}
          title={framing.candidatesTitle}
        >
          <DataTable
            columns={[
              "rank",
              "market_group",
              "adapter_id",
              "market_name",
              "execution_mode",
              "trading_clock_status",
              "market_gate_status",
              "market_gate_score",
              "market_gate_settlement_basis",
              "gate_closure_label",
              "recommendation_status",
              "allocation_score",
              "allocated_power_mw",
              "expected_revenue_eur",
              "operator_next_action",
            ]}
            rows={formatCandidateRows(candidateRows).slice(0, 8)}
          />
        </SectionCard>

        <SectionCard title={framing.controlsTitle}>
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

      <SectionCard
        action={<StatusPill tone={gateTone(readinessGate.data?.gate_status)}>{readinessGate.data?.gate_status ?? "-"}</StatusPill>}
        className="mt-5"
        title={framing.gateTitle}
      >
        <DataTable
          columns={[
            "adapter_id",
            "market_family",
            "gate_status",
            "readiness_score",
            "settlement_basis",
            "trading_clock_status",
            "gate_closure_label",
            "missing_controls",
            "next_action",
          ]}
          rows={formatRouteGateRows(routeGateRows)}
        />
      </SectionCard>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={excludedRows.length ? "amber" : "emerald"}>{excludedRows.length}</StatusPill>}
          title={framing.blockedTitle}
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

        <SectionCard title={framing.linksTitle}>
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

function getAllocationPersonaFraming(
  personaId: PersonaId,
): AllocationPersonaFraming {
  const defaults: AllocationPersonaFraming = {
    blockedTitle: "Excluded or blocked routes",
    candidatesTitle: "Ranked candidate routes",
    controlsTitle: "Strategy intent and control gates",
    decisionEyebrow: "Route allocation decision",
    decisionTitle: "Where should automation trade now?",
    description:
      "Rank eligible EPEX and regelleistung routes, select primary and secondary execution paths, and feed the bid proposal engine with automation-ready market intent.",
    eyebrow: "Automated trading",
    gateTitle: "Market adapter readiness gate",
    linksTitle: "Allocation workflow links",
    primaryLabel: "Primary route",
    secondaryLabel: "Secondary route",
    title: "Market allocation",
  };

  const frames: Partial<Record<PersonaId, AllocationPersonaFraming>> = {
    trading_desk: {
      blockedTitle: "Desk-blocked routes",
      candidatesTitle: "Desk-ranked route candidates",
      controlsTitle: "Desk strategy intent and gates",
      decisionEyebrow: "Desk route decision",
      decisionTitle: "Which route should the desk use for the bid package?",
      description:
        "Rank tradable market routes for the desk, choose primary and fallback execution paths, and send the selected route into bid proposal generation.",
      eyebrow: "Trading desk",
      gateTitle: "Desk market readiness gate",
      linksTitle: "Desk allocation workflow links",
      primaryLabel: "Desk primary route",
      secondaryLabel: "Desk fallback route",
      title: "Desk market allocation",
    },
    revenue_analyst: {
      blockedTitle: "Blocked route value",
      candidatesTitle: "Commercial route ranking",
      controlsTitle: "Commercial strategy intent and gates",
      decisionEyebrow: "Revenue route decision",
      decisionTitle: "Which route creates defensible commercial value?",
      description:
        "Compare market routes by expected revenue, eligibility, risk, and blocked upside so allocation economics can feed revenue assurance and reporting evidence.",
      eyebrow: "Commercial analytics OS",
      gateTitle: "Commercial market readiness gate",
      linksTitle: "Commercial allocation workflow links",
      primaryLabel: "Commercial primary route",
      secondaryLabel: "Commercial fallback route",
      title: "Revenue market allocation",
    },
    market_operations: {
      blockedTitle: "Operationally blocked routes",
      candidatesTitle: "Operational route candidates",
      controlsTitle: "Route operations gates",
      decisionEyebrow: "Market operations route decision",
      decisionTitle: "Which route is operationally ready?",
      description:
        "Connect route allocation to adapter readiness, trading clock, connector status, missing controls, and operator next actions before submission readiness.",
      eyebrow: "Market operations",
      gateTitle: "Adapter readiness gate",
      linksTitle: "Route operations workflow links",
      primaryLabel: "Operational primary route",
      secondaryLabel: "Operational fallback route",
      title: "Route allocation operations",
    },
    risk_compliance: {
      blockedTitle: "Governance-blocked routes",
      candidatesTitle: "Governed route candidates",
      controlsTitle: "Governance strategy and control gates",
      decisionEyebrow: "Governance route decision",
      decisionTitle: "Is the selected route allowed by policy and risk gates?",
      description:
        "Review route selection against automation policy, market gate readiness, excluded markets, approval needs, and settlement basis before bid proposal or escalation.",
      eyebrow: "Risk & compliance",
      gateTitle: "Governed market readiness gate",
      linksTitle: "Governance allocation workflow links",
      primaryLabel: "Governed primary route",
      secondaryLabel: "Governed fallback route",
      title: "Governed market allocation",
    },
  };

  return frames[personaId] ?? defaults;
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
  readinessGate,
  secondary,
  strategyIntent,
}: {
  allocation?: MultiMarketAllocationResponse;
  automationControl?: AutomationControlStatusResponse;
  primary?: MultiMarketAllocationCandidate | null;
  readinessGate?: MarketAdapterReadinessGateResponse;
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
      `Market gate ${readinessGate?.gate_status ?? "not evaluated"}`,
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
          <RouteMetric label="Gate" value={route?.market_gate_status?.replaceAll("_", " ") ?? "-"} />
          <RouteMetric label="Score" value={formatNumber(route?.allocation_score, 1)} />
          <RouteMetric label="Revenue" value={formatCurrency(route?.expected_revenue_eur)} />
          <RouteMetric label="Cut-off" value={route?.gate_closure_label ?? "-"} />
          <RouteMetric label="Order style" value={route?.order_style?.replaceAll("_", " ") ?? "-"} />
          <RouteMetric label="Settlement" value={route?.market_gate_settlement_basis?.replaceAll("_", " ") ?? "-"} />
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
    gate_closure_label: row.gate_closure_label ?? "-",
    market_group: marketGroup(row),
    market_gate_missing_controls: row.market_gate_missing_controls?.join(" | ") ?? "-",
    market_gate_score: formatNumber(row.market_gate_score, 1),
    market_gate_settlement_basis: row.market_gate_settlement_basis?.replaceAll("_", " ") ?? "-",
    market_gate_status: row.market_gate_status?.replaceAll("_", " ") ?? "-",
    missing_credentials: row.missing_credentials?.join(" | ") ?? "-",
    rank: index + 1,
    risk_score: formatNumber(row.risk_score, 1),
    trading_clock_status: row.trading_clock_status?.replaceAll("_", " ") ?? "-",
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

function formatRouteGateRows(rows: MarketAdapterRouteGate[]): TableRow[] {
  return rows.map((row) => ({
    ...row,
    automation_lane: row.automation_lane?.replaceAll("_", " ") ?? "-",
    gate_status: row.gate_status?.replaceAll("_", " ") ?? "-",
    missing_controls: row.missing_controls?.slice(0, 4).join(" | ") ?? "-",
    order_style: row.order_style?.replaceAll("_", " ") ?? "-",
    readiness_score: formatNumber(row.readiness_score, 1),
    settlement_basis: row.settlement_basis?.replaceAll("_", " ") ?? "-",
    trading_clock_status: row.trading_clock_status?.replaceAll("_", " ") ?? "-",
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

function gateTone(value: unknown): DecisionBriefTone {
  if (value === "live_ready_route_available" || value === "live_ready") {
    return "emerald";
  }

  if (value === "supervised_ready_route_available" || value === "supervised_ready") {
    return "blue";
  }

  if (value === "paper_only_routes_available" || value === "paper_only") {
    return "amber";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function routeTone(route: MultiMarketAllocationCandidate): DecisionBriefTone {
  if (route.market_gate_status === "live_ready") {
    return "emerald";
  }

  if (route.market_gate_status === "supervised_ready") {
    return "blue";
  }

  if (route.market_gate_status === "paper_only") {
    return "amber";
  }

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
