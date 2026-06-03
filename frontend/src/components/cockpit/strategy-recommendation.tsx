"use client";

import { CheckCircle2, CircleAlert, ShieldCheck, TrendingUp } from "lucide-react";

import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  AncillaryEligibilityResponse,
  BusinessDecision,
  EegComplianceResponse,
  HedgingSummary,
  RevenueAllocationResult,
  RevenueStackResult,
  SignalMetadata,
  SignalSummary,
} from "@/types/api";

type RecommendationTone = "amber" | "blue" | "emerald" | "red" | "slate";

export function StrategyRecommendation({
  allocationRows = [],
  ancillary,
  businessDecision,
  eeg,
  hedgingSummary,
  metadata,
  revenueRows,
  summary,
}: {
  allocationRows?: RevenueAllocationResult[];
  ancillary?: AncillaryEligibilityResponse;
  businessDecision?: BusinessDecision;
  eeg?: EegComplianceResponse;
  hedgingSummary?: HedgingSummary;
  metadata?: SignalMetadata;
  revenueRows: RevenueStackResult[];
  summary: SignalSummary;
}) {
  const strategy = buildStrategyRecommendation({
    allocationRows,
    ancillary,
    businessDecision,
    eeg,
    hedgingSummary,
    metadata,
    revenueRows,
    summary,
  });

  return (
    <SectionCard
      action={<StatusPill tone={strategy.tone}>{strategy.readiness}</StatusPill>}
      title="Strategy recommendation"
    >
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <div className="flex items-start gap-3">
          <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-sky-400/30 bg-sky-400/10 text-sky-200">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">
              Recommended commercial posture
            </div>
          <h3 className="mt-2 text-xl font-semibold leading-7 text-white">
            {strategy.title}
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {strategy.description}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <StrategyMetric
          label="Merchant PnL"
          value={formatCurrency(strategy.metrics.merchantPnl)}
          helper={`${formatNumber(strategy.metrics.profitPerMwDay, 2)} EUR/MW-day`}
        />
        <StrategyMetric
          label="Hedged revenue"
          value={formatCurrency(strategy.metrics.hedgedRevenue)}
          helper="Revenue certainty layer"
        />
        <StrategyMetric
          label="Residual exposure"
          value={formatCurrency(strategy.metrics.residualExposure)}
          helper="Open merchant risk"
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <DecisionList
          icon={<CheckCircle2 className="h-4 w-4" />}
          items={strategy.actions}
          title="Recommended actions"
          tone="emerald"
        />
        <DecisionList
          icon={<CircleAlert className="h-4 w-4" />}
          items={strategy.blockers}
          title="Blockers before automation"
          tone="amber"
        />
      </div>

      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/60 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-200">
          <ShieldCheck className="h-4 w-4 text-sky-300" />
          Decision basis
        </div>
        <div className="grid gap-2 text-sm text-slate-400 md:grid-cols-2">
          <BasisRow label="Forecast model" value={strategy.basis.forecastModel} />
          <BasisRow label="Forecast source" value={strategy.basis.forecastSource} />
          <BasisRow label="EEG status" value={strategy.basis.eegStatus} />
          <BasisRow label="Ancillary eligible" value={strategy.basis.ancillaryStatus} />
          <BasisRow label="Revenue products" value={strategy.basis.revenueProducts} />
          <BasisRow label="Allocation outputs" value={strategy.basis.allocationOutputs} />
        </div>
      </div>
    </SectionCard>
  );
}

