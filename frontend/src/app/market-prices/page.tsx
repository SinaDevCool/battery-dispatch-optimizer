"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { DataTable } from "@/components/data-table";
import { DecisionBrief, type DecisionBriefTone } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type {
  ActualPriceStatusResponse,
  ApiEnvelope,
  ForecastPreviewResponse,
  ForecastStatusResponse,
  TableRow,
} from "@/types/api";

type MarketsResponse = ApiEnvelope<{
  market_count?: number;
  markets?: TableRow[];
}>;

type MarketProductsResponse = ApiEnvelope<{
  product_count?: number;
  products?: TableRow[];
}>;

type MarketPricesPersonaFraming = {
  bridgeTitle: string;
  controlsTitle: string;
  curveTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  eyebrow: string;
  productsTitle: string;
  summaryTitle: string;
  title: string;
};

export default function MarketPricesPage() {
  const { persona, personaId } = usePersona();
  const framing = getMarketPricesPersonaFraming(personaId);

  const forecastStatus = useQuery({
    queryFn: () => apiGet<ForecastStatusResponse>("/forecast/status"),
    queryKey: ["market-prices-forecast-status"],
  });

  const forecastPreview = useQuery({
    queryFn: () => apiGet<ForecastPreviewResponse>("/forecast/preview"),
    queryKey: ["market-prices-forecast-preview"],
  });

  const actualPrices = useQuery({
    queryFn: () => apiGet<ActualPriceStatusResponse>("/data/actual-prices/status"),
    queryKey: ["market-prices-actual-status"],
  });

  const markets = useQuery({
    queryFn: () => apiGet<MarketsResponse>("/markets"),
    queryKey: ["market-prices-markets"],
  });

  const products = useQuery({
    queryFn: () => apiGet<MarketProductsResponse>("/markets/products?country=Germany"),
    queryKey: ["market-prices-products"],
  });

  const forecastRows = useMemo(
    () => normalizeForecastPriceRows(forecastPreview.data?.preview ?? []),
    [forecastPreview.data?.preview],
  );
  const priceStats = useMemo(
    () => buildPriceStats(forecastRows, forecastStatus.data),
    [forecastRows, forecastStatus.data],
  );
  const productRows = useMemo(
    () => normalizeProductRows(products.data?.products ?? []),
    [products.data?.products],
  );
  const actionablePriceRows = useMemo(
    () => buildActionablePriceRows(forecastRows),
    [forecastRows],
  );
  const backendConnectionRows = useMemo(
    () =>
      buildMarketPriceBackendRows({
        actualPriceStatus: actualPrices.data?.status,
        forecastPreviewRows: forecastRows.length,
        forecastStatus: forecastStatus.data?.status,
        marketCount: markets.data?.market_count,
        productCount: products.data?.product_count,
      }),
    [
      actualPrices.data?.status,
      forecastRows.length,
      forecastStatus.data?.status,
      markets.data?.market_count,
      products.data?.product_count,
    ],
  );
  const decisionBrief = useMemo(
    () =>
      buildPriceDecisionBrief({
        actualPrices: actualPrices.data,
        forecastRows,
        forecastStatus: forecastStatus.data,
        marketCount: markets.data?.market_count,
        priceStats,
        productCount: products.data?.product_count,
      }),
    [
      actualPrices.data,
      forecastRows,
      forecastStatus.data,
      markets.data?.market_count,
      priceStats,
      products.data?.product_count,
    ],
  );

  const refetchPrices = () =>
    Promise.all([
      forecastStatus.refetch(),
      forecastPreview.refetch(),
      actualPrices.refetch(),
      markets.refetch(),
      products.refetch(),
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
              endpoint={decisionBrief.actionEndpoint}
              label={decisionBrief.actionLabel}
              refetch={refetchPrices}
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
          accent={forecastStatus.data?.status === "ok" ? "emerald" : "amber"}
          helper={`${forecastStatus.data?.valid_row_count ?? "-"} valid row(s)`}
          label="Forecast price coverage"
          value={forecastStatus.data?.status ?? "-"}
        />
        <KpiCard
          accent={priceStats.negativeHours ? "amber" : "emerald"}
          helper="Forecast prices below zero"
          label="Negative-price hours"
          value={priceStats.negativeHours}
        />
        <KpiCard
          accent="blue"
          helper={`${formatNumber(priceStats.minPrice, 2)} to ${formatNumber(priceStats.maxPrice, 2)} EUR/MWh`}
          label="Forecast spread"
          value={`${formatNumber(priceStats.spread, 2)} EUR/MWh`}
        />
        <KpiCard
          accent={actualPrices.data?.status === "ok" ? "emerald" : "amber"}
          helper={actualPrices.data?.last_timestamp ?? "Actual prices not ready"}
          label="Actual price evidence"
          value={actualPrices.data?.status ?? "-"}
        />
      </div>

      <SectionCard
        action={
          <StatusPill tone={decisionBrief.tone}>
            {decisionBrief.blockers.length ? "Advisory prices" : "Automation-ready prices"}
          </StatusPill>
        }
        className="mb-6"
        title={framing.bridgeTitle}
      >
        <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <DataTable
            columns={["decision_input", "value"]}
            rows={[
              {
                decision_input: "Automated use",
                value: decisionBrief.blockers.length
                  ? "Keep bid generation supervised until gaps clear."
                  : "Feed price curve into signal, allocation, and proposal generation.",
              },
              {
                decision_input: "Charge candidates",
                value: `${priceStats.negativeHours + priceStats.lowHours} interval(s)`,
              },
              {
                decision_input: "Discharge candidates",
                value: `${priceStats.highHours + priceStats.scarcityHours} interval(s)`,
              },
              {
                decision_input: "Primary blocker",
                value: decisionBrief.blockers[0] ?? "No blocking price-data issue.",
              },
            ]}
          />
          <DataTable
            columns={["capability", "backend_route", "status", "business_value"]}
            rows={backendConnectionRows}
          />
        </div>
      </SectionCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone="blue">{forecastRows.length} interval(s)</StatusPill>}
          title={framing.curveTitle}
        >
          <div className="mb-4 grid gap-3 md:grid-cols-4">
            <MarketPriceRow label="Negative" tone={priceStats.negativeHours ? "amber" : "emerald"} value={priceStats.negativeHours} />
            <MarketPriceRow label="Low" tone="blue" value={priceStats.lowHours} />
            <MarketPriceRow label="High" tone="blue" value={priceStats.highHours} />
            <MarketPriceRow label="Scarcity" tone={priceStats.scarcityHours ? "amber" : "slate"} value={priceStats.scarcityHours} />
          </div>
          <DataTable
            columns={[
              "timestamp",
              "forecast_price",
              "price_regime",
              "automation_use",
            ]}
            rows={actionablePriceRows}
          />
          {forecastRows.length ? (
            <div className="mt-5">
              <BarComparisonChart
                data={forecastRows}
                xKey="timestamp_label"
                yKey="forecast_price"
              />
            </div>
          ) : null}
        </SectionCard>

        <SectionCard title={framing.summaryTitle}>
          <div className="space-y-3">
            <MarketPriceRow label="Average forecast" tone="blue" value={`${formatNumber(priceStats.averagePrice, 2)} EUR/MWh`} />
            <MarketPriceRow label="Volatility estimate" tone="blue" value={`${formatNumber(priceStats.volatility, 2)} EUR/MWh`} />
            <MarketPriceRow label="Actual average" tone="emerald" value={`${formatNumber(actualPrices.data?.average_actual_price, 2)} EUR/MWh`} />
            <MarketPriceRow label="Actual min/max" tone="slate" value={`${formatNumber(actualPrices.data?.min_actual_price, 2)} / ${formatNumber(actualPrices.data?.max_actual_price, 2)}`} />
            <MarketPriceRow label="Market profiles" tone="blue" value={markets.data?.market_count ?? "-"} />
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone="blue">{productRows.length} product(s)</StatusPill>}
          title={framing.productsTitle}
        >
          <DataTable
            columns={[
              "product_id",
              "product_name",
              "market",
              "revenue_type",
              "settlement_granularity",
              "minimum_power_mw",
            ]}
            rows={productRows.slice(0, 8)}
          />
        </SectionCard>

        {persona.layer === "client" ? null : (
          <SectionCard title={framing.controlsTitle}>
            <div className="grid gap-3">
              <ActionButton
                endpoint="/data/update-entsoe"
                label="Update ENTSO-E forecast"
                refetch={refetchPrices}
                variant="primary"
              />
              <ActionButton
                endpoint="/data/update-actual-prices"
                label="Update actual prices"
                refetch={refetchPrices}
              />
            </div>
          </SectionCard>
        )}
      </div>
    </>
  );
}

