"use client";

import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DispatchChart } from "@/components/charts/dispatch-chart";
import { DataTable } from "@/components/data-table";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { LatestSignalResponse } from "@/types/api";

export default function DispatchPage() {
  const { selectedAssetId } = useAssetContext();

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["dispatch-signal", selectedAssetId],
  });

  const summary = signal.data?.data?.summary ?? {};
  const dispatch = signal.data?.data?.dispatch ?? [];

  return (
    <>
      <PageHeading
        description="Inspect the hourly dispatch schedule, state of charge path, charging windows, discharge windows, and cumulative economics."
        eyebrow="Operational schedule"
        title="Dispatch"
      />

      {signal.error ? <ErrorState message="Could not load latest dispatch signal." /> : null}

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/signal/run-latest`}
          label="Generate latest signal"
          refetch={() => signal.refetch()}
          variant="primary"
        />
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard label="Signal" value={summary.signal ?? "-"} />
        <KpiCard accent="emerald" label="Total PnL" value={formatCurrency(summary.total_pnl_eur)} />
        <KpiCard label="Charge hours" value={summary.charge_hours ?? "-"} />
        <KpiCard label="Discharge hours" value={summary.discharge_hours ?? "-"} />
      </div>

      <SectionCard title="Dispatch analytics">
        {dispatch.length ? <DispatchChart rows={dispatch} /> : <ErrorState message="No dispatch rows found." />}
      </SectionCard>

      <div className="mt-5">
        <SectionCard title="Hourly dispatch schedule">
          <DataTable
            columns={[
              "timestamp",
              "price",
              "action",
              "soc_mwh",
              "grid_energy_mwh",
              "battery_energy_mwh",
              "pnl_eur",
              "total_pnl_eur",
            ]}
            rows={dispatch}
          />
        </SectionCard>
      </div>
    </>
  );
}
