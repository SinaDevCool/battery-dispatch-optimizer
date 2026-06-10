"use client";

import Link from "next/link";
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
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type {
  AutomationGuardrailsResponse,
  AutomationControlStatusResponse,
  ExecutionReadinessResponse,
  ForecastConfidenceResponse,
  LatestSignalResponse,
  MultiMarketAllocationCandidate,
  MultiMarketAllocationResponse,
  SignalSummary,
  StrategyIntentResponse,
  TableRow,
} from "@/types/api";

type MarketSignalsPersonaFraming = {
  automationControlsTitle: string;
  blockersTitle: string;
  bridgeTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  dispatchTitle: string;
  eyebrow: string;
  nextStepTitle: string;
  orderDecisionTitle: string;
  routeTitle: string;
  title: string;
};

export default function MarketSignalsPage() {
  const { selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();
  const framing = getMarketSignalsPersonaFraming(personaId);

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["market-signals-latest-signal", selectedAssetId],
  });

  const confidence = useQuery({
    queryFn: () =>
      apiGet<ForecastConfidenceResponse>(
        `/assets/${selectedAssetId}/forecast-confidence`,
      ),
    queryKey: ["market-signals-forecast-confidence", selectedAssetId],
  });

  const guardrails = useQuery({
    queryFn: () =>
      apiGet<AutomationGuardrailsResponse>(
        `/assets/${selectedAssetId}/execution/automation-guardrails`,
      ),
    queryKey: ["market-signals-guardrails", selectedAssetId],
  });

  const readiness = useQuery({
    queryFn: () =>
      apiGet<ExecutionReadinessResponse>(
        `/assets/${selectedAssetId}/execution/readiness`,
      ),
    queryKey: ["market-signals-readiness", selectedAssetId],
  });

  const automationControl = useQuery({
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["market-signals-automation-control", selectedAssetId],
  });

  const strategyIntent = useQuery({
    queryFn: () =>
      apiGet<StrategyIntentResponse>(
        `/assets/${selectedAssetId}/execution/strategy-intent`,
      ),
    queryKey: ["market-signals-strategy-intent", selectedAssetId],
  });

  const allocation = useQuery({
    queryFn: () =>
      apiGet<MultiMarketAllocationResponse>(
        `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      ),
    queryKey: ["market-signals-market-allocation", selectedAssetId],
  });

  const signalSummary = signal.data?.data?.summary ?? {};
  const metadata = signal.data?.data?.metadata ?? {};
  const dispatchRows = signal.data?.data?.dispatch ?? [];
  const activeRows = dispatchRows.filter((row) => row.action !== "idle");
  const primaryMarket = allocation.data?.primary_market;
  const automationMode = classifyAutomationMode({
    allocationStatus: allocation.data?.allocation_status,
    confidenceEligibility: confidence.data?.automation_eligibility,
    guardrailStatus: guardrails.data?.automation_status,
    readinessStatus: readiness.data?.readiness_status,
    signalValue: signalSummary.signal,
  });
  const recommendedAction = buildRecommendedAction({
    automationMode,
    primaryMarket,
    signalValue: signalSummary.signal,
  });
  const blockers = buildAutomationBlockers({
    allocation: allocation.data,
    automationControl: automationControl.data,
    guardrails: guardrails.data,
    readiness: readiness.data,
  });
  const blockerSummary = summarizeBlockers(blockers);
  const decisionBrief = buildMarketSignalDecisionBrief({
    allocation: allocation.data,
    automationControl: automationControl.data,
    automationMode,
    assetId: selectedAssetId,
    blockers,
    confidence: confidence.data,
    primaryMarket,
    recommendedAction,
    signalSummary,
    strategyIntent: strategyIntent.data,
  });
  const backendConnectionRows = buildSignalBackendConnectionRows({
    allocationStatus: allocation.data?.allocation_status,
    automationStatus: automationControl.data?.automation_status,
    confidenceStatus: confidence.data?.automation_eligibility,
    guardrailStatus: guardrails.data?.automation_status,
    readinessStatus: readiness.data?.readiness_status,
    selectedAssetId,
    signalStatus: signal.data?.status,
    strategyStatus: strategyIntent.data?.strategy_mode,
  });

  const refetchSignals = () =>
    Promise.all([
      signal.refetch(),
      confidence.refetch(),
      guardrails.refetch(),
      readiness.refetch(),
      automationControl.refetch(),
      strategyIntent.refetch(),
      allocation.refetch(),
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
          action={
            <ActionButton
              endpoint={
                decisionBrief.actionEndpoint ??
                `/assets/${selectedAssetId}/signal/run-latest`
              }
              label={decisionBrief.actionLabel}
              refetch={refetchSignals}
              variant="primary"
            />
          }
          blockers={decisionBrief.blockers}
          decision={decisionBrief.decision}
          evidence={decisionBrief.evidence}
          eyebrow={framing.decisionEyebrow}
          nextAction={decisionBrief.nextAction}
          tone={decisionBrief.tone}
          title={framing.decisionTitle}
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={signalSummary.signal === "ACTION" ? "emerald" : "slate"}
          helper={String(signalSummary.opportunity_level ?? "No opportunity level")}
          label="Trading signal"
          value={String(signalSummary.signal ?? "-")}
        />
        <KpiCard
          accent={automationTone(automationMode)}
          helper="Derived from confidence, readiness, guardrails, and allocation"
          label="Automation mode"
          value={automationMode}
        />
        <KpiCard
          accent={confidenceTone(confidence.data?.confidence_band)}
          helper={confidence.data?.automation_eligibility ?? "No automation policy"}
          label="Confidence"
          value={`${formatNumber(confidence.data?.confidence_score, 1)}/100`}
        />
        <KpiCard
          accent={readiness.data?.readiness_status === "blocked" ? "red" : "blue"}
          helper={`${readiness.data?.summary?.blocked ?? 0} blocked / ${readiness.data?.summary?.review ?? 0} review`}
          label="Execution readiness"
          value={readiness.data?.readiness_status ?? "-"}
        />
      </div>

      <SectionCard
        action={
          <StatusPill tone={decisionBrief.tone}>
            {automationMode === "blocked" ? "Order blocked" : "Order path evaluated"}
          </StatusPill>
        }
        className="mb-6"
        title={framing.bridgeTitle}
      >
        <DataTable
          columns={["capability", "backend_route", "status", "business_value"]}
          rows={backendConnectionRows}
        />
      </SectionCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={automationTone(automationMode)}>{automationMode}</StatusPill>}
          title={framing.orderDecisionTitle}
        >
          <div className="grid gap-3 md:grid-cols-2">
            <AutomationDecisionRow
              label="Recommended action"
              tone={automationTone(automationMode)}
              value={recommendedAction}
            />
            <AutomationDecisionRow
              label="Target market"
              tone={primaryMarket ? "blue" : "amber"}
              value={primaryMarket?.market_name ?? "No market route selected"}
            />
            <AutomationDecisionRow
              label="Market allocation"
              tone={allocationTone(allocation.data?.allocation_status)}
              value={allocation.data?.allocation_status ?? "-"}
            />
            <AutomationDecisionRow
              label="Forecast provider"
              tone="slate"
              value={metadata.forecast_provider ?? metadata.source ?? "-"}
            />
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <KpiCard
              accent="emerald"
              helper="Forecast dispatch economics"
              label="Expected PnL"
              value={formatCurrency(signalSummary.total_pnl_eur)}
            />
            <KpiCard
              accent="blue"
              helper="Intervals with charge/discharge intent"
              label="Active intervals"
              value={activeRows.length}
            />
            <KpiCard
              accent={primaryMarket ? "emerald" : "amber"}
              helper={primaryMarket?.operator_next_action ?? "Market allocation required"}
              label="Primary route score"
              value={formatNumber(primaryMarket?.allocation_score, 1)}
            />
          </div>
        </SectionCard>

        <SectionCard title={framing.nextStepTitle}>
          <div className="space-y-3">
            <AutomationStepLink
              href="/forecasts"
              label="Validate forecast confidence"
              status={confidence.data?.automation_eligibility ?? "not evaluated"}
            />
            <AutomationStepLink
              href="/execution/market-allocation"
              label="Confirm market route"
              status={primaryMarket?.market_name ?? "allocation pending"}
            />
            <AutomationStepLink
              href="/execution/proposals"
              label="Build bid proposal"
              status={signalSummary.signal === "ACTION" ? "ready to build" : "wait for action signal"}
            />
            <AutomationStepLink
              href="/execution/risk-approval"
              label="Apply guardrails and approval"
              status={guardrails.data?.automation_status ?? "not evaluated"}
            />
            <AutomationStepLink
              href="/execution/simulation"
              label="Run paper market validation"
              status={automationMode === "blocked" ? "blocked" : "next validation step"}
            />
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard
          action={<StatusPill tone={blockers.length ? "amber" : "emerald"}>{blockers.length}</StatusPill>}
          title={framing.blockersTitle}
        >
          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <AutomationDecisionRow label="Readiness" tone={blockerSummary.readiness ? "amber" : "emerald"} value={blockerSummary.readiness} />
            <AutomationDecisionRow label="Guardrails" tone={blockerSummary.guardrails ? "amber" : "emerald"} value={blockerSummary.guardrails} />
            <AutomationDecisionRow label="Market route" tone={blockerSummary.market ? "amber" : "emerald"} value={blockerSummary.market} />
          </div>
          <DataTable columns={["source", "blocker"]} rows={blockers.slice(0, 8)} />
        </SectionCard>

        <SectionCard
          action={<StatusPill tone="blue">{activeRows.length} active</StatusPill>}
          title={framing.dispatchTitle}
        >
          <DataTable
            columns={[
              "timestamp",
              "action",
              "price",
              "grid_energy_mwh",
              "battery_energy_mwh",
              "pnl_eur",
              "total_pnl_eur",
            ]}
            rows={formatDispatchRows(activeRows.slice(0, 12))}
          />
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard title={framing.routeTitle}>
          <DataTable
            columns={[
              "adapter_id",
              "market_name",
              "recommendation_status",
              "allocation_score",
              "risk_score",
              "allocated_power_mw",
              "expected_revenue_eur",
              "operator_next_action",
            ]}
            rows={formatMarketCandidates((allocation.data?.allocation ?? []).slice(0, 8))}
          />
        </SectionCard>

        <SectionCard title={framing.automationControlsTitle}>
          <div className="grid gap-3">
            <ActionButton
              endpoint={`/assets/${selectedAssetId}/signal/run-latest`}
              label="Refresh signal"
              refetch={refetchSignals}
              variant="primary"
            />
            <ActionButton
              endpoint={`/assets/${selectedAssetId}/execution/proposal/build`}
              label="Build proposal"
              refetch={refetchSignals}
            />
            <ActionButton
              endpoint={`/assets/${selectedAssetId}/execution/paper-trade/run`}
              label="Run paper trade"
              refetch={refetchSignals}
            />
          </div>
        </SectionCard>
      </div>
    </>
  );
}

function getMarketSignalsPersonaFraming(
  personaId: PersonaId,
): MarketSignalsPersonaFraming {
  const defaults: MarketSignalsPersonaFraming = {
    automationControlsTitle: "Automation controls",
    blockersTitle: "Automation blockers",
    bridgeTitle: "Signal evidence chain",
    decisionEyebrow: "Signal-to-trade decision",
    decisionTitle: "Can automation trade this signal?",
    description:
      "Convert forecast, price, readiness, market allocation, and guardrail evidence into the next executable trading step: proposal, paper trade, supervised live candidate, or hold.",
    dispatchTitle: "Dispatch signal evidence",
    eyebrow: "Market intelligence",
    nextStepTitle: "Next automated workflow step",
    orderDecisionTitle: "Signal-to-order decision",
    routeTitle: "Market route candidates",
    title: "Signal-to-order readiness",
  };

  const frames: Partial<Record<PersonaId, MarketSignalsPersonaFraming>> = {
    trading_desk: {
      automationControlsTitle: "Desk action controls",
      blockersTitle: "Desk execution blockers",
      bridgeTitle: "Signal-to-desk evidence chain",
      decisionEyebrow: "Desk signal decision",
      decisionTitle: "Can the desk act on this signal?",
      description:
        "Turn forecast, price, market allocation, and risk evidence into the next desk action: build proposal, paper trade, supervised candidate, or hold.",
      dispatchTitle: "Desk dispatch signal evidence",
      eyebrow: "Trading desk",
      nextStepTitle: "Next desk workflow step",
      orderDecisionTitle: "Signal-to-bid decision",
      routeTitle: "Tradable route candidates",
      title: "Desk signal readiness",
    },
    automation_operator: {
      automationControlsTitle: "Operator automation controls",
      blockersTitle: "Automation escalation blockers",
      bridgeTitle: "Signal-to-automation evidence chain",
      decisionEyebrow: "Automation escalation decision",
      decisionTitle: "Can this signal move through automation safely?",
      description:
        "Combine signal, confidence, readiness, guardrails, policy freshness, and market route evidence into the safe next automation action.",
      dispatchTitle: "Automation signal evidence",
      eyebrow: "Internal automation OS",
      nextStepTitle: "Next automation control step",
      orderDecisionTitle: "Signal-to-automation decision",
      routeTitle: "Automation route candidates",
      title: "Automation signal control",
    },
    forecast_quant: {
      automationControlsTitle: "Signal validation controls",
      blockersTitle: "Model-to-signal blockers",
      bridgeTitle: "Forecast-to-signal evidence chain",
      decisionEyebrow: "Model signal decision",
      decisionTitle: "Does model evidence support this signal?",
      description:
        "Trace the signal back to forecast confidence, active dispatch intervals, provider metadata, allocation, and guardrail outcomes before model output influences execution.",
      dispatchTitle: "Model dispatch signal evidence",
      eyebrow: "Model quality OS",
      nextStepTitle: "Next model validation step",
      orderDecisionTitle: "Forecast-to-signal decision",
      routeTitle: "Modelled market route candidates",
      title: "Model signal trust",
    },
    revenue_analyst: {
      automationControlsTitle: "Commercial signal controls",
      blockersTitle: "Revenue signal blockers",
      bridgeTitle: "Signal-to-revenue evidence chain",
      decisionEyebrow: "Commercial signal decision",
      decisionTitle: "Does this signal support the revenue case?",
      description:
        "Connect signal actionability, expected PnL, route selection, confidence, and blockers to revenue assurance, dispatch economics, and reporting evidence.",
      dispatchTitle: "Revenue signal evidence",
      eyebrow: "Commercial analytics OS",
      nextStepTitle: "Next commercial workflow step",
      orderDecisionTitle: "Signal-to-revenue decision",
      routeTitle: "Revenue route candidates",
      title: "Revenue signal readiness",
    },
  };

  return frames[personaId] ?? defaults;
}

function classifyAutomationMode({
  allocationStatus,
  confidenceEligibility,
  guardrailStatus,
  readinessStatus,
  signalValue,
}: {
  allocationStatus?: string;
  confidenceEligibility?: string;
  guardrailStatus?: string;
  readinessStatus?: string;
  signalValue?: string;
}) {
  if (signalValue !== "ACTION") {
    return "wait_for_signal";
  }

  if (
    readinessStatus === "blocked" ||
    guardrailStatus === "blocked" ||
    allocationStatus === "blocked"
  ) {
    return "blocked";
  }

  if (confidenceEligibility === "paper_only" || guardrailStatus === "paper_only") {
    return "paper_only";
  }

  if (
    confidenceEligibility === "supervised_live_candidate" &&
    readinessStatus === "supervised_ready"
  ) {
    return "supervised_live_candidate";
  }

  return "human_approval_required";
}

function buildRecommendedAction({
  automationMode,
  primaryMarket,
  signalValue,
}: {
  automationMode: string;
  primaryMarket?: MultiMarketAllocationCandidate | null;
  signalValue?: string;
}) {
  if (signalValue !== "ACTION") {
    return "Wait for a tradable market signal.";
  }

  if (automationMode === "blocked") {
    return "Keep automation disabled and clear blockers.";
  }

  if (automationMode === "paper_only") {
    return "Run paper trade against the recommended market route.";
  }

  if (automationMode === "supervised_live_candidate") {
    return `Prepare supervised execution for ${primaryMarket?.market_name ?? "the selected market"}.`;
  }

  return "Request operator approval before paper or supervised execution.";
}

function buildAutomationBlockers({
  allocation,
  automationControl,
  guardrails,
  readiness,
}: {
  allocation?: MultiMarketAllocationResponse;
  automationControl?: AutomationControlStatusResponse;
  guardrails?: AutomationGuardrailsResponse;
  readiness?: ExecutionReadinessResponse;
}) {
  const rows: TableRow[] = [];

  for (const check of readiness?.checks ?? []) {
    if (check.status === "blocked" || check.status === "review") {
      rows.push({
        blocker: check.message ?? check.label ?? check.check,
        source: `readiness:${check.check ?? "check"}`,
      });
    }
  }

  for (const guardrail of guardrails?.guardrails ?? []) {
    if (guardrail.status === "blocked" || guardrail.status === "review") {
      rows.push({
        blocker: guardrail.message ?? guardrail.guardrail,
        source: `guardrail:${guardrail.guardrail ?? "check"}`,
      });
    }
  }

  for (const blocker of automationControl?.blockers ?? []) {
    rows.push({
      blocker:
        blocker.message ??
        blocker.required_action ??
        blocker.label ??
        blocker.check ??
        "Automation control blocker",
      source: `automation:${blocker.source ?? blocker.check ?? "control"}`,
    });
  }

  for (const gate of automationControl?.freshness_gates ?? []) {
    if (gate.freshness_status === "missing" || gate.freshness_status === "stale") {
      rows.push({
        blocker: gate.required_action ?? `${gate.label ?? gate.gate_id} is ${gate.freshness_status}`,
        source: `freshness:${gate.gate_id ?? "gate"}`,
      });
    }
  }

  for (const market of allocation?.excluded_markets ?? []) {
    rows.push({
      blocker: (market.blocking_reasons ?? []).join(" | ") || market.operator_next_action,
      source: `market:${market.adapter_id ?? "candidate"}`,
    });
  }

  return rows;
}

function buildMarketSignalDecisionBrief({
  allocation,
  automationControl,
  automationMode,
  assetId,
  blockers,
  confidence,
  primaryMarket,
  recommendedAction,
  signalSummary,
  strategyIntent,
}: {
  allocation?: MultiMarketAllocationResponse;
  automationControl?: AutomationControlStatusResponse;
  automationMode: string;
  assetId: string;
  blockers: TableRow[];
  confidence?: ForecastConfidenceResponse;
  primaryMarket?: MultiMarketAllocationCandidate | null;
  recommendedAction: string;
  signalSummary: SignalSummary;
  strategyIntent?: StrategyIntentResponse;
}) {
  const automationAction = automationControl?.next_automation_action;
  const intentAction = strategyIntent?.recommended_next_action;
  const action = String(
    automationAction?.label ??
      intentAction?.label ??
      recommendedAction ??
      "Refresh market signal",
  );
  const blockerLabels = blockers
    .slice(0, 4)
    .map((row) => String(row.blocker ?? "Automation blocker"));

  const actionEndpoint =
    signalSummary?.signal === "ACTION" && automationMode !== "blocked"
      ? `/assets/${assetId}/execution/proposal/build`
      : undefined;

  return {
    actionEndpoint,
    actionLabel:
      signalSummary?.signal === "ACTION" && automationMode !== "blocked"
        ? "Build proposal"
        : "Refresh signal",
    blockers: blockerLabels,
    decision: action,
    evidence: [
      `Signal ${signalSummary?.signal ?? "unavailable"} with ${signalSummary?.opportunity_level ?? "no"} opportunity level`,
      `Expected PnL ${formatCurrency(signalSummary?.total_pnl_eur)}`,
      `Primary route ${primaryMarket?.market_name ?? allocation?.primary_market?.market_name ?? "not selected"}`,
      `Forecast confidence ${formatNumber(confidence?.confidence_score, 1)}/100 (${confidence?.automation_eligibility ?? "not evaluated"})`,
    ],
    nextAction:
      automationAction?.message ??
      intentAction?.message ??
      primaryMarket?.operator_next_action ??
      recommendedAction,
    tone: automationTone(automationMode),
  };
}

function summarizeBlockers(rows: TableRow[]) {
  return {
    guardrails: rows.filter((row) => String(row.source ?? "").startsWith("guardrail")).length,
    market: rows.filter((row) => String(row.source ?? "").startsWith("market")).length,
    readiness: rows.filter((row) => String(row.source ?? "").startsWith("readiness")).length,
  };
}

function formatDispatchRows(rows: TableRow[]) {
  return rows.map((row) => ({
    ...row,
    pnl_eur: formatCurrency(row.pnl_eur),
    price: formatNumber(row.price, 2),
    timestamp: formatDateTime(row.timestamp),
    total_pnl_eur: formatCurrency(row.total_pnl_eur),
  }));
}

function formatMarketCandidates(rows: MultiMarketAllocationCandidate[]) {
  return rows.map((row) => ({
    ...row,
    allocated_power_mw: formatNumber(row.allocated_power_mw, 2),
    allocation_score: formatNumber(row.allocation_score, 1),
    expected_revenue_eur: formatCurrency(row.expected_revenue_eur),
    risk_score: formatNumber(row.risk_score, 1),
  }));
}

function AutomationDecisionRow({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "amber" | "blue" | "emerald" | "red" | "slate";
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3">
      <span className="text-sm text-slate-300">{label}</span>
      <StatusPill tone={tone}>{value}</StatusPill>
    </div>
  );
}

function AutomationStepLink({
  href,
  label,
  status,
}: {
  href: string;
  label: string;
  status: React.ReactNode;
}) {
  return (
    <Link
      className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3 transition hover:border-sky-400/40 hover:bg-sky-950/20"
      href={href}
    >
      <span className="text-sm font-medium text-slate-200">{label}</span>
      <span className="text-xs text-sky-200">{status}</span>
    </Link>
  );
}

function automationTone(value: unknown): DecisionBriefTone {
  if (value === "supervised_live_candidate") {
    return "emerald";
  }

  if (value === "human_approval_required") {
    return "blue";
  }

  if (value === "paper_only" || value === "wait_for_signal") {
    return "amber";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function confidenceTone(value: unknown): DecisionBriefTone {
  if (value === "high") {
    return "emerald";
  }

  if (value === "medium") {
    return "blue";
  }

  if (value === "low") {
    return "amber";
  }

  return "slate";
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

function buildSignalBackendConnectionRows({
  allocationStatus,
  automationStatus,
  confidenceStatus,
  guardrailStatus,
  readinessStatus,
  selectedAssetId,
  signalStatus,
  strategyStatus,
}: {
  allocationStatus?: string;
  automationStatus?: string;
  confidenceStatus?: string;
  guardrailStatus?: string;
  readinessStatus?: string;
  selectedAssetId: string;
  signalStatus?: string;
  strategyStatus?: string;
}) {
  return [
    {
      backend_route: `/assets/${selectedAssetId}/signal/latest`,
      business_value: "Provides the charge/discharge intent and expected trading value.",
      capability: "Trading signal",
      status: signalStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/forecast-confidence`,
      business_value: "Decides whether the forecast can support automation or only paper mode.",
      capability: "Forecast confidence",
      status: confidenceStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      business_value: "Selects the market route before bid proposal generation.",
      capability: "Market allocation",
      status: allocationStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/readiness`,
      business_value: "Checks proposal, telemetry, approval, market adapter, and settlement readiness.",
      capability: "Execution readiness",
      status: readinessStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/automation-guardrails`,
      business_value: "Blocks unsafe live trading before order creation.",
      capability: "Guardrails",
      status: guardrailStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/automation-control/status`,
      business_value: "Combines freshness gates and policy state into the next automation action.",
      capability: "Automation control",
      status: automationStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/strategy-intent`,
      business_value: "Turns signal evidence into strategy posture and bid-building intent.",
      capability: "Strategy intent",
      status: strategyStatus ?? "not_loaded",
    },
  ];
}
