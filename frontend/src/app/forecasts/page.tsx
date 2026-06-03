"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { DataTable } from "@/components/data-table";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type {
  ActualPriceStatusResponse,
  ForecastActualResponse,
  ForecastPerformanceHistoryResponse,
  ForecastPerformanceRun,
  ForecastPreviewResponse,
  ForecastProfitabilityResponse,
  ForecastProfitabilityResult,
  ForecastStatusResponse,
  LatestSignalResponse,
  TableRow,
} from "@/types/api";

export default function ForecastsPage() {
  const { selectedAssetId } = useAssetContext();

  const status = useQuery({
    queryFn: () => apiGet<ForecastStatusResponse>("/forecast/status"),
    queryKey: ["forecast-status"],
  });

  const preview = useQuery({
    queryFn: () => apiGet<ForecastPreviewResponse>("/forecast/preview"),
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

  const performance = useQuery({
    queryFn: () =>
      apiGet<ForecastPerformanceHistoryResponse>(
        `/assets/${selectedAssetId}/forecast-performance?limit=25`,
      ),
    queryKey: ["forecast-performance-history", selectedAssetId],
  });

  const latestSignal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["forecast-latest-signal", selectedAssetId],
  });

  const comparisonRows = useMemo(
    () => comparison.data?.results ?? [],
    [comparison.data?.results],
  );
  const performanceRows = useMemo(
    () => performance.data?.runs ?? [],
    [performance.data?.runs],
  );
  const latestPerformance = performanceRows[0];
  const signalMetadata = latestSignal.data?.data?.metadata ?? {};
  const forecastQualityScore = buildForecastQualityScore(status.data);
  const providerLeaderboard = useMemo(
    () => buildProviderLeaderboard(comparisonRows, performanceRows),
    [comparisonRows, performanceRows],
  );
  const recommendedProvider = providerLeaderboard[0];
  const bestComparison = getBestProfitabilityRow(comparisonRows);
  const currentProvider = signalMetadata.forecast_provider ?? signalMetadata.source;
  const currentSignalUsesFallback = currentProvider === "local_saved_forecast";
  const revenueLeakage = Math.abs(Number(latestPerformance?.revenue_delta_eur ?? 0));

  const refetchForecasts = () =>
    Promise.all([
      status.refetch(),
      preview.refetch(),
      comparison.refetch(),
      actualPrices.refetch(),
      forecastActual.refetch(),
      performance.refetch(),
      latestSignal.refetch(),
    ]);

  return (
    <>
      <PageHeading
        description="Measure which forecast source creates the most battery value, how forecast error changes realized economics, and whether the latest signal is using a trusted data source."
        eyebrow="Forecast intelligence"
        title="Forecasts"
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint="/data/update-entsoe"
          label="Update ENTSO-E forecast"
          refetch={refetchForecasts}
          variant="primary"
        />
        <ActionButton
          endpoint="/forecasts/compare-profitability"
          label="Compare forecast profitability"
          refetch={refetchForecasts}
        />
        <ActionButton
          endpoint="/data/update-actual-prices"
          label="Update actual prices"
          refetch={refetchForecasts}
        />
        <ActionButton
          endpoint={`/backtesting/forecast-actual/run?asset_id=${selectedAssetId}`}
          label="Run forecast-vs-actual"
          refetch={refetchForecasts}
        />
      </div>

      {currentSignalUsesFallback ? (
        <div className="mb-6">
          <ErrorState message="Latest signal used a local saved forecast fallback. Treat the dispatch recommendation as advisory until live or validated forecast data is available." />
        </div>
      ) : null}

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={forecastQualityScore >= 80 ? "emerald" : forecastQualityScore >= 60 ? "amber" : "red"}
          label="Forecast quality score"
          value={`${forecastQualityScore}/100`}
          helper={`${status.data?.valid_row_count ?? "-"} valid row(s), ${status.data?.duplicate_timestamps ?? "-"} duplicate timestamp(s)`}
        />
        <KpiCard
          accent="emerald"
          label="Recommended source"
          value={recommendedProvider?.forecast_provider ?? bestComparison?.forecast_provider ?? "-"}
          helper={
            recommendedProvider
              ? `${formatCurrency(recommendedProvider.total_pnl_eur)} modelled PnL`
              : "Run comparison to rank providers"
          }
        />
        <KpiCard
          accent={latestPerformance ? "blue" : "amber"}
          label="Forecast error"
          value={
            latestPerformance
              ? `${formatNumber(latestPerformance.mae_eur_per_mwh, 2)} MAE`
              : "Not tested"
          }
          helper={
            latestPerformance
              ? `${formatNumber(latestPerformance.rmse_eur_per_mwh, 2)} RMSE`
              : "Actual prices needed"
          }
        />
        <KpiCard
          accent={revenueLeakage > 0 ? "amber" : "emerald"}
          label="Revenue leakage"
          value={latestPerformance ? formatCurrency(revenueLeakage) : "-"}
          helper="Absolute forecast-vs-real PnL delta"
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Current signal source"
          value={currentProvider ?? "-"}
          helper={signalMetadata.forecast_model ?? "No signal metadata"}
          accent={currentSignalUsesFallback ? "amber" : "blue"}
        />
        <KpiCard
          label="Actual prices"
          value={String(actualPrices.data?.status ?? "-")}
          helper={actualPrices.data?.last_timestamp ?? "No actual price file"}
        />
        <KpiCard
          label="Predicted PnL"
          value={formatCurrency(latestPerformance?.predicted_pnl_eur)}
          helper="From forecast-based dispatch"
          accent="blue"
        />
        <KpiCard
          label="Realized PnL"
          value={formatCurrency(latestPerformance?.realized_pnl_eur)}
          helper="From actual price replay"
          accent="emerald"
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(420px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone="blue">{providerLeaderboard.length} source(s)</StatusPill>}
          title="Forecast provider leaderboard"
        >
          <DataTable
            columns={[
              "forecast_provider",
              "total_pnl_eur",
              "profit_per_mw_day",
              "mae_eur_per_mwh",
              "revenue_delta_eur",
              "trust_score",
              "status",
            ]}
            rows={providerLeaderboard}
          />
          {providerLeaderboard.length ? (
            <div className="mt-5">
              <BarComparisonChart
                data={providerLeaderboard}
                xKey="forecast_provider"
                yKey="total_pnl_eur"
              />
            </div>
          ) : null}
        </SectionCard>

        <SectionCard title="Commercial forecast decision">
          <div className="space-y-3">
            <DecisionRow
              label="Use for dispatch"
              tone={recommendedProvider ? "emerald" : "amber"}
              value={recommendedProvider?.forecast_provider ?? "Run comparison"}
            />
            <DecisionRow
              label="Current signal source"
              tone={currentSignalUsesFallback ? "amber" : "blue"}
              value={currentProvider ?? "-"}
            />
            <DecisionRow
              label="Trust basis"
              tone={latestPerformance ? "blue" : "amber"}
              value={
                latestPerformance
                  ? "Actual-price backtest available"
                  : "No actual-price backtest yet"
              }
            />
            <DecisionRow
              label="Business warning"
              tone={currentSignalUsesFallback ? "amber" : "emerald"}
              value={
                currentSignalUsesFallback
                  ? "Fallback forecast used"
                  : "No fallback warning"
              }
            />
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Forecast performance history">
          <DataTable
            columns={[
              "target_date",
              "forecast_provider",
              "mae_eur_per_mwh",
              "rmse_eur_per_mwh",
              "bias_eur_per_mwh",
              "predicted_pnl_eur",
              "realized_pnl_eur",
              "revenue_delta_eur",
            ]}
            rows={formatPerformanceRows(performanceRows)}
          />
          {performanceRows.length ? (
            <div className="mt-5">
              <BarComparisonChart
                data={performanceRows}
                xKey="target_date"
                yKey="revenue_delta_eur"
              />
            </div>
          ) : null}
        </SectionCard>

        <SectionCard title="Forecast preview">
          <DataTable
            columns={[
              "timestamp",
              "forecast_price",
              "forecast_provider",
              "forecast_model",
            ]}
            rows={preview.data?.preview ?? []}
          />
        </SectionCard>
      </div>
    </>
  );
}

