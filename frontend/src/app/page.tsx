"use client";

import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { DispatchChart } from "@/components/charts/dispatch-chart";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/format";
import type {
  EegComplianceResponse,
  HealthResponse,
  LatestSignalResponse,
  RevenueStackResponse,
} from "@/types/api";

export default function OverviewPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();

  const health = useQuery({
    queryFn: () => apiGet<HealthResponse>("/health"),
    queryKey: ["health"],
  });

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["asset-signal-latest", selectedAssetId],
  });

  const revenue = useQuery({
    queryFn: () =>
      apiGet<RevenueStackResponse>(
        `/assets/${selectedAssetId}/revenue-stack/latest`,
      ),
    queryKey: ["revenue-stack-latest", selectedAssetId],
  });

  const eeg = useQuery({
    queryFn: () =>
      apiGet<EegComplianceResponse>(
        `/assets/${selectedAssetId}/eeg-compliance/latest`,
      ),
    queryKey: ["eeg-compliance", selectedAssetId],
  });

  const metadata = signal.data?.data?.metadata ?? {};
  const summary = signal.data?.data?.summary ?? {};
  const dispatch = signal.data?.data?.dispatch ?? [];
  const revenueRows = revenue.data?.results ?? [];

  return (
    <>
      <PageHeading
        description={`A sellable control room for ${selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId}: latest signal, expected economics, regulatory status, and revenue stack in one place.`}
        eyebrow="Operations cockpit"
        title="Portfolio overview"
      />

      {health.error ? (
        <ErrorState message="The FastAPI backend is not reachable. Start it with: python -m uvicorn src.api.main:app --reload --port 8000" />
      ) : null}

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint="/workflow/run-daily"
          label="Run daily workflow"
          refetch={() =>
            Promise.all([signal.refetch(), revenue.refetch(), eeg.refetch()])
          }
          variant="primary"
        />
        <ActionButton
          endpoint="/portfolio/run-daily"
          label="Run portfolio workflow"
          refetch={() =>
            Promise.all([signal.refetch(), revenue.refetch(), eeg.refetch()])
          }
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent="blue"
          helper={String(metadata.forecast_model ?? "-")}
          label="Forecast source"
          value={String(metadata.source ?? "-")}
        />
        <KpiCard
          helper={formatDateTime(metadata.generated_at)}
          label="Target date"
          value={String(metadata.target_date ?? "-")}
        />
        <KpiCard
          accent={summary.signal === "ACTION" ? "emerald" : "amber"}
          helper={String(summary.opportunity_level ?? "-")}
          label="Latest signal"
          value={String(summary.signal ?? "-")}
        />
        <KpiCard
          accent="emerald"
          helper={`${summary.profit_per_mw_day ?? "-"} EUR/MW-day`}
          label="Expected PnL"
          value={formatCurrency(summary.total_pnl_eur)}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.7fr)_minmax(360px,0.8fr)]">
        <SectionCard title="Forecast price, state of charge, and cumulative PnL">
          {dispatch.length ? (
            <DispatchChart rows={dispatch} />
          ) : (
            <ErrorState message="No dispatch schedule is available yet. Run the daily workflow or generate the latest signal." />
          )}
        </SectionCard>

        <SectionCard title="Commercial and regulatory position">
          <div className="space-y-3">
            <SignalRow label="API health" value={health.data?.status ?? "checking"} />
            <SignalRow
              label="EEG compliance"
              value={eeg.data?.status ?? "not available"}
            />
            <SignalRow
              label="Revenue scenarios"
              value={`${revenueRows.length} result(s)`}
            />
            <div className="rounded-lg border border-amber-400/25 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100">
              Germany mode should keep energy origin, EEG eligibility, grid fee
              assumptions, and hedging terms explicit before any dispatch signal
              is treated as executable.
            </div>
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Latest dispatch actions">
          <DataTable
            columns={[
              "timestamp",
              "price",
              "action",
              "soc_mwh",
              "pnl_eur",
              "total_pnl_eur",
            ]}
            rows={dispatch.slice(0, 12)}
          />
        </SectionCard>

        <SectionCard title="Revenue stack snapshot">
          <DataTable
            columns={["market", "revenue_eur", "risk_adjusted_revenue_eur", "status"]}
            rows={revenueRows.slice(0, 8)}
          />
        </SectionCard>
      </div>
    </>
  );
}

function SignalRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3">
      <span className="text-sm text-slate-400">{label}</span>
      <StatusPill tone="slate">{value}</StatusPill>
    </div>
  );
}
