import { ActionButton } from "@/components/action-button";
import { BarComparisonChart } from "@/components/charts/bar-comparison-chart";
import { StrategyRecommendation } from "@/components/cockpit/strategy-recommendation";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency } from "@/lib/format";
import type {
  AncillaryEligibilityResponse,
  BusinessDecisionResponse,
  EegComplianceResponse,
  HedgingRevenueResponse,
  SignalMetadata,
  SignalSummary,
  TableRow,
} from "@/types/api";

export function RevenueStackPanel({
  ancillary,
  blockedRows,
  eligibleRows,
  rows,
  warningRows,
}: {
  ancillary?: AncillaryEligibilityResponse;
  blockedRows: TableRow[];
  eligibleRows: TableRow[];
  rows: TableRow[];
  warningRows: TableRow[];
}) {
  const rankedRows = rows
    .toSorted(
      (left, right) =>
        Number(right.estimated_revenue_eur ?? 0) -
        Number(left.estimated_revenue_eur ?? 0),
    )
    .slice(0, 8);
  const blockerRows = uniqueRowsByProduct([...blockedRows, ...warningRows]).slice(0, 4);

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
      <SectionCard
        action={<StatusPill tone="blue">{rows.length} product(s)</StatusPill>}
        title="Automated revenue ranking"
      >
        <DataTable
          columns={[
            "product_id",
            "estimated_revenue_eur",
            "eligibility_status",
            "automation_fit",
            "status",
          ]}
          rows={rankedRows}
        />
        {rankedRows.length ? (
          <div className="mt-5">
            <BarComparisonChart data={rankedRows} xKey="product_id" yKey="estimated_revenue_eur" />
          </div>
        ) : null}
      </SectionCard>
      <SectionCard title="Market stack summary">
        <div className="space-y-3">
          <CommercialRow label="Eligible products" tone="emerald" value={eligibleRows.length} />
          <CommercialRow label="Blocked products" tone={blockedRows.length ? "amber" : "emerald"} value={blockedRows.length} />
          <CommercialRow label="Review warnings" tone={warningRows.length ? "amber" : "emerald"} value={warningRows.length} />
          <CommercialRow label="Ancillary eligible" tone={ancillary?.eligible ? "emerald" : "amber"} value={ancillary?.eligible ? "yes" : ancillary?.reason ?? "not yet"} />
        </div>
        <div className="mt-4">
          <DataTable
            columns={["product_id", "automation_fit", "blocking_reasons"]}
            rows={blockerRows}
          />
        </div>
      </SectionCard>
    </div>
  );
}

export function RevenueAllocationPanel({
  allocationRows,
  metadata,
  signalSummary,
}: {
  allocationRows: TableRow[];
  metadata: SignalMetadata;
  signalSummary: SignalSummary;
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
      <SectionCard title="Revenue allocation">
        <DataTable
          columns={["market", "allocated_capacity_mw", "expected_revenue_eur", "risk_note"]}
          rows={allocationRows}
        />
      </SectionCard>
      <SectionCard title="Allocation economics">
        <div className="space-y-3">
          <CommercialRow label="Allocated markets" tone="blue" value={allocationRows.length} />
          <CommercialRow label="Expected allocation revenue" tone="emerald" value={formatCurrency(sumAllocationRevenue(allocationRows))} />
          <CommercialRow label="Signal PnL" tone="blue" value={formatCurrency(signalSummary.total_pnl_eur)} />
          <CommercialRow label="Forecast provider" tone="slate" value={metadata.forecast_provider ?? metadata.source ?? "-"} />
        </div>
      </SectionCard>
    </div>
  );
}