function buildForecastQualityScore(status?: ForecastStatusResponse) {
  if (!status || status.status !== "ok") {
    return 0;
  }

  const rowCount = Number(status.row_count ?? 0);
  const validRows = Number(status.valid_row_count ?? 0);
  const invalidRows = Math.max(rowCount - validRows, 0);
  const duplicatePenalty = Number(status.duplicate_timestamps ?? 0) * 8;
  const invalidPenalty = invalidRows * 6;
  const missingPenalty = Number(status.missing_prices ?? 0) * 6;
  const coverageScore = rowCount > 0 ? Math.min((validRows / rowCount) * 100, 100) : 0;
  const score = coverageScore - duplicatePenalty - invalidPenalty - missingPenalty;

  return Math.max(0, Math.min(100, Math.round(score)));
}

function getBestProfitabilityRow(rows: ForecastProfitabilityResult[]) {
  return rows
    .filter((row) => row.status === "ok")
    .toSorted(
      (left, right) =>
        Number(right.total_pnl_eur ?? 0) - Number(left.total_pnl_eur ?? 0),
    )[0];
}

function buildProviderLeaderboard(
  comparisonRows: ForecastProfitabilityResult[],
  performanceRows: ForecastPerformanceRun[],
) {
  const latestPerformanceByProvider = new Map<string, ForecastPerformanceRun>();

  for (const row of performanceRows) {
    const provider = row.forecast_provider ?? "unknown";

    if (!latestPerformanceByProvider.has(provider)) {
      latestPerformanceByProvider.set(provider, row);
    }
  }

  return comparisonRows
    .map((row) => {
      const provider = row.forecast_provider ?? "unknown";
      const performance = latestPerformanceByProvider.get(provider);
      const totalPnl = Number(row.total_pnl_eur ?? 0);
      const mae = Number(performance?.mae_eur_per_mwh ?? 0);
      const revenueDelta = Number(performance?.revenue_delta_eur ?? 0);

      return {
        forecast_provider: provider,
        mae_eur_per_mwh: performance?.mae_eur_per_mwh,
        profit_per_mw_day: row.profit_per_mw_day,
        revenue_delta_eur: performance?.revenue_delta_eur,
        status: row.status,
        total_pnl_eur: row.total_pnl_eur,
        trust_score: calculateTrustScore(totalPnl, mae, revenueDelta, row.status),
      };
    })
    .toSorted((left, right) => {
      if (Number(right.trust_score) !== Number(left.trust_score)) {
        return Number(right.trust_score) - Number(left.trust_score);
      }

      return Number(right.total_pnl_eur ?? 0) - Number(left.total_pnl_eur ?? 0);
    });
}

function calculateTrustScore(
  totalPnl: number,
  mae: number,
  revenueDelta: number,
  status?: string,
) {
  if (status !== "ok") {
    return 0;
  }

  let score = 70;

  if (totalPnl > 0) {
    score += 15;
  }

  if (mae > 0) {
    score -= Math.min(mae, 30);
  }

  if (revenueDelta) {
    score -= Math.min(Math.abs(revenueDelta) / 250, 20);
  }

  return Math.max(0, Math.min(100, Math.round(score)));
}

function formatPerformanceRows(rows: ForecastPerformanceRun[]): TableRow[] {
  return rows.map((row) => ({
    ...row,
    generated_at: formatDateTime(row.generated_at),
  }));
}

function DecisionRow({
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
