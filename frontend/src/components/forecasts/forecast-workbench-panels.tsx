import { ActionButton } from "@/components/action-button";
import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  ActualPriceStatusResponse,
  Asset,
  ForecastPerformanceRun,
  ForecastPreviewResponse,
  ForecastStatusResponse,
  SignalMetadata,
  TableRow,
} from "@/types/api";

export function ForecastMarketPanel({
  actualPrices,
  asset,
  currentProvider,
  currentSignalUsesFallback,
  providerLeaderboard,
  signalMetadata,
}: {
  actualPrices?: ActualPriceStatusResponse;
  asset?: Asset;
  currentProvider?: string;
  currentSignalUsesFallback: boolean;
  providerLeaderboard: TableRow[];
  signalMetadata: SignalMetadata;
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(380px,0.8fr)]">
      <ForecastProviderLeaderboard providerLeaderboard={providerLeaderboard} />
      <SectionCard title="Market source status">
        <div className="space-y-3">
          <DecisionRow
            label="Selected asset"
            tone="blue"
            value={asset?.asset_name ?? asset?.site_name ?? asset?.asset_id ?? "-"}
          />
          <DecisionRow
            label="Asset data mode"
            tone={asset?.data_mode === "production" ? "emerald" : "blue"}
            value={formatEnumLabel(asset?.data_mode ?? "mock")}
          />
          <DecisionRow
            label="Current signal source"
            tone={currentSignalUsesFallback ? "amber" : "blue"}
            value={currentProvider ?? "-"}
          />
          <DecisionRow
            label="Forecast model"
            tone="blue"
            value={signalMetadata.forecast_model ?? "No signal metadata"}
          />
          <DecisionRow
            label="Actual prices"
            tone={actualPrices?.status === "ok" ? "emerald" : "amber"}
            value={String(actualPrices?.status ?? "-")}
          />
          <DecisionRow
            label="Actual data through"
            tone="slate"
            value={actualPrices?.last_timestamp ?? "No actual price file"}
          />
        </div>
      </SectionCard>
    </div>
  );
}

export function ForecastPerformancePanel({
  latestPerformance,
  performanceRows,
}: {
  latestPerformance?: ForecastPerformanceRun;
  performanceRows: ForecastPerformanceRun[];
}) {
  const latestRows = performanceRows.slice(0, 8);

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent="blue"
          helper="From forecast-based dispatch"
          label="Predicted PnL"
          value={formatCurrency(latestPerformance?.predicted_pnl_eur)}
        />
        <KpiCard
          accent="emerald"
          helper="From actual price replay"
          label="Realized PnL"
          value={formatCurrency(latestPerformance?.realized_pnl_eur)}
        />
        <KpiCard
          accent={latestPerformance ? "blue" : "amber"}
          helper="EUR/MWh absolute error"
          label="MAE"
          value={formatNumber(latestPerformance?.mae_eur_per_mwh, 2)}
        />
        <KpiCard
          accent="slate"
          helper="Directional forecast error"
          label="Bias"
          value={formatNumber(latestPerformance?.bias_eur_per_mwh, 2)}
        />
      </div>
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
          rows={latestRows}
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
    </div>
  );
}

export function ForecastConfidencePanel({
  currentSignalUsesFallback,
  latestPerformance,
  providerLeaderboard,
  recommendedProvider,
}: {
  currentSignalUsesFallback: boolean;
  latestPerformance?: ForecastPerformanceRun;
  providerLeaderboard: TableRow[];
  recommendedProvider?: TableRow;
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <SectionCard title="Trading confidence decision">
        <div className="space-y-3">
          <DecisionRow
            label="Use for dispatch"
            tone={recommendedProvider ? "emerald" : "amber"}
            value={String(recommendedProvider?.forecast_provider ?? "Run comparison")}
          />
          <DecisionRow
            label="Trust score"
            tone={Number(recommendedProvider?.trust_score ?? 0) >= 75 ? "emerald" : "amber"}
            value={recommendedProvider ? `${String(recommendedProvider.trust_score)}/100` : "-"}
          />
          <DecisionRow
            label="Trust basis"
            tone={latestPerformance ? "blue" : "amber"}
            value={latestPerformance ? "Actual-price backtest available" : "No actual-price backtest yet"}
          />
          <DecisionRow
            label="Business warning"
            tone={currentSignalUsesFallback ? "amber" : "emerald"}
            value={currentSignalUsesFallback ? "Fallback forecast used" : "No fallback warning"}
          />
        </div>
      </SectionCard>
      <ForecastProviderLeaderboard providerLeaderboard={providerLeaderboard} />
    </div>
  );
}

export function ForecastDataQualityPanel({
  preview,
  status,
}: {
  preview?: ForecastPreviewResponse;
  status?: ForecastStatusResponse;
}) {
  const previewRows = (preview?.preview ?? []).slice(0, 16);
  const previewColumns = buildPreviewColumns(preview);

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(340px,0.7fr)_minmax(0,1.3fr)]">
      <SectionCard title="Data quality evidence">
        <div className="space-y-3">
          <DecisionRow label="Forecast rows" tone="blue" value={status?.row_count ?? "-"} />
          <DecisionRow label="Valid rows" tone="emerald" value={status?.valid_row_count ?? "-"} />
          <DecisionRow label="Duplicate timestamps" tone={Number(status?.duplicate_timestamps ?? 0) ? "amber" : "emerald"} value={status?.duplicate_timestamps ?? "-"} />
          <DecisionRow label="Missing prices" tone={Number(status?.missing_prices ?? 0) ? "amber" : "emerald"} value={status?.missing_prices ?? "-"} />
          <DecisionRow label="Negative price hours" tone="blue" value={status?.negative_price_hours ?? "-"} />
        </div>
      </SectionCard>
      <SectionCard title="Forecast preview">
        <DataTable
          columns={previewColumns}
          rows={previewRows}
        />
      </SectionCard>
    </div>
  );
}

function buildPreviewColumns(preview?: ForecastPreviewResponse) {
  const preferredColumns = [
    "timestamp",
    "forecast_price",
    "forecast_solar_mw",
    "site_load_mw",
    "site_peak_limit_mw",
    "site_export_limit_mw",
    "scenario_note",
    "forecast_provider",
    "forecast_model",
  ];
  const availableColumns = new Set(preview?.columns ?? []);
  const selectedColumns = preferredColumns.filter((column) =>
    availableColumns.has(column),
  );

  return selectedColumns.length
    ? selectedColumns
    : ["timestamp", "forecast_price", "forecast_provider", "forecast_model"];
}

export function ForecastRunControlsPanel({
  refetchForecasts,
  selectedAssetId,
}: {
  refetchForecasts: () => Promise<unknown>;
  selectedAssetId: string;
}) {
  return (
    <SectionCard title="Run controls">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <ActionButton
          endpoint="/data/update-entsoe"
          label="Update ENTSO-E forecast"
          refetch={refetchForecasts}
          variant="primary"
        />
        <ActionButton
          endpoint="/forecasts/compare-profitability"
          label="Compare profitability"
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
    </SectionCard>
  );
}

function ForecastProviderLeaderboard({
  providerLeaderboard,
}: {
  providerLeaderboard: TableRow[];
}) {
  const leaderboardRows = providerLeaderboard.slice(0, 5);

  return (
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
        rows={leaderboardRows}
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
  );
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

function formatEnumLabel(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
