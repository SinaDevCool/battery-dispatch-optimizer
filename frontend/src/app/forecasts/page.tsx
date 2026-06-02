"use client";

import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import type {
  ActualPriceStatusResponse,
  ForecastActualResponse,
  ForecastPreviewResponse,
  ForecastProfitabilityResponse,
  ForecastStatusResponse,
} from "@/types/api";

export default function ForecastsPage() {
  const { selectedAssetId } = useAssetContext();

  const status = useQuery({
    queryFn: () => apiGet<ForecastStatusResponse>("/forecast/status"),
    queryKey: ["forecast-status"],
  });

  const preview = useQuery({
    queryFn: () =>
      apiGet<ForecastPreviewResponse>("/forecast/preview"),
    queryKey: ["forecast-preview"],
  });

  const comparison = useQuery({
    queryFn: () =>
      apiGet<ForecastProfitabilityResponse>(
        "/forecasts/compare-profitability/latest",
      ),
    queryKey: ["forecast-profitability-comparison"],
  });

  const actualPrices = useQuery({
    queryFn: () =>
      apiGet<ActualPriceStatusResponse>("/data/actual-prices/status"),
    queryKey: ["actual-prices-status"],
  });

  const forecastActual = useQuery({
    queryFn: () =>
      apiGet<ForecastActualResponse>(
        `/backtesting/forecast-actual/latest?asset_id=${selectedAssetId}`,
      ),
    queryKey: ["forecast-actual-latest", selectedAssetId],
  });

  const comparisonRows = comparison.data?.results ?? [];

  return (
    <>
      <PageHeading
        description="Compare local forecasts, ENTSO-E inputs, in-house model outputs, forecast quality, and profitability impact."
        eyebrow="Forecast intelligence"
        title="Forecasts"
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint="/data/update-entsoe"
          label="Update ENTSO-E forecast"
          refetch={() => Promise.all([status.refetch(), preview.refetch()])}
          variant="primary"
        />
        <ActionButton
          endpoint="/forecasts/compare-profitability"
          label="Compare forecast profitability"
          refetch={() => comparison.refetch()}
        />
        <ActionButton
          endpoint="/data/update-actual-prices"
          label="Update actual prices"
          refetch={() => actualPrices.refetch()}
        />
        <ActionButton
          endpoint={`/backtesting/forecast-actual/run?asset_id=${selectedAssetId}`}
          label="Run forecast-vs-actual"
          refetch={() => forecastActual.refetch()}
        />
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-6">
        <KpiCard label="Rows" value={String(status.data?.row_count ?? "-")} />
        <KpiCard label="Valid rows" value={String(status.data?.valid_row_count ?? "-")} />
        <KpiCard
          accent="amber"
          label="Negative price hours"
          value={String(status.data?.negative_price_hours ?? "-")}
        />
        <KpiCard
          accent="blue"
          label="Average price"
          value={`${status.data?.average_price ?? "-"} EUR/MWh`}
        />
        <KpiCard
          label="Actual prices"
          value={String(actualPrices.data?.status ?? "-")}
        />
        <KpiCard
          accent="blue"
          label="Forecast backtest"
          value={String(forecastActual.data?.status ?? "-")}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard title="Forecast preview">
          <DataTable
            columns={["timestamp", "forecast_price", "forecast_provider", "forecast_model"]}
            rows={preview.data?.preview ?? []}
          />
        </SectionCard>

        <SectionCard title="Profitability by forecast provider">
          <DataTable
            columns={[
              "forecast_provider",
              "signal",
              "total_pnl_eur",
              "profit_per_mw_day",
              "status",
            ]}
            rows={comparisonRows}
          />
          {comparisonRows.length ? (
            <div className="mt-5">
              <BarComparisonChart
                data={comparisonRows}
                xKey="forecast_provider"
                yKey="total_pnl_eur"
              />
            </div>
          ) : null}
        </SectionCard>
      </div>
    </>
  );
}