function getMarketPricesPersonaFraming(
  personaId: PersonaId,
): MarketPricesPersonaFraming {
  const defaults: MarketPricesPersonaFraming = {
    bridgeTitle: "Price-to-automation bridge",
    controlsTitle: "Price data controls",
    curveTitle: "Actionable price curve",
    decisionEyebrow: "Price-to-bid decision",
    decisionTitle: "Can automation trust this price evidence?",
    description:
      "Decide whether market-price evidence is reliable enough for automated bid creation, forecast backtesting, charge/discharge window selection, and settlement proof.",
    eyebrow: "Market intelligence",
    productsTitle: "German market products",
    summaryTitle: "Price evidence summary",
    title: "Market price trust",
  };

  const frames: Partial<Record<PersonaId, MarketPricesPersonaFraming>> = {
    trading_desk: {
      bridgeTitle: "Price-to-desk bridge",
      controlsTitle: "Desk price data controls",
      curveTitle: "Tradable price curve",
      decisionEyebrow: "Desk price decision",
      decisionTitle: "Can the desk trust this price curve?",
      description:
        "Show whether forecast and actual price evidence is fresh enough for desk bid sizing, charge/discharge window selection, and proposal generation.",
      eyebrow: "Trading desk",
      productsTitle: "Tradable German products",
      summaryTitle: "Desk price evidence summary",
      title: "Desk price trust",
    },
    forecast_quant: {
      bridgeTitle: "Price-to-model bridge",
      controlsTitle: "Model price data controls",
      curveTitle: "Model price curve",
      decisionEyebrow: "Model price evidence decision",
      decisionTitle: "Is the price evidence good enough for model validation?",
      description:
        "Validate forecast price coverage, actual-price readiness, regimes, volatility, and raw curve quality before backtesting or model-driven dispatch.",
      eyebrow: "Model quality OS",
      productsTitle: "Modelled market products",
      summaryTitle: "Model price evidence summary",
      title: "Price evidence for models",
    },
    revenue_analyst: {
      bridgeTitle: "Price-to-revenue bridge",
      controlsTitle: "Revenue price data controls",
      curveTitle: "Revenue price curve",
      decisionEyebrow: "Revenue price decision",
      decisionTitle: "Can this price evidence support the revenue case?",
      description:
        "Connect price freshness, volatility, negative-price windows, actual-price proof, and tradable products to revenue assurance and dispatch economics.",
      eyebrow: "Commercial analytics OS",
      productsTitle: "Revenue market products",
      summaryTitle: "Revenue price evidence summary",
      title: "Price evidence for revenue",
    },
    market_operations: {
      bridgeTitle: "Price-data operations bridge",
      controlsTitle: "Market data controls",
      curveTitle: "Operational price curve",
      decisionEyebrow: "Market data readiness decision",
      decisionTitle: "Is market data ready for downstream systems?",
      description:
        "Monitor forecast and actual-price feeds, market profiles, product context, and data gaps so trading, model validation, and settlement evidence have current inputs.",
      eyebrow: "Market operations",
      productsTitle: "Market product catalog",
      summaryTitle: "Market data evidence summary",
      title: "Market data readiness",
    },
    project_developer: {
      bridgeTitle: "Price-to-development bridge",
      controlsTitle: "Price evidence controls",
      curveTitle: "Development price assumptions",
      decisionEyebrow: "Development price decision",
      decisionTitle: "Are price assumptions credible enough for development planning?",
      description:
        "Show whether forecast and actual-price evidence can support project scenarios, market assumptions, and the commercial case before investment commitment.",
      eyebrow: "Development readiness",
      productsTitle: "Relevant German market products",
      summaryTitle: "Development price evidence summary",
      title: "Price assumptions",
    },
  };

  return frames[personaId] ?? defaults;
}

