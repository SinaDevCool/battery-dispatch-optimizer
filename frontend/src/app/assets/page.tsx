"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import type {
  Asset,
  AutomationControlStatusResponse,
  DataCompletenessResponse,
  StorageClassificationResponse,
  TableRow,
} from "@/types/api";

const assetArchetypes: TableRow[] = [
  {
    archetype: "Standalone grid battery",
    commercial_use: "Merchant arbitrage, ancillary services, congestion response",
    evidence_needed: "Grid connection, telemetry, market access, SOC limits",
    fit: "Current asset",
  },
  {
    archetype: "Solar + battery",
    commercial_use: "Solar shifting, grid export optimization, EEG/GO origin separation",
    evidence_needed: "Generation meter, storage meter, metering concept, EEG status",
    fit: "Supported",
  },
  {
    archetype: "Wind + battery",
    commercial_use: "Wind shaping, imbalance reduction, reserve-ready flexibility",
    evidence_needed: "Generation forecast, metering concept, grid/export limits",
    fit: "Supported",
  },
  {
    archetype: "Hybrid renewable park",
    commercial_use: "Portfolio dispatch across generation, storage, and market products",
    evidence_needed: "Asset grouping, allocation rules, market route per product",
    fit: "Supported",
  },
  {
    archetype: "Behind-the-meter industrial",
    commercial_use: "Peak shaving, self-consumption, backup, optional market access",
    evidence_needed: "Load meter, site tariff, export permission, operational constraints",
    fit: "Needs site data",
  },
  {
    archetype: "Fleet or EV depot battery",
    commercial_use: "Depot optimization, flexibility trading, availability-aware dispatch",
    evidence_needed: "Availability windows, charging demand, connection limits",
    fit: "Needs schedule data",
  },
];

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
  const backendConnectionRows = buildAssetBackendConnectionRows({
    assetCount: assets.length,
    automation: automationControl.data,
    completeness: dataCompleteness.data,
    classification: classification.data,
    selectedAssetId,
  });

  return (
    <>
      <PageHeading
        description="Confirm physical limits, market classification, evidence readiness, and automation gates before an asset enters automated trading."
        eyebrow="Asset registry"
        title="Asset onboarding"
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
        <KpiCard
          accent="blue"
          label="Selected asset"
          value={selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId}
          helper={`${selectedAsset?.country ?? "-"} / ${selectedAsset?.market ?? "market pending"}`}
        />
        <KpiCard
          accent="blue"
          label="Asset archetype"
          value={getAssetArchetypeLabel(classification.data)}
          helper={classification.data?.market_participation_mode ?? classification.data?.status ?? "not classified"}
        />
        <KpiCard
          accent="emerald"
          label="Technical envelope"
          value={`${formatAssetCapacity(selectedAsset)} MWh`}
          helper={`${formatPowerLimit(selectedAsset?.max_charge_power_mw)} MW charge / ${formatPowerLimit(selectedAsset?.max_discharge_power_mw)} MW discharge`}
        />
        <KpiCard
          accent={dataCompleteness.data?.readiness === "ready" ? "emerald" : "amber"}
          label="Evidence readiness"
          value={`${dataCompleteness.data?.score ?? "-"} / 100`}
          helper={dataCompleteness.data?.readiness ?? "not evaluated"}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.75fr)]">
        <SectionCard
          action={<StatusPill tone={registryDecision.tone}>{registryDecision.blockers.length ? "Onboarding" : "Tradable"}</StatusPill>}
          title="Asset trading passport"
        >
          <DataTable
            columns={["field", "value"]}
            rows={buildAssetPassportRows({
              asset: selectedAsset,
              classification: classification.data,
            })}
          />
        </SectionCard>

        <SectionCard
          action={
            <StatusPill tone={automationControl.data?.automation_status === "blocked" ? "amber" : "emerald"}>
              {automationControl.data?.automation_status ?? "not evaluated"}
            </StatusPill>
          }
          title="Onboarding gates"
        >
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

      <SectionCard
        action={
          <StatusPill tone={registryDecision.blockers.length ? "amber" : "emerald"}>
            {registryDecision.blockers.length} blocker(s)
          </StatusPill>
        }
        className="mt-5"
        title="Blocker details"
      >
        <DataTable
          columns={["blocker", "owner", "reason", "next_action"]}
          rows={buildBlockerRows({
            automation: automationControl.data,
            registryBlockers: registryDecision.blockers,
          })}
        />
      </SectionCard>

      <SectionCard
        action={<StatusPill tone="blue">{assetArchetypes.length} archetypes</StatusPill>}
        className="mt-5"
        title="Supported asset archetype reference"
      >
        <DataTable
          columns={["archetype", "commercial_use", "evidence_needed", "fit"]}
          rows={assetArchetypes}
        />
      </SectionCard>

      <SectionCard
        action={<StatusPill tone="blue">Backend linked</StatusPill>}
        className="mt-5"
        title="Asset backend connection map"
      >
        <DataTable
          columns={["capability", "backend_route", "status", "business_value"]}
          rows={backendConnectionRows}
        />
      </SectionCard>

      <SectionCard className="mt-5" title="Registered portfolio">
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