export function RevenueConstraintsPanel({
  ancillary,
  blockedRows,
  eeg,
  warningRows,
}: {
  ancillary?: AncillaryEligibilityResponse;
  blockedRows: TableRow[];
  eeg?: EegComplianceResponse;
  warningRows: TableRow[];
}) {
  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-4">
        <KpiCard label="Blocked products" value={blockedRows.length} accent={blockedRows.length ? "amber" : "emerald"} />
        <KpiCard label="Review warnings" value={warningRows.length} accent={warningRows.length ? "amber" : "emerald"} />
        <KpiCard label="EEG status" value={eeg?.eeg_eligible ? "Eligible" : eeg?.status ?? "-"} accent={eeg?.eeg_eligible ? "emerald" : "amber"} />
        <KpiCard label="Ancillary" value={ancillary?.eligible ? "Eligible" : "Review"} accent={ancillary?.eligible ? "emerald" : "amber"} />
      </div>
      <SectionCard title="Blocked and review products">
        <DataTable
          columns={[
            "product_id",
            "eligibility_status",
            "status",
            "missing_inputs",
            "blocking_reasons",
            "review_warnings",
          ]}
          rows={[...blockedRows, ...warningRows]}
        />
      </SectionCard>
    </div>
  );
}

export function RevenueEconomicsPanel({
  allocationRows,
  ancillary,
  businessDecision,
  eeg,
  hedgeSummary,
  metadata,
  revenueRows,
  signalSummary,
  totalRevenue,
}: {
  allocationRows: TableRow[];
  ancillary?: AncillaryEligibilityResponse;
  businessDecision?: BusinessDecisionResponse["decision"];
  eeg?: EegComplianceResponse;
  hedgeSummary: NonNullable<HedgingRevenueResponse["summary"]>;
  metadata: SignalMetadata;
  revenueRows: TableRow[];
  signalSummary: SignalSummary;
  totalRevenue: number;
}) {
  return (
    <div className="space-y-5">
      <StrategyRecommendation
        allocationRows={allocationRows}
        ancillary={ancillary}
        businessDecision={businessDecision}
        eeg={eeg}
        hedgingSummary={hedgeSummary}
        metadata={metadata}
        revenueRows={revenueRows}
        summary={signalSummary}
      />
      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard title="Owner economics">
          <div className="space-y-3">
            <CommercialRow label="Modelled stack revenue" tone="emerald" value={formatCurrency(totalRevenue)} />
            <CommercialRow label="Merchant dispatch PnL" tone="blue" value={formatCurrency(signalSummary.total_pnl_eur)} />
            <CommercialRow label="Hedged revenue" tone="emerald" value={formatCurrency(hedgeSummary.hedged_revenue_eur)} />
            <CommercialRow label="Residual exposure" tone="amber" value={formatCurrency(hedgeSummary.residual_exposure_eur)} />
          </div>
        </SectionCard>
        <SectionCard title="Business decision basis">
          <DataTable
            columns={["field", "value"]}
            rows={[
              { field: "Recommendation", value: businessDecision?.recommendation_title ?? "-" },
              { field: "Readiness", value: businessDecision?.readiness ?? "-" },
              { field: "Forecast provider", value: metadata.forecast_provider ?? metadata.source ?? "-" },
              { field: "Forecast model", value: metadata.forecast_model ?? "-" },
            ]}
          />
        </SectionCard>
      </div>
    </div>
  );
}

export function RevenueRunControlsPanel({
  refetchAllocation,
  refetchStack,
  selectedAssetId,
}: {
  refetchAllocation: () => Promise<unknown>;
  refetchStack: () => Promise<unknown>;
  selectedAssetId: string;
}) {
  return (
    <SectionCard title="Run controls">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/revenue-stack/run`}
          label="Run revenue stack"
          refetch={refetchStack}
          variant="primary"
        />
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/revenue-stack/allocate`}
          label="Run allocation"
          refetch={refetchAllocation}
        />
      </div>
    </SectionCard>
  );
}

function CommercialRow({
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

function sumAllocationRevenue(rows: TableRow[]) {
  return rows.reduce(
    (sum, row) => sum + Number(row.expected_revenue_eur ?? 0),
    0,
  );
}

function uniqueRowsByProduct(rows: TableRow[]) {
  const seen = new Set<string>();

  return rows.filter((row) => {
    const key = `${row.product_id ?? row.market ?? "-"}:${row.automation_fit ?? row.status ?? "-"}`;

    if (seen.has(key)) {
      return false;
    }

    seen.add(key);
    return true;
  });
}
