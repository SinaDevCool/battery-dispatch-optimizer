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

  return (
    <>
      <PageHeading
        description="Germany-focused regulatory cockpit for storage classification, EEG logic, grid fee exposure, and ancillary service eligibility."
        eyebrow="Germany regulatory layer"
        title="Regulation"
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard label="Storage class" value={String(classification.data?.storage_classification ?? "-")} />
        <KpiCard accent="amber" label="EEG status" value={String(eeg.data?.status ?? "-")} />
        <KpiCard label="Ancillary eligible" value={String(ancillary.data?.eligible ?? "-")} />
        <KpiCard accent="blue" label="Country" value="Germany" />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard title="Storage and EEG checks">
          <DataTable
            columns={["field", "value"]}
            rows={[
              ...objectToRows(classification.data ?? {}),
              ...objectToRows(eeg.data ?? {}),
            ]}
          />
        </SectionCard>

        <SectionCard title="Grid fee sensitivity">
          <DataTable
            columns={["scenario_name", "grid_fee_eur_per_mwh", "total_pnl_eur", "pnl_delta_eur"]}
            rows={gridFees.data?.sensitivity ?? []}
          />
        </SectionCard>
      </div>
    </>
  );
}

function objectToRows(value: JsonObject) {
  return Object.entries(value).map(([field, rowValue]) => ({
    field,
    value: rowValue,
  }));
}