function buildAssetBackendConnectionRows({
  assetCount,
  automation,
  completeness,
  classification,
  selectedAssetId,
}: {
  assetCount: number;
  automation?: AutomationControlStatusResponse;
  completeness?: DataCompletenessResponse;
  classification?: StorageClassificationResponse;
  selectedAssetId: string;
}) {
  return [
    {
      capability: "Registered portfolio",
      backend_route: "/assets",
      status: `${assetCount} asset(s)`,
      business_value: "Lists the physical assets available for trading workflows.",
    },
    {
      capability: "Storage classification",
      backend_route: `/assets/${selectedAssetId}/storage-classification`,
      status:
        classification?.storage_classification ??
        classification?.storage_mode ??
        classification?.status ??
        "not_loaded",
      business_value: "Determines market, EEG, and metering assumptions before automation.",
    },
    {
      capability: "Evidence completeness",
      backend_route: `/assets/${selectedAssetId}/data-completeness`,
      status: `${completeness?.score ?? "-"} / 100`,
      business_value: "Blocks onboarding when forecast, revenue, or execution proof is missing.",
    },
    {
      capability: "Automation control",
      backend_route: `/assets/${selectedAssetId}/execution/automation-control/status`,
      status: automation?.automation_status ?? "not_loaded",
      business_value: "Prevents live trading until policy, approval, and guardrails are clear.",
    },
  ];
}

function buildAssetPassportRows({
  asset,
  classification,
}: {
  asset?: Asset;
  classification?: StorageClassificationResponse;
}) {
  return [
    {
      field: "Asset",
      value: asset?.asset_name ?? asset?.site_name ?? asset?.asset_id ?? "-",
    },
    {
      field: "Market",
      value: `${asset?.country ?? "-"} / ${asset?.market ?? "market pending"}`,
    },
    {
      field: "Capacity",
      value: `${formatAssetCapacity(asset)} MWh`,
    },
    {
      field: "Power limits",
      value: `${formatPowerLimit(asset?.max_charge_power_mw)} MW charge / ${formatPowerLimit(asset?.max_discharge_power_mw)} MW discharge`,
    },
    {
      field: "Storage classification",
      value: getAssetArchetypeLabel(classification),
    },
    {
      field: "Market participation",
      value:
        classification?.market_participation_mode ??
        classification?.status ??
        "not evaluated",
    },
  ];
}

function buildBlockerRows({
  automation,
  registryBlockers,
}: {
  automation?: AutomationControlStatusResponse;
  registryBlockers: string[];
}) {
  const automationBlockers = (automation?.blockers ?? []).map((blocker) => ({
    blocker: String(
      blocker.key ??
        blocker.blocker ??
        blocker.category ??
        blocker.source ??
        "automation_gate",
    ),
    owner: String(blocker.owner ?? blocker.source ?? "automation_control"),
    reason: String(blocker.message ?? blocker.reason ?? "Automation gate is blocked."),
    next_action: String(
      blocker.next_action ??
        blocker.remediation ??
        automation?.next_automation_action?.message ??
        "Open Automation Control or Mission Control to clear this gate.",
    ),
  }));

  if (automationBlockers.length) {
    return automationBlockers;
  }

  return registryBlockers.map((blocker, index) => ({
    blocker: `registry_blocker_${index + 1}`,
    owner: "asset_onboarding",
    reason: blocker,
    next_action:
      automation?.next_automation_action?.message ??
      "Complete missing evidence and rerun onboarding checks.",
  }));
}

function getAssetArchetypeLabel(classification?: StorageClassificationResponse) {
  const storageMode =
    classification?.storage_classification ?? classification?.storage_mode;

  if (storageMode === "standalone_grid_connected") {
    return "Standalone grid battery";
  }

  if (storageMode === "pure_green_colocated") {
    return "Co-located renewable battery";
  }

  if (storageMode === "mixed_colocated") {
    return "Mixed-source co-located battery";
  }

  if (storageMode === "brown_colocated") {
    return "Co-located non-renewable battery";
  }

  return storageMode ?? "Not classified";
}

function formatAssetCapacity(asset?: Asset) {
  return String(
    asset?.capacity_mwh ??
      (asset?.battery_config as { capacity_mwh?: number } | undefined)
        ?.capacity_mwh ??
      "-",
  );
}

function formatPowerLimit(value?: number | null) {
  return value === null || value === undefined ? "-" : String(value);
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