function normalizeForecastPriceRows(rows: NonNullable<ForecastPreviewResponse["preview"]>) {
  return rows.map((row) => {
    const price = Number(row.forecast_price ?? 0);

    return {
      ...row,
      forecast_price: Number.isFinite(price) ? price : 0,
      price_regime: classifyPriceRegime(price),
      timestamp_label: String(row.timestamp).slice(5, 16),
    };
  });
}

function normalizeProductRows(rows: TableRow[]) {
  return rows.map((row) => ({
    ...row,
    market: row.market ?? row.market_segment ?? "-",
    minimum_power_mw: row.minimum_power_mw ?? row.min_power_mw ?? "-",
    product_name: row.product_name ?? row.name ?? "-",
    revenue_type: row.revenue_type ?? row.product_family ?? "-",
    settlement_granularity: row.settlement_granularity ?? row.market_time_unit ?? "-",
  }));
}

function buildPriceStats(
  rows: ReturnType<typeof normalizeForecastPriceRows>,
  status?: ForecastStatusResponse,
) {
  const prices = rows
    .map((row) => Number(row.forecast_price))
    .filter((value) => Number.isFinite(value));

  const minPrice = prices.length
    ? Math.min(...prices)
    : Number(status?.min_price ?? 0);
  const maxPrice = prices.length
    ? Math.max(...prices)
    : Number(status?.max_price ?? 0);
  const averagePrice = prices.length
    ? prices.reduce((sum, value) => sum + value, 0) / prices.length
    : Number(status?.average_price ?? 0);
  const variance = prices.length
    ? prices.reduce((sum, value) => sum + (value - averagePrice) ** 2, 0) /
      prices.length
    : 0;

  return {
    averagePrice,
    highHours: prices.filter((value) => value > 80 && value <= 120).length,
    lowHours: prices.filter((value) => value >= 0 && value < 25).length,
    maxPrice,
    minPrice,
    negativeHours: Number(status?.negative_price_hours ?? prices.filter((value) => value < 0).length),
    scarcityHours: prices.filter((value) => value > 120).length,
    spread: maxPrice - minPrice,
    volatility: Math.sqrt(variance),
  };
}

