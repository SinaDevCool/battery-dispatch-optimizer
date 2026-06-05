"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import type {
  Asset,
  AutomationControlStatusResponse,
  DataCompletenessResponse,
  StorageClassificationResponse,
} from "@/types/api";

export default function AssetsPage() {
  const { assets, selectedAssetId } = useAssetContext();

  const classification = useQuery({
    queryFn: () =>
      apiGet<StorageClassificationResponse>(
        `/assets/${selectedAssetId}/storage-classification`,
      ),
    queryKey: ["storage-classification", selectedAssetId],
  });

  const dataCompleteness = useQuery({
    queryFn: () =>
      apiGet<DataCompletenessResponse>(
        `/assets/${selectedAssetId}/data-completeness`,
      ),
    queryKey: ["asset-registry-data-completeness", selectedAssetId],
  });

  const automationControl = useQuery({
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["asset-registry-automation-control", selectedAssetId],
  });

  const rows = assets.map(formatAssetRow);
  const selectedAsset = assets.find((asset) => asset.asset_id === selectedAssetId);
  const registryDecision = buildRegistryDecision({
    asset: selectedAsset,
    automation: automationControl.data,
    completeness: dataCompleteness.data,
    classification: classification.data,
  });

  return (
    <>
      <PageHeading
        description="Manage battery assets, commercial assumptions, technical limits, and Germany-specific storage classification."
        eyebrow="Asset registry"
        title="Battery assets"
      />

      {!rows.length ? <ErrorState message="Could not load assets from the API." /> : null}

      <DecisionBrief
        blockers={registryDecision.blockers}
        className="mb-6"
        decision={registryDecision.decision}
        evidence={registryDecision.evidence}
        eyebrow="Asset onboarding decision"
        nextAction={registryDecision.nextAction}
        title="Is this asset ready for automated trading?"
        tone={registryDecision.tone}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Registered assets" value={rows.length} />
        <KpiCard
          accent="blue"
          label="Storage class"
          value={String(
            classification.data?.storage_classification ??
              classification.data?.storage_mode ??
              "-",
          )}
        />
        <KpiCard
          accent="amber"
          label="Market participation"
          value={String(
            classification.data?.market_participation_mode ??
              classification.data?.status ??
              "-",
          )} 
        />
        <KpiCard
          accent={dataCompleteness.data?.readiness === "ready" ? "emerald" : "amber"}
          label="Evidence readiness"
          value={`${dataCompleteness.data?.score ?? "-"} / 100`}
          helper={dataCompleteness.data?.readiness ?? "not evaluated"}
        />
        <KpiCard
          accent={automationControl.data?.paper_trading_allowed ? "emerald" : "amber"}
          label="Automation mode"
          value={automationControl.data?.automation_mode ?? "-"}
          helper={automationControl.data?.automation_status ?? "control plane"}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.75fr)]">
        <SectionCard title="Asset list">
          <DataTable
            columns={[
              "asset_id",
              "asset_name",
              "country",
              "market",
              "capacity_mwh",
              "max_charge_power_mw",
              "max_discharge_power_mw",
            ]}
            rows={rows}
          />
        </SectionCard>

        <SectionCard title="Automation onboarding checklist">
          <DataTable
            columns={["gate", "status", "message"]}
            rows={[
              {
                gate: "Asset master data",
                message: selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId,
                status: selectedAsset ? "complete" : "missing",
              },
              {
                gate: "Storage classification",
                message:
                  classification.data?.storage_classification ??
                  classification.data?.storage_mode ??
                  "-",
                status: classification.data?.status ?? "not evaluated",
              },
              {
                gate: "Data completeness",
                message: `${dataCompleteness.data?.complete_count ?? 0}/${dataCompleteness.data?.check_count ?? 0} evidence checks complete`,
                status: dataCompleteness.data?.readiness ?? "-",
              },
              {
                gate: "Automation control",
                message: automationControl.data?.next_automation_action?.message ?? "-",
                status: automationControl.data?.automation_status ?? "-",
              },
            ]}
          />
        </SectionCard>
      </div>
    </>
  );
}

function formatAssetRow(asset: Asset) {
  return {
    ...asset,
    asset_name:
      asset.asset_name ??
      asset.site_name ??
      asset.client_name ??
      asset.asset_id,
    capacity_mwh:
      asset.capacity_mwh ??
      (asset.battery_config as { capacity_mwh?: number } | undefined)
        ?.capacity_mwh,
  };
}

function buildRegistryDecision({
  asset,
  automation,
  completeness,
  classification,
}: {
  asset?: Asset;
  automation?: AutomationControlStatusResponse;
  completeness?: DataCompletenessResponse;
  classification?: StorageClassificationResponse;
}) {
  const blockers = [
    !asset ? "Selected asset is missing from the registry." : null,
    completeness?.readiness !== "ready"
      ? `${completeness?.missing_count ?? 0} asset evidence item(s) still need completion.`
      : null,
    automation?.automation_status === "blocked"
      ? "Automation control plane is blocked for this asset."
      : null,
  ].filter(Boolean) as string[];

  return {
    blockers,
    decision: blockers.length
      ? "Keep this asset in onboarding until evidence and automation gates clear."
      : "Asset registry is ready to support automated trading workflows.",
    evidence: [
      `Asset ${asset?.asset_name ?? asset?.site_name ?? asset?.asset_id ?? "not selected"}`,
      `Storage class ${classification?.storage_classification ?? classification?.storage_mode ?? "not classified"}`,
      `Data completeness ${completeness?.score ?? "-"} / 100`,
      `Automation mode ${automation?.automation_mode ?? "not evaluated"}`,
    ],
    nextAction:
      automation?.next_automation_action?.message ??
      completeness?.next_actions?.[0] ??
      "Complete asset evidence before routing the battery into automated trading.",
    tone: blockers.length ? "amber" as const : "emerald" as const,
  };
}
