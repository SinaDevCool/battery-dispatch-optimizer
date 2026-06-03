"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
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

  return (
    <>
      <PageHeading
        description="Germany-focused regulatory cockpit for storage classification, EEG logic, grid fee exposure, and ancillary service eligibility."
        eyebrow="Germany regulatory layer"
        title="Regulation"
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
        <SectionCard title="Storage classification">
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
            rows={gridFeeRows}
          />
        </SectionCard>

        <SectionCard title="Ancillary eligibility">
          <DataTable
            columns={[
              "product_id",
              "name",
              "eligibility_status",
              "minimum_duration_minutes",
              "response_time_seconds",
              "review_warnings",
              "blocking_reasons",
            ]}
            rows={formatAncillaryRows(ancillaryRows)}
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
