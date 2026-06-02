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
import { formatCurrency } from "@/lib/format";
import type {
  RevenueAllocationResponse,
  RevenueStackResponse,
} from "@/types/api";

export default function RevenuePage() {
  const { selectedAssetId } = useAssetContext();

  const stack = useQuery({
    queryFn: () =>
      apiGet<RevenueStackResponse>(
        `/assets/${selectedAssetId}/revenue-stack/latest`,
      ),
    queryKey: ["revenue-stack", selectedAssetId],
  });

  const allocation = useQuery({
    queryFn: () =>
      apiGet<RevenueAllocationResponse>(
        `/assets/${selectedAssetId}/revenue-stack/allocation/latest`,
      ),
    queryKey: ["revenue-allocation", selectedAssetId],
  });

  const rows = stack.data?.results ?? [];
  const allocationRows = allocation.data?.results ?? [];
  const totalRevenue = rows.reduce(
    (sum, row) => sum + Number(row.revenue_eur ?? row.total_revenue_eur ?? 0),
    0,
  );

  return (
    <>
      <PageHeading
        description="Model stacked merchant revenue, ancillary options, grid fee assumptions, opportunity conflicts, and portfolio allocation."
        eyebrow="Commercial optimizer"
        title="Revenue stack"
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/revenue-stack/run`}
          label="Run revenue stack"
          refetch={() => stack.refetch()}
          variant="primary"
        />
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/revenue-stack/allocate`}
          label="Run revenue allocation"
          refetch={() => allocation.refetch()}
        />
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard accent="emerald" label="Modelled revenue" value={formatCurrency(totalRevenue)} />
        <KpiCard label="Revenue products" value={rows.length} />
        <KpiCard label="Allocation status" value={allocation.data?.status ?? "-"} />
        <KpiCard accent="blue" label="Asset" value={selectedAssetId} />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard title="Revenue product results">
          <DataTable
            columns={[
              "market",
              "revenue_eur",
              "risk_adjusted_revenue_eur",
              "availability_hours",
              "status",
            ]}
            rows={rows}
          />
          {rows.length ? (
            <div className="mt-5">
              <BarComparisonChart data={rows} xKey="market" yKey="revenue_eur" />
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Revenue allocation"
        >
          <DataTable
            columns={["market", "allocated_capacity_mw", "expected_revenue_eur", "risk_note"]}
            rows={allocationRows}
          />
        </SectionCard>
      </div>
    </>
  );
}
