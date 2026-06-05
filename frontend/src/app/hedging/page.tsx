"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
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
  const downsideProtection = bestContract?.downside_protection_eur_per_month;
  const recommendedContractName =
    bestContract?.name ?? bestContract?.contract_name ?? "contract pending";
  const recommendedRows = bestContract
    ? [
        {
          field: "Recommended contract",
          value: recommendedContractName,
        },
        {
          field: "Owner revenue",
          value: formatCurrency(bestContract.expected_owner_revenue_eur_per_month),
        },
        {
          field: "Downside protection",
          value: formatCurrency(bestContract.downside_protection_eur_per_month),
        },
        {
          field: "Availability requirement",
          value: `${bestContract.availability_requirement_percent ?? "-"}%`,
        },
      ]
    : [];

  return (
    <>
      <PageHeading
        description="Convert volatile merchant battery revenue into bankable revenue profiles using floors, collars, revenue shares, and availability contracts."
        eyebrow="Revenue certainty"
        title="Hedging"
      />

      <DecisionBrief
        blockers={
          contracts.length
            ? []
            : ["No hedge contract options are available for commercial packaging."]
        }
        className="mb-6"
        decision={
          <>
            {recommendedContractName}
            <span className="text-slate-500"> / </span>
            {formatCurrency(hedgedRevenue)}
          </>
        }
        evidence={[
          `${contracts.length} hedge contract option(s) modelled.`,
          `${formatCurrency(downsideProtection)} expected downside protection from the recommended structure.`,
          `${formatCurrency(residualExposure)} merchant revenue is given away under the current best option.`,
        ]}
        eyebrow="Bankability decision"
        nextAction="Use the recommended hedge as the owner-facing commercial offer, then keep merchant automation limits aligned with the availability and upside-sharing terms."
        title="Hedge-to-owner offer"
        tone={contracts.length ? "emerald" : "amber"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard label="Contracts" value={contracts.length} />
        <KpiCard accent="emerald" label="Best owner revenue" value={formatCurrency(hedgedRevenue)} />
        <KpiCard label="Owner upside" value={formatCurrency(merchantUpside)} />
        <KpiCard accent="amber" label="Merchant revenue given away" value={formatCurrency(residualExposure)} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
        <SectionCard title="Recommended owner offer">
          <DataTable columns={["field", "value"]} rows={recommendedRows} />
        </SectionCard>

        <SectionCard title="Hedge contract options">
          <DataTable
            columns={[
              "name",
              "contract_type",
              "expected_owner_revenue_eur_per_month",
              "downside_protection_eur_per_month",
              "upside_share_percent",
              "availability_requirement_percent",
            ]}
            rows={contractRows.slice(0, 6)}
          />
        </SectionCard>
      </div>
    </>
  );
}

function formatContractRow(contract: HedgeContract): TableRow {
  return {
    ...contract,
    name: contract.name ?? contract.contract_name ?? "-",
  };
}
