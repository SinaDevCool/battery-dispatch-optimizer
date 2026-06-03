"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { HedgeContract, HedgingRevenueResponse, TableRow } from "@/types/api";

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
  const bestContract = hedge.data?.best_contract;
  const contractRows = contracts.map(formatContractRow);
  const hedgedRevenue =
    summary.hedged_revenue_eur ??
    bestContract?.expected_owner_revenue_eur_per_month;
  const merchantUpside =
    summary.merchant_upside_eur ??
    bestContract?.owner_upside_eur_per_month;
  const residualExposure =
    summary.residual_exposure_eur ??
    bestContract?.merchant_revenue_given_away_eur_per_month;

  return (
    <>
      <PageHeading
        description="Convert volatile merchant battery revenue into bankable revenue profiles using floors, collars, revenue shares, and availability contracts."
        eyebrow="Revenue certainty"
        title="Hedging"
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard label="Contracts" value={contracts.length} />
        <KpiCard accent="emerald" label="Best owner revenue" value={formatCurrency(hedgedRevenue)} />
        <KpiCard label="Owner upside" value={formatCurrency(merchantUpside)} />
        <KpiCard accent="amber" label="Merchant revenue given away" value={formatCurrency(residualExposure)} />
      </div>

      <SectionCard title="Hedge contract options">
        <DataTable
          columns={[
            "name",
            "contract_type",
            "floor_revenue_eur_per_month",
            "upside_share_percent",
            "expected_owner_revenue_eur_per_month",
            "downside_protection_eur_per_month",
            "availability_requirement_percent",
          ]}
          rows={contractRows}
        />
      </SectionCard>
    </>
  );
}

function formatContractRow(contract: HedgeContract): TableRow {
  return {
    ...contract,
    name: contract.name ?? contract.contract_name ?? "-",
  };
}