function buildActionablePriceRows(
  rows: ReturnType<typeof normalizeForecastPriceRows>,
) {
  const actionRows = rows.filter(
    (row) => row.price_regime === "negative" || row.price_regime === "scarcity",
  );
  const sourceRows = actionRows.length ? actionRows : rows;

  return sourceRows.slice(0, 18).map((row) => ({
    ...row,
    automation_use: priceAutomationUse(String(row.price_regime)),
  }));
}

function priceAutomationUse(regime: string) {
  if (regime === "negative") {
    return "charge candidate";
  }

  if (regime === "scarcity" || regime === "high") {
    return "discharge candidate";
  }

  if (regime === "low") {
    return "watch charge window";
  }

  return "baseline evidence";
}

function buildPriceDecisionBrief({
  actualPrices,
  forecastRows,
  forecastStatus,
  marketCount,
  priceStats,
  productCount,
}: {
  actualPrices?: ActualPriceStatusResponse;
  forecastRows: ReturnType<typeof normalizeForecastPriceRows>;
  forecastStatus?: ForecastStatusResponse;
  marketCount?: number;
  priceStats: ReturnType<typeof buildPriceStats>;
  productCount?: number;
}) {
  const blockers: string[] = [];

  if (forecastStatus?.status !== "ok" || !forecastRows.length) {
    blockers.push("Forecast price curve is missing or not validated.");
  }

  if (Number(forecastStatus?.missing_prices ?? 0) > 0) {
    blockers.push(`${forecastStatus?.missing_prices} forecast price(s) are missing.`);
  }

  if (Number(forecastStatus?.duplicate_timestamps ?? 0) > 0) {
    blockers.push(`${forecastStatus?.duplicate_timestamps} duplicate forecast timestamp(s) need cleanup.`);
  }

  if (actualPrices?.status !== "ok") {
    blockers.push("Actual price evidence is not ready for forecast performance validation.");
  }

  if (!marketCount || !productCount) {
    blockers.push("Tradable market and product context is incomplete.");
  }

  const hasPriceCurve = forecastStatus?.status === "ok" && forecastRows.length > 0;
  const hasActualPrices = actualPrices?.status === "ok";
  const tone: DecisionBriefTone = blockers.length
    ? hasPriceCurve
      ? "amber"
      : "red"
    : "emerald";

  return {
    actionEndpoint: hasPriceCurve ? "/data/update-actual-prices" : "/data/update-entsoe",
    actionLabel: hasPriceCurve ? "Update actual prices" : "Update forecast",
    blockers: blockers.slice(0, 4),
    decision: blockers.length
      ? "Keep market-price evidence in advisory mode until data gaps are cleared."
      : "Price evidence is ready to feed automated bid proposal generation.",
    evidence: [
      `${forecastRows.length || forecastStatus?.valid_row_count || 0} forecast interval(s) available`,
      `${priceStats.negativeHours} negative-price hour(s) flagged for charge/discharge strategy`,
      `Forecast range ${formatNumber(priceStats.minPrice, 2)} to ${formatNumber(priceStats.maxPrice, 2)} EUR/MWh`,
      hasActualPrices
        ? `Actual prices ready through ${actualPrices?.last_timestamp ?? "latest file"}`
        : "Actual prices unavailable for backtest evidence",
    ],
    nextAction: blockers.length
      ? blockers[0]
      : "Use this curve in Market Signals and validate realized performance after execution.",
    tone,
  };
}