function buildStrategyRecommendation({
  allocationRows,
  ancillary,
  businessDecision,
  eeg,
  hedgingSummary,
  metadata,
  revenueRows,
  summary,
}: {
  allocationRows: RevenueAllocationResult[];
  ancillary?: AncillaryEligibilityResponse;
  businessDecision?: BusinessDecision;
  eeg?: EegComplianceResponse;
  hedgingSummary?: HedgingSummary;
  metadata?: SignalMetadata;
  revenueRows: RevenueStackResult[];
  summary: SignalSummary;
}) {
  if (businessDecision) {
    const status = businessDecision.recommendation_status;
    const tone: RecommendationTone =
      status === "advisory_ready"
        ? "emerald"
        : status === "commercial_review"
          ? "amber"
          : status === "no_trade"
            ? "slate"
            : "blue";

    return {
      actions: businessDecision.recommended_actions ?? [],
      basis: {
        allocationOutputs: String(allocationRows.length),
        ancillaryStatus: ancillary?.eligible ? "yes" : "not yet",
        eegStatus: businessDecision.eeg_eligible ? "eligible" : "needs review",
        forecastModel: businessDecision.forecast_model ?? "-",
        forecastSource: businessDecision.forecast_provider ?? "-",
        revenueProducts: String(businessDecision.eligible_product_count ?? revenueRows.length),
      },
      blockers: businessDecision.blockers ?? [],
      description:
        businessDecision.description ??
        "The backend decision service returned a persisted recommendation.",
      metrics: {
        hedgedRevenue: businessDecision.hedged_revenue_eur,
        merchantPnl: businessDecision.expected_pnl_eur,
        profitPerMwDay: businessDecision.profit_per_mw_day,
        residualExposure: businessDecision.residual_exposure_eur,
      },
      readiness: businessDecision.readiness ?? "Backend decision",
      title: businessDecision.recommendation_title ?? "Backend decision available",
      tone,
    };
  }

  const pnl = Number(summary.total_pnl_eur ?? 0);
  const hedgedRevenue = Number(hedgingSummary?.hedged_revenue_eur ?? 0);
  const residualExposure = Number(hedgingSummary?.residual_exposure_eur ?? 0);
  const modelledProducts = revenueRows.filter((row) => row.status === "ok");
  const hasReserveAssumptions = revenueRows.some(
    (row) =>
      String(row.market ?? "").toLowerCase().includes("fcr") ||
      String(row.market ?? "").toLowerCase().includes("afrr") ||
      String(row.market ?? "").toLowerCase().includes("mfrr"),
  );
  const fallbackForecast = metadata?.source === "local_saved_forecast";
  const blockers: string[] = [];

  if (fallbackForecast) {
    blockers.push("Live forecast source unavailable; local saved forecast was used.");
  }

  if (!eeg?.eeg_eligible) {
    blockers.push("EEG eligibility or energy-origin treatment is not fully cleared.");
  }

  if (!ancillary?.eligible) {
    blockers.push("Ancillary eligibility is not confirmed for reserve commitments.");
  }

  if (!hasReserveAssumptions) {
    blockers.push("Reserve market prices and prequalification assumptions are incomplete.");
  }

  blockers.push("Market API, telemetry, approval capture, and order limits must be connected before auto-trading.");

  const actions = [
    pnl > 0
      ? "Use day-ahead arbitrage as the primary dispatch path for the current signal."
      : "Keep the asset in advisory mode until a positive dispatch opportunity appears.",
    hedgedRevenue > 0
      ? "Keep hedge floor visible to separate bankable revenue from merchant upside."
      : "Add a hedge-floor scenario before presenting revenue certainty to asset owners.",
    residualExposure > 0
      ? "Track residual exposure as merchant risk before enabling automated execution."
      : "Residual exposure is low under the current hedge assumptions.",
    modelledProducts.length > 1
      ? "Compare market products on risk-adjusted revenue, not raw revenue only."
      : "Do not commit to stacked products until assumptions are populated.",
    allocationRows.length
      ? "Use revenue allocation outputs to prioritize capacity across modelled products."
      : "Run revenue allocation before presenting a portfolio capacity plan.",
  ];

  if (pnl > 0 && eeg?.eeg_eligible) {
    return {
      actions,
      basis: {
        allocationOutputs: String(allocationRows.length),
        ancillaryStatus: ancillary?.eligible ? "yes" : "not yet",
        eegStatus: eeg?.eeg_eligible ? "eligible" : eeg?.status ?? "-",
        forecastModel: metadata?.forecast_model ?? "-",
        forecastSource: metadata?.source ?? "-",
        revenueProducts: String(revenueRows.length),
      },
      blockers,
      description:
        "The current backend evidence supports a merchant day-ahead dispatch recommendation, while hedging and reserve products should remain advisory until execution and market assumptions are complete.",
      metrics: {
        hedgedRevenue,
        merchantPnl: pnl,
        profitPerMwDay: summary.profit_per_mw_day,
        residualExposure,
      },
      readiness: "Advisory ready",
      title: "Run day-ahead arbitrage, keep hedge floor visible, defer reserve automation",
      tone: "emerald" as RecommendationTone,
    };
  }

  if (pnl > 0) {
    return {
      actions,
      basis: {
        allocationOutputs: String(allocationRows.length),
        ancillaryStatus: ancillary?.eligible ? "yes" : "not yet",
        eegStatus: eeg?.eeg_eligible ? "eligible" : eeg?.status ?? "-",
        forecastModel: metadata?.forecast_model ?? "-",
        forecastSource: metadata?.source ?? "-",
        revenueProducts: String(revenueRows.length),
      },
      blockers,
      description:
        "The signal has positive economics, but regulatory and execution evidence is not complete enough to treat it as an executable trading instruction.",
      metrics: {
        hedgedRevenue,
        merchantPnl: pnl,
        profitPerMwDay: summary.profit_per_mw_day,
        residualExposure,
      },
      readiness: "Commercial review",
      title: "Use dispatch as commercial upside, hold execution until blockers clear",
      tone: "amber" as RecommendationTone,
    };
  }

  return {
    actions,
    basis: {
      allocationOutputs: String(allocationRows.length),
      ancillaryStatus: ancillary?.eligible ? "yes" : "not yet",
      eegStatus: eeg?.eeg_eligible ? "eligible" : eeg?.status ?? "-",
      forecastModel: metadata?.forecast_model ?? "-",
      forecastSource: metadata?.source ?? "-",
      revenueProducts: String(revenueRows.length),
    },
    blockers,
    description:
      "The current signal does not justify active dispatch. Keep the asset available, refresh forecast inputs, and use hedging analysis to protect downside.",
    metrics: {
      hedgedRevenue,
      merchantPnl: pnl,
      profitPerMwDay: summary.profit_per_mw_day,
      residualExposure,
    },
    readiness: "No trade",
    title: "Do not dispatch; refresh forecast and preserve optionality",
    tone: "slate" as RecommendationTone,
  };
}

function StrategyMetric({
  helper,
  label,
  value,
}: {
  helper: string;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-lg font-semibold text-white">{value}</div>
      <div className="mt-1 text-xs text-slate-500">{helper}</div>
    </div>
  );
}

function DecisionList({
  icon,
  items,
  title,
  tone,
}: {
  icon: React.ReactNode;
  items: string[];
  title: string;
  tone: RecommendationTone;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <span className="text-sky-300">{icon}</span>
          {title}
        </div>
        <StatusPill tone={tone}>{items.length}</StatusPill>
      </div>
      <ul className="space-y-2">
        {items.map((item) => (
          <li className="text-sm leading-6 text-slate-400" key={item}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function BasisRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-md border border-slate-800 bg-slate-900/40 px-3 py-2">
      <span>{label}</span>
      <span className="truncate text-right font-semibold text-slate-200">
        {value}
      </span>
    </div>
  );
}
