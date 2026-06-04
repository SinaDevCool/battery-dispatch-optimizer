"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatNumber } from "@/lib/format";
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

export default function MarketPricesPage() {
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
        description="Inspect market price coverage, forecast regimes, negative-price windows, actual-price readiness, and German tradable product context."
        eyebrow="Market intelligence"
        title="Market prices"
      />

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

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone="blue">{forecastRows.length} interval(s)</StatusPill>}
          title="Forecast price curve"
        >
          <DataTable
            columns={[
              "timestamp",
              "forecast_price",
              "price_regime",
              "forecast_provider",
              "forecast_model",
            ]}
            rows={forecastRows}
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

        <SectionCard title="Price evidence summary">
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
          title="German market products"
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
            rows={productRows}
          />
        </SectionCard>

        <SectionCard title="Price data controls">
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
      </div>
    </>
  );
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
    maxPrice,
    minPrice,
    negativeHours: Number(status?.negative_price_hours ?? prices.filter((value) => value < 0).length),
    spread: maxPrice - minPrice,
    volatility: Math.sqrt(variance),
  };
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
