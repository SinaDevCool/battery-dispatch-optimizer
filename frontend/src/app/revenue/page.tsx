"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import {
  RevenueAllocationPanel,
  RevenueConstraintsPanel,
  RevenueEconomicsPanel,
  RevenueRunControlsPanel,
  RevenueStackPanel,
} from "@/components/revenue/revenue-workbench-panels";
import { WorkspaceTabs } from "@/components/workspace-tabs";
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

const revenueTabs = [
  {
    id: "stack",
    label: "Market Stack",
    helper: "Tradable products, revenue ranking, eligibility, and product-level blockers.",
  },
  {
    id: "allocation",
    label: "Capacity Allocation",
    helper: "How battery capacity should be assigned across revenue pools.",
  },
  {
    id: "constraints",
    label: "Constraints",
    helper: "Missing inputs, blocked products, EEG status, ancillary readiness, and review warnings.",
  },
  {
    id: "economics",
    label: "Economics",
    helper: "Owner/investor view of merchant value, hedge protection, and recommendation basis.",
  },
  {
    id: "controls",
    label: "Run Controls",
    helper: "Refresh the revenue stack and allocation decision.",
  },
] as const;

type RevenueTabId = (typeof revenueTabs)[number]["id"];

export default function RevenuePage() {
  const { selectedAssetId } = useAssetContext();
  const [activeTab, setActiveTab] = useState<RevenueTabId>("stack");

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
  const eligibleRows = rows.filter((row) => row.eligibility_status === "eligible");
  const blockedRows = rows.filter(
    (row) =>
      row.eligibility_status === "not_eligible" ||
      row.status === "blocked" ||
      row.blocking_reasons !== "-",
  );
  const warningRows = rows.filter((row) => row.review_warnings !== "-");
  const metadata = signal.data?.data?.metadata ?? {};
  const summary = signal.data?.data?.summary ?? {};
  const hedgeSummary = hedging.data?.summary ?? {};
  const totalRevenue =
    stack.data?.total_estimated_revenue_eur ??
    rows.reduce(
      (sum, row) => sum + Number(row.estimated_revenue_eur ?? 0),
      0,
    );
  const bestProduct = rows
    .filter((row) => row.eligibility_status === "eligible")
    .toSorted(
      (left, right) =>
        Number(right.estimated_revenue_eur ?? 0) -
        Number(left.estimated_revenue_eur ?? 0),
    )[0];
  const commercialBlockers = [
    blockedRows.length ? `${blockedRows.length} product(s) are blocked or not eligible.` : null,
    warningRows.length ? `${warningRows.length} product(s) require commercial review.` : null,
    allocationRows.length ? null : "Capacity allocation evidence is not available yet.",
  ].filter(Boolean) as string[];

  return (
    <>
      <PageHeading
        description="Decide which revenue streams are tradable, how capacity should be allocated, what constraints block value, and how the economics look to owners and investors."
        eyebrow="Commercial optimizer"
        title="Revenue stack"
      />

      <DecisionBrief
        blockers={commercialBlockers}
        className="mb-6"
        decision={
          <>
            {formatCurrency(totalRevenue)}
            <span className="text-slate-500"> / </span>
            {bestProduct?.product_id ?? "product pending"}
          </>
        }
        evidence={[
          `${eligibleRows.length}/${stack.data?.product_count ?? rows.length} market product(s) eligible.`,
          bestProduct
            ? `${bestProduct.product_id} is currently the strongest eligible revenue product.`
            : "No eligible product has been ranked yet.",
          businessDecision.data?.decision?.recommendation_status
            ? `Decision status: ${businessDecision.data.decision.recommendation_status}.`
            : "Business decision evidence is pending.",
        ]}
        eyebrow="Commercial decision"
        nextAction={
          commercialBlockers.length
            ? "Resolve product eligibility, allocation, or review blockers before promising automated revenue capture."
            : "Use this revenue stack to guide market allocation and trading strategy intent."
        }
        title="Revenue-to-market decision"
        tone={commercialBlockers.length ? "amber" : "emerald"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard accent="emerald" label="Modelled revenue" value={formatCurrency(totalRevenue)} />
        <KpiCard label="Eligible products" value={`${eligibleRows.length}/${stack.data?.product_count ?? rows.length}`} />
        <KpiCard label="Allocation status" value={allocation.data?.status ?? "-"} />
        <KpiCard accent="blue" label="Asset" value={selectedAssetId} />
      </div>

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={revenueTabs}
      />

      {activeTab === "stack" ? (
        <RevenueStackPanel
          ancillary={ancillary.data}
          blockedRows={blockedRows}
          eligibleRows={eligibleRows}
          rows={rows}
          warningRows={warningRows}
        />
      ) : null}

      {activeTab === "allocation" ? (
        <RevenueAllocationPanel
          allocationRows={allocationRows}
          metadata={metadata}
          signalSummary={summary}
        />
      ) : null}

      {activeTab === "constraints" ? (
        <RevenueConstraintsPanel
          ancillary={ancillary.data}
          blockedRows={blockedRows}
          eeg={eeg.data}
          warningRows={warningRows}
        />
      ) : null}

      {activeTab === "economics" ? (
        <RevenueEconomicsPanel
          allocationRows={allocationRows}
          ancillary={ancillary.data}
          businessDecision={businessDecision.data?.decision}
          eeg={eeg.data}
          hedgeSummary={hedgeSummary}
          metadata={metadata}
          revenueRows={rows}
          signalSummary={summary}
          totalRevenue={totalRevenue}
        />
      ) : null}

      {activeTab === "controls" ? (
        <RevenueRunControlsPanel
          refetchAllocation={() => allocation.refetch()}
          refetchStack={() => stack.refetch()}
          selectedAssetId={selectedAssetId}
        />
      ) : null}
    </>
  );
}

function normalizeRevenueRows(data?: RevenueStackResponse): TableRow[] {
  const sourceRows = data?.results?.length ? data.results : data?.products ?? [];

  return sourceRows.map((row: RevenueStackResult) => ({
    ...row,
    automation_fit: classifyRevenueAutomationFit(row),
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

function classifyRevenueAutomationFit(row: RevenueStackResult) {
  if (row.eligibility_status === "eligible" && row.status === "ok") {
    return "ready for market allocation";
  }

  if (row.eligibility_status === "not_eligible" || row.blocking_reasons?.length) {
    return "blocked from automation";
  }

  if (row.eligibility_status === "review_required" || row.review_warnings?.length) {
    return "needs commercial review";
  }

  return "advisory only";
}
