"use client";

import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { StrategyRecommendation } from "@/components/cockpit/strategy-recommendation";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type {
  AncillaryEligibilityResponse,
  BusinessDecisionResponse,
  EegComplianceResponse,
  HedgingRevenueResponse,
  LatestSignalResponse,
  RevenueAllocationResponse,
  RevenueStackResult,
  RevenueStackResponse,
  TableRow,
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

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["revenue-signal-latest", selectedAssetId],
  });

  const hedging = useQuery({
    queryFn: () =>
      apiGet<HedgingRevenueResponse>(
        `/assets/${selectedAssetId}/hedging/revenue`,
      ),
    queryKey: ["revenue-hedging", selectedAssetId],
  });

  const eeg = useQuery({
    queryFn: () =>
      apiGet<EegComplianceResponse>(
        `/assets/${selectedAssetId}/eeg-compliance/latest`,
      ),
    queryKey: ["revenue-eeg", selectedAssetId],
  });

  const ancillary = useQuery({
    queryFn: () =>
      apiGet<AncillaryEligibilityResponse>(
        `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
      ),
    queryKey: ["revenue-ancillary", selectedAssetId],
  });

  const businessDecision = useQuery({
    queryFn: () =>
      apiGet<BusinessDecisionResponse>(
        `/assets/${selectedAssetId}/business-decision/latest`,
      ),
    queryKey: ["revenue-business-decision", selectedAssetId],
  });

  const rows = normalizeRevenueRows(stack.data);
  const allocationRows = allocation.data?.results ?? [];
  const metadata = signal.data?.data?.metadata ?? {};
  const summary = signal.data?.data?.summary ?? {};
  const hedgeSummary = hedging.data?.summary ?? {};
  const totalRevenue =
    stack.data?.total_estimated_revenue_eur ??
    rows.reduce(
      (sum, row) => sum + Number(row.estimated_revenue_eur ?? 0),
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
        <KpiCard label="Revenue products" value={stack.data?.product_count ?? rows.length} />
        <KpiCard label="Allocation status" value={allocation.data?.status ?? "-"} />
        <KpiCard accent="blue" label="Asset" value={selectedAssetId} />
      </div>

      <div className="mb-5">
        <StrategyRecommendation
          allocationRows={allocationRows}
          ancillary={ancillary.data}
          businessDecision={businessDecision.data?.decision}
          eeg={eeg.data}
          hedgingSummary={hedgeSummary}
          metadata={metadata}
          revenueRows={rows}
          summary={summary}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard title="Revenue product results">
          <DataTable
            columns={[
              "product_id",
              "estimated_revenue_eur",
              "eligibility_status",
              "status",
              "missing_inputs",
              "blocking_reasons",
            ]}
            rows={rows}
          />
          {rows.length ? (
            <div className="mt-5">
              <BarComparisonChart data={rows} xKey="product_id" yKey="estimated_revenue_eur" />
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

function normalizeRevenueRows(data?: RevenueStackResponse): TableRow[] {
  const sourceRows = data?.results?.length ? data.results : data?.products ?? [];

  return sourceRows.map((row: RevenueStackResult) => ({
    ...row,
    blocking_reasons: formatIssueList(row.blocking_reasons),
    estimated_revenue_eur: row.estimated_revenue_eur ?? row.revenue_eur ?? row.total_revenue_eur ?? 0,
    missing_inputs: row.missing_inputs?.join(", ") || "-",
    product_id: row.product_id ?? row.market ?? "-",
    review_warnings: formatIssueList(row.review_warnings),
  }));
}

function formatIssueList(value: unknown) {
  if (!Array.isArray(value) || value.length === 0) {
    return "-";
  }

  return value
    .map((item) => {
      if (typeof item === "string") {
        return item;
      }

      if (item && typeof item === "object" && "message" in item) {
        return String((item as { message?: unknown }).message);
      }

      return JSON.stringify(item);
    })
    .join("; ");
}
