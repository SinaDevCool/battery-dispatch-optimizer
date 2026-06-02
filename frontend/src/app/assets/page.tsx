"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import type { StorageClassificationResponse } from "@/types/api";

export default function AssetsPage() {
  const { assets, selectedAssetId } = useAssetContext();

  const classification = useQuery({
    queryFn: () =>
      apiGet<StorageClassificationResponse>(
        `/assets/${selectedAssetId}/storage-classification`,
      ),
    queryKey: ["storage-classification", selectedAssetId],
  });

  const rows = assets;

  return (
    <>
      <PageHeading
        description="Manage battery assets, commercial assumptions, technical limits, and Germany-specific storage classification."
        eyebrow="Asset registry"
        title="Battery assets"
      />

      {!rows.length ? <ErrorState message="Could not load assets from the API." /> : null}

      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <KpiCard label="Registered assets" value={rows.length} />
        <KpiCard
          accent="blue"
          label="Storage class"
          value={String(classification.data?.storage_classification ?? "-")}
        />
        <KpiCard
          accent="amber"
          label="Market participation"
          value={String(classification.data?.market_participation_mode ?? "-")}
        />
      </div>

      <SectionCard title="Asset list">
        <DataTable
          columns={["asset_id", "asset_name", "country", "market", "capacity_mwh"]}
          rows={rows}
        />
      </SectionCard>
    </>
  );
}
