"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { HedgingRevenueResponse } from "@/types/api";

export default function HedgingPage() {
  const { selectedAssetId } = useAssetContext();

  const hedge = useQuery({
    queryFn: () =>
      apiGet<HedgingRevenueResponse>(
        `/assets/${selectedAssetId}/hedging/revenue`,
      ),
    queryKey: ["hedging-revenue", selectedAssetId],
  });

  const summary = hedge.data?.summary ?? {};
  const contracts = hedge.data?.contracts ?? [];

  return (
    <>
      <PageHeading
        description="Convert volatile merchant battery revenue into bankable revenue profiles using floors, collars, revenue shares, and availability contracts."
        eyebrow="Revenue certainty"
        title="Hedging"
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard label="Contracts" value={contracts.length} />
        <KpiCard accent="emerald" label="Hedged revenue" value={formatCurrency(summary.hedged_revenue_eur)} />
        <KpiCard label="Merchant upside" value={formatCurrency(summary.merchant_upside_eur)} />
        <KpiCard accent="amber" label="Residual exposure" value={formatCurrency(summary.residual_exposure_eur)} />
      </div>

      <SectionCard title="Hedge contract options">
        <DataTable
          columns={[
            "contract_name",
            "contract_type",
            "floor_eur",
            "cap_eur",
            "revenue_share_percent",
            "hedged_revenue_eur",
          ]}
          rows={contracts}
        />
      </SectionCard>
    </>
  );
}
