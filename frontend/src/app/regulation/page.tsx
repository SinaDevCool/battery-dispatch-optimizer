"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import type {
  AncillaryEligibilityResponse,
  EegComplianceResponse,
  GridFeeSensitivityResponse,
  JsonObject,
  StorageClassificationResponse,
  TableRow,
} from "@/types/api";

export default function RegulationPage() {
  const { selectedAssetId } = useAssetContext();

  const classification = useQuery({
    queryFn: () =>
      apiGet<StorageClassificationResponse>(
        `/assets/${selectedAssetId}/storage-classification`,
      ),
    queryKey: ["reg-storage-classification", selectedAssetId],
  });

  const eeg = useQuery({
    queryFn: () =>
      apiGet<EegComplianceResponse>(
        `/assets/${selectedAssetId}/eeg-compliance/latest`,
      ),
    queryKey: ["reg-eeg", selectedAssetId],
  });

  const gridFees = useQuery({
    queryFn: () =>
      apiGet<GridFeeSensitivityResponse>(
        `/assets/${selectedAssetId}/grid-fees/germany/sensitivity`,
      ),
    queryKey: ["reg-grid-fees", selectedAssetId],
  });

  const ancillary = useQuery({
    queryFn: () =>
      apiGet<AncillaryEligibilityResponse>(
        `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
      ),
    queryKey: ["reg-ancillary", selectedAssetId],
  });

  const gridFeeRows = gridFees.data?.sensitivity?.length
    ? gridFees.data.sensitivity
    : gridFees.data?.scenarios ?? [];
  const ancillaryRows = ancillary.data?.products ?? [];
  const formattedAncillaryRows = formatAncillaryRows(ancillaryRows);
  const blockedAncillaryRows = formattedAncillaryRows.filter(
    (row) =>
      row.eligibility_status === "not_eligible" ||
      row.blocking_reasons !== "-",
  );
  const reviewAncillaryRows = formattedAncillaryRows.filter(
    (row) => row.review_warnings !== "-",
  );
  const automationBlockers = [
    eeg.data && !eeg.data.eeg_eligible
      ? "EEG compliance is not eligible for automatic trading."
      : null,
    eeg.data?.mixed_origin_risk
      ? "Mixed-origin or renewable-support risk needs compliance review."
      : null,
    blockedAncillaryRows.length
      ? `${blockedAncillaryRows.length} ancillary product(s) are blocked.`
      : null,
    reviewAncillaryRows.length
      ? `${reviewAncillaryRows.length} ancillary product(s) require review.`
      : null,
  ].filter(Boolean) as string[];

  return (
    <>
      <PageHeading
        description="Germany-focused regulatory cockpit for storage classification, EEG logic, grid fee exposure, and ancillary service eligibility."
        eyebrow="Germany regulatory layer"
        title="Regulation"
      />

      <DecisionBrief
        blockers={automationBlockers}
        className="mb-6"
        decision={
          <>
            {automationBlockers.length ? "Review before auto-trade" : "Auto-trade eligible"}
            <span className="text-slate-500"> / </span>
            Germany
          </>
        }
        evidence={[
          `Storage classification: ${String(classification.data?.storage_classification ?? classification.data?.storage_mode ?? "-")}.`,
          `EEG status: ${String(eeg.data?.status ?? "-")}.`,
          `${String(ancillary.data?.eligible_product_count ?? ancillary.data?.eligible_products?.length ?? 0)} ancillary product(s) eligible.`,
        ]}
        eyebrow="Regulatory automation gate"
        nextAction={
          automationBlockers.length
            ? "Clear the regulatory blockers before allowing unattended bid submission."
            : "Use this regulatory clearance as a pre-trade automation gate for German market routes."
        }
        title="German eligibility decision"
        tone={automationBlockers.length ? "amber" : "emerald"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard
          label="Storage mode"
          value={String(
            classification.data?.storage_classification ??
              classification.data?.storage_mode ??
              "-",
          )}
        />
        <KpiCard accent="amber" label="EEG status" value={String(eeg.data?.status ?? "-")} />
        <KpiCard
          label="Ancillary eligible"
          value={String(
            ancillary.data?.eligible_product_count ??
              ancillary.data?.eligible_products?.length ??
              "-",
          )}
          helper="Product count"
        />
        <KpiCard accent="blue" label="Country" value="Germany" />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard title="Automation gate summary">
          <DataTable
            columns={["gate", "status", "automation_use"]}
            rows={[
              {
                automation_use: "Select tradable market routes",
                gate: "Storage classification",
                status:
                  classification.data?.storage_classification ??
                  classification.data?.storage_mode ??
                  "-",
              },
              {
                automation_use: "Block unsupported renewable-support logic",
                gate: "EEG compliance",
                status: eeg.data?.eeg_eligible ? "eligible" : eeg.data?.status ?? "-",
              },
              {
                automation_use: "Allow ancillary-market bidding only for cleared products",
                gate: "Ancillary eligibility",
                status: `${ancillary.data?.eligible_product_count ?? ancillary.data?.eligible_products?.length ?? 0} eligible`,
              },
              {
                automation_use: "Apply tariff economics before dispatch approval",
                gate: "Grid fee sensitivity",
                status: `${gridFeeRows.length} scenario(s)`,
              },
            ]}
          />
        </SectionCard>

        <SectionCard title="Storage classification detail">
          <DataTable
            columns={["field", "value"]}
            rows={storageRows(classification.data)}
          />
        </SectionCard>

        <SectionCard title="EEG and green colocation checks">
          <DataTable
            columns={["field", "value"]}
            rows={eegRows(eeg.data)}
          />
        </SectionCard>

        <SectionCard title="Grid fee sensitivity">
          <DataTable
            columns={[
              "grid_fee_scenario",
              "import_grid_fee_eur_per_mwh",
              "capacity_charge_eur_per_mw_year",
              "annualized_grid_fee_cost_eur",
              "description",
            ]}
            rows={gridFeeRows.slice(0, 6)}
          />
        </SectionCard>

        <SectionCard title="Ancillary eligibility">
          <DataTable
            columns={[
              "product_id",
              "eligibility_status",
              "automation_gate",
              "market_requirement",
              "next_action",
            ]}
            rows={formatAncillaryGateRows(formattedAncillaryRows).slice(0, 6)}
          />
        </SectionCard>
      </div>
    </>
  );
}

function storageRows(value?: StorageClassificationResponse): TableRow[] {
  if (!value) {
    return [];
  }

  return objectToRows({
    status: value.status,
    storage_mode: value.storage_mode,
    storage_classification: value.storage_classification,
    market_participation_mode: value.market_participation_mode,
    charges_from_grid: value.charges_from_grid,
    charges_from_renewables: value.charges_from_renewables,
    exports_stored_renewable_power: value.exports_stored_renewable_power,
    uses_eeg_support: value.uses_eeg_support,
    eeg_support_risk: value.eeg_support_risk,
    metering_concept: value.metering_concept,
    warnings: formatList(value.warnings),
  });
}

function eegRows(value?: EegComplianceResponse): TableRow[] {
  if (!value) {
    return [];
  }

  return objectToRows({
    status: value.status,
    eeg_eligible: value.eeg_eligible,
    green_colocation: value.green_colocation,
    mixed_origin_risk: value.mixed_origin_risk,
    eeg_support_risk: value.eeg_support_risk,
    compliance_notes: formatList(value.compliance_notes),
    findings: formatList(value.findings),
    recommended_actions: formatList(value.recommended_actions),
  });
}

function objectToRows(value: JsonObject): TableRow[] {
  return Object.entries(value)
    .filter(([, rowValue]) => rowValue !== undefined)
    .map(([field, rowValue]) => ({
      field,
      value: rowValue,
    }));
}

function formatAncillaryRows(rows: TableRow[]): TableRow[] {
  return rows.map((row) => ({
    ...row,
    blocking_reasons: formatList(row.blocking_reasons),
    review_warnings: formatList(row.review_warnings),
  }));
}

function formatAncillaryGateRows(rows: TableRow[]): TableRow[] {
  return rows.map((row) => {
    const blocked = row.eligibility_status === "not_eligible" || row.blocking_reasons !== "-";
    const review = row.review_warnings !== "-";

    return {
      automation_gate: blocked ? "blocked" : review ? "review" : "eligible",
      eligibility_status: row.eligibility_status ?? "-",
      market_requirement:
        row.name ??
        `${row.minimum_duration_minutes ?? "-"} min / ${row.response_time_seconds ?? "-"} sec`,
      next_action: blocked
        ? row.blocking_reasons
        : review
          ? row.review_warnings
          : "Can be considered for automated route selection.",
      product_id: row.product_id ?? "-",
    };
  });
}

function formatList(value: unknown) {
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
