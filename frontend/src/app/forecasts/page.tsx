"use client";

import { type ReactNode, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ErrorState } from "@/components/error-state";
import {
  ForecastConfidencePanel,
  ForecastDataQualityPanel,
  ForecastMarketPanel,
  ForecastPerformancePanel,
  ForecastRunControlsPanel,
} from "@/components/forecasts/forecast-workbench-panels";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type {
  ActualPriceStatusResponse,
  Asset,
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

const forecastTabs = [
  {
    id: "market",
    label: "Source Trust",
    helper: "Which forecast source should drive automated trading, and whether it is live, fallback, or stale.",
  },
  {
    id: "performance",
    label: "Backtest Proof",
    helper: "Forecast-vs-actual error, revenue leakage, and backtest history.",
  },
  {
    id: "confidence",
    label: "Trading Confidence",
    helper: "Commercial source selection, trust score, and fallback warnings.",
  },
  {
    id: "data",
    label: "Data Quality",
    helper: "Forecast file health, actual-price readiness, and raw preview records.",
  },
  {
    id: "controls",
    label: "Run Controls",
    helper: "Refresh market data, compare providers, and rerun forecast validation.",
  },
] as const;

type ForecastTabId = (typeof forecastTabs)[number]["id"];

type ForecastPersonaFraming = {
  bridgeTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  fallbackMessage: string;
  eyebrow: string;
  nextActionClear: string;
  nextActionBlocked: string;
  performanceDescription: string;
  performanceTitle: string;
  title: string;
};

export default function ForecastsPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const framing = getForecastPersonaFraming(personaId);
  const [activeTab, setActiveTab] = useState<ForecastTabId>("market");
  const visibleForecastTabs =
    persona.layer === "client"
      ? forecastTabs.filter((tab) => tab.id !== "data" && tab.id !== "controls")
      : forecastTabs;
  const effectiveActiveTab = visibleForecastTabs.some((tab) => tab.id === activeTab)
    ? activeTab
    : "market";

  useEffect(() => {
    const syncTabFromHash = () => {
      const queryTab = new URLSearchParams(window.location.search).get("tab");
      const hashTab = window.location.hash.replace(/^#/, "").split("#")[0];
      const requestedTab = queryTab ?? hashTab;
      const nextTab = forecastTabs.some((tab) => tab.id === requestedTab)
        ? (requestedTab as ForecastTabId)
        : "market";

      setActiveTab(nextTab);
    };

    syncTabFromHash();
    window.addEventListener("popstate", syncTabFromHash);
    window.addEventListener("hashchange", syncTabFromHash);

    return () => {
      window.removeEventListener("popstate", syncTabFromHash);
      window.removeEventListener("hashchange", syncTabFromHash);
    };
  }, []);

  const status = useQuery({
    queryFn: () =>
      apiGet<ForecastStatusResponse>(
        `/assets/${selectedAssetId}/forecast/status`,
      ),
    queryKey: ["asset-forecast-status", selectedAssetId],
  });

  const preview = useQuery({
    queryFn: () =>
      apiGet<ForecastPreviewResponse>(
        `/assets/${selectedAssetId}/forecast/preview`,
      ),
    queryKey: ["asset-forecast-preview", selectedAssetId],
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
  const assetDataProfile = selectedAsset?.data_profile ?? {};
  const signalMetadata = latestSignal.data?.data?.metadata ?? {};
  const forecastQualityScore = buildForecastQualityScore(status.data);
  const backendForecastKpis = normalizeProofKpis(status.data?.forecast_proof?.kpis);
  const visibleForecastRows = status.data?.forecast_proof?.rows ?? [];
  const providerLeaderboard = useMemo(
    () => buildProviderLeaderboard(comparisonRows, performanceRows),
    [comparisonRows, performanceRows],
  );
  const recommendedProvider = providerLeaderboard[0];
  const bestComparison = getBestProfitabilityRow(comparisonRows);
  const currentProvider = signalMetadata.forecast_provider ?? signalMetadata.source;
  const currentSignalUsesFallback = currentProvider === "local_saved_forecast";
  const revenueLeakage = Math.abs(Number(latestPerformance?.revenue_delta_eur ?? 0));
  const forecastBlockers = [
    currentSignalUsesFallback ? "Latest signal used local saved forecast fallback." : null,
    selectedAsset?.data_mode === "production"
      ? null
      : `Selected asset is using ${formatDataMode(selectedAsset?.data_mode)} forecast evidence.`,
    latestPerformance ? null : "Forecast-vs-actual performance is not available yet.",
    actualPrices.data?.status === "ok" ? null : "Actual price evidence is not ready.",
  ].filter(Boolean) as string[];
  const automationLane =
    forecastBlockers.length || forecastQualityScore < 80
      ? "Advisory / supervised"
      : "Automation input";
  const backendConnectionRows = buildForecastBackendConnectionRows({
    actualPriceStatus: actualPrices.data?.status,
    comparisonStatus: comparison.data?.status,
    performanceCount: performance.data?.run_count ?? performanceRows.length,
    previewStatus: preview.data?.status,
    selectedAssetId,
    signalStatus: latestSignal.data?.status,
    statusStatus: status.data?.status,
  });
  const pageHeading =
    effectiveActiveTab === "performance"
      ? {
          description: framing.performanceDescription,
          title: framing.performanceTitle,
        }
      : {
          description: framing.description,
          title: framing.title,
        };

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
        description={pageHeading.description}
        eyebrow={framing.eyebrow}
        title={pageHeading.title}
      />

      {currentSignalUsesFallback ? (
        <div className="mb-6">
          <ErrorState message={framing.fallbackMessage} />
        </div>
      ) : null}

      <DecisionBrief
        blockers={forecastBlockers}
        className="mb-6"
        decision={
          <>
            {recommendedProvider?.forecast_provider ??
              bestComparison?.forecast_provider ??
              currentProvider ??
              "Source pending"}
            <span className="text-slate-500"> / </span>
            {forecastQualityScore >= 80
              ? "tradable"
              : forecastQualityScore >= 60
                ? "supervised"
                : "advisory"}
          </>
        }
        evidence={[
          `${forecastQualityScore}/100 forecast quality score.`,
          latestPerformance
            ? `${formatNumber(latestPerformance.mae_eur_per_mwh, 2)} EUR/MWh MAE on latest performance run.`
            : "No latest performance run is available.",
          recommendedProvider
            ? `${formatCurrency(recommendedProvider.total_pnl_eur)} modelled PnL from recommended source.`
            : "Provider ranking needs a comparison run.",
          `${selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId} uses ${String(assetDataProfile.label ?? "selected asset forecast profile")}.`,
        ]}
        eyebrow={framing.decisionEyebrow}
        nextAction={
          forecastBlockers.length
            ? framing.nextActionBlocked
            : framing.nextActionClear
        }
        title={framing.decisionTitle}
        tone={
          forecastBlockers.length
            ? "amber"
            : forecastQualityScore >= 80
              ? "emerald"
              : "blue"
        }
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <KpiCard
          accent={forecastQualityScore >= 80 ? "emerald" : forecastQualityScore >= 60 ? "amber" : "red"}
          label="Forecast quality score"
          value={`${forecastQualityScore}/100`}
          helper={`${status.data?.valid_row_count ?? "-"} valid row(s), ${status.data?.duplicate_timestamps ?? "-"} duplicate timestamp(s)`}
        />
        <KpiCard
          accent={selectedAsset?.data_mode === "production" ? "emerald" : "blue"}
          label="Selected asset profile"
          value={formatAssetType(selectedAsset)}
          helper={String(assetDataProfile.market_data_mode ?? selectedAsset?.data_source ?? "source pending")}
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

      <WorkspaceTabs
        activeTab={effectiveActiveTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          window.history.replaceState(
            null,
            "",
            tab === "market" ? "/forecasts" : `/forecasts?tab=${tab}`,
          );
          window.dispatchEvent(new Event("locationchange"));
        }}
        tabs={visibleForecastTabs}
      />

      {effectiveActiveTab === "market" ? (
        <div className="space-y-5">
          <ForecastMarketPanel
            actualPrices={actualPrices.data}
            asset={selectedAsset}
            currentProvider={currentProvider}
            currentSignalUsesFallback={currentSignalUsesFallback}
            providerLeaderboard={providerLeaderboard}
            signalMetadata={signalMetadata}
          />
          <SectionCard
            action={<StatusPill tone={selectedAsset?.data_mode === "production" ? "emerald" : "blue"}>{formatDataMode(selectedAsset?.data_mode)}</StatusPill>}
            title="Selected asset forecast profile"
          >
            <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <DataTable
                columns={["field", "value"]}
                rows={buildSelectedAssetForecastProfileRows({
                  asset: selectedAsset,
                  forecastFile: status.data?.forecast_file,
                })}
              />
              <DataTable
                columns={["forecast_context", "value"]}
                rows={buildForecastContextRows(preview.data)}
              />
            </div>
          </SectionCard>
          <SectionCard
            action={<StatusPill tone="blue">{formatDataMode(selectedAsset?.data_mode)} forecast proof</StatusPill>}
            title="Asset forecast proof"
          >
            <div className="mb-4 grid gap-4 md:grid-cols-3">
              {backendForecastKpis.map((kpi) => (
                <KpiCard
                  accent={kpi.accent}
                  helper={kpi.helper}
                  key={kpi.label}
                  label={kpi.label}
                  value={kpi.value}
                />
              ))}
            </div>
            <DataTable
              columns={["forecast_driver", "mock_evidence", "investor_meaning", "production_upgrade"]}
              rows={visibleForecastRows}
            />
          </SectionCard>
        </div>
      ) : null}

      {effectiveActiveTab === "performance" ? (
        <ForecastPerformancePanel
          latestPerformance={latestPerformance}
          performanceRows={performanceRows}
        />
      ) : null}

      {effectiveActiveTab === "confidence" ? (
        <div className="space-y-5">
          <SectionCard
            action={
              <StatusPill tone={automationLane === "Automation input" ? "emerald" : "amber"}>
                {automationLane}
              </StatusPill>
            }
            title={framing.bridgeTitle}
          >
            <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <DataTable
                columns={["decision_input", "value"]}
                rows={[
                  {
                    decision_input: "Current source",
                    value: currentProvider ?? "source pending",
                  },
                  {
                    decision_input: "Recommended source",
                    value:
                      recommendedProvider?.forecast_provider ??
                      bestComparison?.forecast_provider ??
                      "run provider comparison",
                  },
                  {
                    decision_input: "Trading lane",
                    value: automationLane,
                  },
                  {
                    decision_input: "Reason to hold back",
                    value: forecastBlockers[0] ?? "No blocking forecast issue.",
                  },
                ]}
              />
              <DataTable
                columns={["capability", "backend_route", "status", "business_value"]}
                rows={backendConnectionRows}
              />
            </div>
          </SectionCard>
          <ForecastConfidencePanel
            currentSignalUsesFallback={currentSignalUsesFallback}
            latestPerformance={latestPerformance}
            providerLeaderboard={providerLeaderboard}
            recommendedProvider={recommendedProvider}
          />
        </div>
      ) : null}

      {effectiveActiveTab === "data" ? (
        <ForecastDataQualityPanel
          preview={preview.data}
          status={status.data}
        />
      ) : null}

      {effectiveActiveTab === "controls" ? (
        <ForecastRunControlsPanel
          refetchForecasts={refetchForecasts}
          selectedAssetId={selectedAssetId}
        />
      ) : null}
    </>
  );
}

function getForecastPersonaFraming(personaId: PersonaId): ForecastPersonaFraming {
  const defaults: ForecastPersonaFraming = {
    bridgeTitle: "Forecast trust bridge",
    decisionEyebrow: "Forecast decision",
    decisionTitle: "Forecast-to-trade decision",
    description:
      "Decide whether a forecast source is reliable enough to drive automated bid sizing. The page links source quality, actual-price backtests, revenue leakage, and fallback risk before a signal can move toward live trading.",
    fallbackMessage:
      "Latest signal used a local saved forecast fallback. Treat the dispatch recommendation as advisory until live or validated forecast data is available.",
    eyebrow: "Forecast intelligence",
    nextActionBlocked:
      "Keep trading in advisory or supervised mode until forecast evidence is current.",
    nextActionClear:
      "Use this source as the trading confidence input for strategy intent and bid sizing.",
    performanceDescription:
      "Review forecast-vs-actual backtests, model error, realized revenue leakage, and proof gaps before a forecast model is trusted for automated bid sizing.",
    performanceTitle: "Model performance",
    title: "Forecast trust",
  };

  const frames: Partial<Record<PersonaId, ForecastPersonaFraming>> = {
    project_developer: {
      bridgeTitle: "Forecast-to-development bridge",
      decisionEyebrow: "Development forecast decision",
      decisionTitle: "Are forecast assumptions credible enough for scenarios?",
      description:
        "Show whether forecast evidence is strong enough to support development scenarios, market eligibility assumptions, and pre-COD commercial planning.",
      fallbackMessage:
        "The latest signal used a saved forecast fallback. Treat scenario and development assumptions as provisional until validated forecast evidence exists.",
      eyebrow: "Development readiness",
      nextActionBlocked:
        "Keep development scenarios provisional until forecast evidence and actual-price proof are refreshed.",
      nextActionClear:
        "Use this forecast as a credible input for development scenarios and revenue assumptions.",
      performanceDescription:
        "Review forecast error and revenue impact so development assumptions do not rely on an untested market view.",
      performanceTitle: "Development forecast proof",
      title: "Forecast assumptions",
    },
    trading_desk: {
      bridgeTitle: "Forecast-to-desk bridge",
      decisionEyebrow: "Desk forecast decision",
      decisionTitle: "Can the desk trade from this forecast?",
      description:
        "Decide whether the current forecast source is reliable enough for bid sizing, supervised execution, and intraday trading decisions.",
      fallbackMessage:
        "Latest signal used a saved forecast fallback. Keep desk action advisory or paper-only until live or validated forecast data is available.",
      eyebrow: "Trading desk",
      nextActionBlocked:
        "Keep bids advisory or supervised until forecast proof, actual prices, and source quality are current.",
      nextActionClear:
        "Use this forecast source as the desk input for bid sizing and strategy intent.",
      performanceDescription:
        "Review forecast error, revenue leakage, and provider ranking before using the model for desk execution.",
      performanceTitle: "Desk forecast performance",
      title: "Tradable forecast trust",
    },
    forecast_quant: {
      bridgeTitle: "Model quality bridge",
      decisionEyebrow: "Model quality decision",
      decisionTitle: "Is this forecast model good enough for automation?",
      description:
        "Evaluate source quality, provider ranking, forecast-vs-actual performance, revenue leakage, and raw data health before model output drives automation.",
      fallbackMessage:
        "Latest signal used a saved forecast fallback. Diagnose provider freshness and data health before treating the model as production evidence.",
      eyebrow: "Model quality OS",
      nextActionBlocked:
        "Refresh validation, actual-price evidence, or provider comparison before model output influences automation limits.",
      nextActionClear:
        "Use this source as the validated model input for signal generation and automation evidence.",
      performanceDescription:
        "Review forecast-vs-actual backtests, model error, revenue leakage, provider ranking, and proof gaps.",
      performanceTitle: "Model validation evidence",
      title: "Forecast model trust",
    },
    revenue_analyst: {
      bridgeTitle: "Forecast-to-revenue bridge",
      decisionEyebrow: "Revenue forecast decision",
      decisionTitle: "Does forecast error change the revenue case?",
      description:
        "Connect forecast quality, provider choice, backtest proof, and revenue leakage to revenue assurance, hedging, and scenario assumptions.",
      fallbackMessage:
        "Latest signal used a saved forecast fallback. Treat revenue assumptions as provisional until forecast evidence is current.",
      eyebrow: "Commercial analytics OS",
      nextActionBlocked:
        "Hold revenue, hedge, or allocation assumptions until forecast performance and actual-price evidence are refreshed.",
      nextActionClear:
        "Use this forecast evidence to support revenue assurance, hedging, and scenario analysis.",
      performanceDescription:
        "Review model error and revenue leakage so commercial assumptions reflect actual forecast risk.",
      performanceTitle: "Revenue forecast proof",
      title: "Forecast-backed revenue trust",
    },
    executive: {
      bridgeTitle: "Forecast confidence bridge",
      decisionEyebrow: "Executive confidence decision",
      decisionTitle: "Does forecast risk affect commercial confidence?",
      description:
        "Summarize whether forecast quality, source reliability, backtest proof, and revenue leakage create a material risk to the commercial story.",
      fallbackMessage:
        "Latest signal used a saved forecast fallback. Treat portfolio signal confidence as limited until validated forecast evidence exists.",
      eyebrow: "Executive view",
      nextActionBlocked:
        "Keep the commercial story qualified until forecast evidence is current and revenue impact is understood.",
      nextActionClear:
        "Use this forecast confidence summary to support portfolio and revenue decisions.",
      performanceDescription:
        "Review forecast error and revenue impact at management level before trusting model-driven value.",
      performanceTitle: "Forecast confidence evidence",
      title: "Forecast confidence",
    },
  };

  return frames[personaId] ?? defaults;
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

function buildSelectedAssetForecastProfileRows({
  asset,
  forecastFile,
}: {
  asset?: Asset;
  forecastFile?: string;
}) {
  const profile = asset?.data_profile ?? {};

  return [
    {
      field: "Selected asset",
      value: asset?.asset_name ?? asset?.site_name ?? asset?.asset_id ?? "-",
    },
    {
      field: "Asset type",
      value: formatAssetType(asset),
    },
    {
      field: "Mock profile",
      value: profile.label ?? profile.profile_id ?? "-",
    },
    {
      field: "Forecast file",
      value: forecastFile ?? profile.forecast_source ?? asset?.forecast_file ?? "-",
    },
    {
      field: "Data mode",
      value: formatDataMode(asset?.data_mode),
    },
    {
      field: "Investor meaning",
      value:
        profile.description ??
        "Selected-asset forecast evidence is not described yet.",
    },
  ];
}

function buildForecastContextRows(preview?: ForecastPreviewResponse) {
  const rows = preview?.preview ?? [];
  const firstRow = rows[0] ?? {};
  const contextColumns = (preview?.columns ?? []).filter(
    (column) =>
      ![
        "timestamp",
        "forecast_price",
        "forecast_provider",
        "forecast_model",
        "market_profile_id",
        "market_time_unit_minutes",
      ].includes(column),
  );

  if (!contextColumns.length) {
    return [
      {
        forecast_context: "Profile context",
        value: "No extra mock context columns are available for this forecast.",
      },
    ];
  }

  return contextColumns.map((column) => ({
    forecast_context: column,
    value: firstRow[column] ?? "available in preview rows",
  }));
}

type ForecastProofKpi = {
  accent: "amber" | "blue" | "emerald" | "red" | "slate";
  helper: string;
  label: string;
  value: ReactNode;
};

function normalizeProofKpis(rows?: TableRow[]): ForecastProofKpi[] {
  return (rows ?? []).map((row) => ({
    accent: normalizeAccent(row.accent),
    helper: String(row.helper ?? ""),
    label: String(row.label ?? "Evidence"),
    value: normalizeKpiValue(row.value),
  }));
}

function normalizeAccent(value: unknown): ForecastProofKpi["accent"] {
  if (
    value === "amber" ||
    value === "blue" ||
    value === "emerald" ||
    value === "red" ||
    value === "slate"
  ) {
    return value;
  }

  return "slate";
}

function normalizeKpiValue(value: TableRow[string]): React.ReactNode {
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  if (value === null || value === undefined) {
    return "-";
  }

  return JSON.stringify(value);
}

function formatAssetType(asset?: Asset) {
  return formatEnumLabel(asset?.asset_type ?? "grid_scale_battery");
}

function formatDataMode(dataMode?: string) {
  return formatEnumLabel(dataMode ?? "mock");
}

function formatEnumLabel(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function buildForecastBackendConnectionRows({
  actualPriceStatus,
  comparisonStatus,
  performanceCount,
  previewStatus,
  selectedAssetId,
  signalStatus,
  statusStatus,
}: {
  actualPriceStatus?: string;
  comparisonStatus?: string;
  performanceCount: number;
  previewStatus?: string;
  selectedAssetId: string;
  signalStatus?: string;
  statusStatus?: string;
}) {
  return [
    {
      backend_route: "/forecast/status",
      business_value: "Validates forecast file quality before it can drive dispatch.",
      capability: "Forecast quality",
      status: statusStatus ?? "not_loaded",
    },
    {
      backend_route: "/forecasts/compare-profitability/latest",
      business_value: "Ranks forecast providers by modelled trading value.",
      capability: "Provider ranking",
      status: comparisonStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/forecast-performance`,
      business_value: "Stores forecast-vs-actual proof and revenue leakage evidence.",
      capability: "Backtest proof",
      status: `${performanceCount} run(s)`,
    },
    {
      backend_route: "/data/actual-prices/status",
      business_value: "Confirms actual prices exist before trusting model error.",
      capability: "Actual price evidence",
      status: actualPriceStatus ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/signal/latest`,
      business_value: "Shows whether the latest dispatch signal used this forecast source.",
      capability: "Signal linkage",
      status: signalStatus ?? "not_loaded",
    },
    {
      backend_route: "/forecast/preview",
      business_value: "Lets data teams inspect raw forecast rows when quality is disputed.",
      capability: "Raw preview",
      status: previewStatus ?? "not_loaded",
    },
  ];
}