function buildMarketPriceBackendRows({
  actualPriceStatus,
  forecastPreviewRows,
  forecastStatus,
  marketCount,
  productCount,
}: {
  actualPriceStatus?: string;
  forecastPreviewRows: number;
  forecastStatus?: string;
  marketCount?: number;
  productCount?: number;
}) {
  return [
    {
      backend_route: "/forecast/status",
      business_value: "Validates whether the price curve is complete enough to trade.",
      capability: "Forecast price coverage",
      status: forecastStatus ?? "not_loaded",
    },
    {
      backend_route: "/forecast/preview",
      business_value: "Provides interval-level prices for charge/discharge window selection.",
      capability: "Price curve preview",
      status: `${forecastPreviewRows} row(s)`,
    },
    {
      backend_route: "/data/actual-prices/status",
      business_value: "Supplies realized price evidence for model performance and settlement.",
      capability: "Actual price evidence",
      status: actualPriceStatus ?? "not_loaded",
    },
    {
      backend_route: "/markets",
      business_value: "Shows which market profiles exist before choosing a route.",
      capability: "Market profiles",
      status: `${marketCount ?? 0} market(s)`,
    },
    {
      backend_route: "/markets/products?country=Germany",
      business_value: "Maps price evidence to tradable German products.",
      capability: "Tradable products",
      status: `${productCount ?? 0} product(s)`,
    },
  ];
}

function classifyPriceRegime(price: number) {
  if (price < 0) {
    return "negative";
  }

  if (price < 25) {
    return "low";
  }

  if (price > 120) {
    return "scarcity";
  }

  if (price > 80) {
    return "high";
  }

  return "normal";
}

function MarketPriceRow({
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
