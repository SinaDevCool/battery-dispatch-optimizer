"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { DemoDataResetPanel } from "@/components/demo-data-reset-panel";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import type { PersonaId } from "@/lib/personas";
import type {
  Asset,
  AutomationControlStatusResponse,
  DataCompletenessResponse,
  StorageClassificationResponse,
  TableRow,
} from "@/types/api";

type AssetPersonaFraming = {
  archetypeTitle: string;
  backendTitle: string;
  blockersTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  eyebrow: string;
  gatesTitle: string;
  passportTitle: string;
  portfolioTitle: string;
  title: string;
};

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

const assetTabs = [
  {
    helper: "Selected asset passport, onboarding gates, and current blockers.",
    id: "overview",
    label: "Overview",
  },
  {
    helper: "Supported archetypes, selected data profile, demo reset, and backend source map.",
    id: "data",
    label: "Data Profile",
  },
  {
    helper: "Registered portfolio table for comparing configured assets.",
    id: "portfolio",
    label: "Portfolio",
  },
] as const;

type AssetTabId = (typeof assetTabs)[number]["id"];

export default function AssetsPage() {
  const { assets, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const [activeTab, setActiveTab] = useState<AssetTabId>("overview");
  const framing = getAssetPersonaFraming(personaId);

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
  const dataProfile = selectedAsset?.data_profile ?? {};
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
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
      />

      {!rows.length ? <ErrorState message="Could not load assets from the API." /> : null}

      <DecisionBrief
        blockers={registryDecision.blockers}
        className="mb-6"
        decision={registryDecision.decision}
        evidence={registryDecision.evidence}
        eyebrow={framing.decisionEyebrow}
        nextAction={registryDecision.nextAction}
        title={framing.decisionTitle}
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
          value={getAssetTypeLabel(selectedAsset)}
          helper={getAssetSubtypeLabel(selectedAsset) ?? getAssetArchetypeLabel(classification.data)}
        />
        <KpiCard
          accent="emerald"
          label="Technical envelope"
          value={`${formatAssetCapacity(selectedAsset)} MWh`}
          helper={`${formatPowerLimit(selectedAsset?.max_charge_power_mw)} MW charge / ${formatPowerLimit(selectedAsset?.max_discharge_power_mw)} MW discharge`}
        />
        <KpiCard
          accent={selectedAsset?.data_mode === "production" ? "emerald" : "blue"}
          label="Data mode"
          value={formatDataMode(selectedAsset?.data_mode)}
          helper={String(dataProfile.label ?? selectedAsset?.data_source ?? "source pending")}
        />
      </div>

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={assetTabs}
      />

      {activeTab === "overview" ? (
        <div className="space-y-5">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.75fr)]">
        <SectionCard
          action={<StatusPill tone={registryDecision.tone}>{registryDecision.blockers.length ? "Onboarding" : "Tradable"}</StatusPill>}
          title={framing.passportTitle}
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
          title={framing.gatesTitle}
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
                gate: "Mock data boundary",
                message: String(
                  selectedAsset?.data_mode === "production"
                    ? "Production data source"
                    : dataProfile.description ?? "Local mock data is isolated from production integrations.",
                ),
                status: selectedAsset?.data_mode ?? "unknown",
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
        title={framing.blockersTitle}
      >
        <DataTable
          columns={["blocker", "owner", "reason", "next_action"]}
          rows={buildBlockerRows({
            automation: automationControl.data,
            registryBlockers: registryDecision.blockers,
          })}
        />
      </SectionCard>
        </div>
      ) : null}

      {activeTab === "data" ? (
        <div className="space-y-5">
          <SectionCard
        action={<StatusPill tone="blue">{assetArchetypes.length} archetypes</StatusPill>}
        title={framing.archetypeTitle}
      >
        <DataTable
          columns={["archetype", "commercial_use", "evidence_needed", "fit"]}
          rows={assetArchetypes}
        />
      </SectionCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(420px,1.05fr)]">
        <SectionCard
          action={<StatusPill tone={selectedAsset?.data_mode === "production" ? "emerald" : "blue"}>{formatDataMode(selectedAsset?.data_mode)}</StatusPill>}
          title="Selected asset data profile"
        >
          <DataTable
            columns={["field", "value"]}
            rows={buildDataProfileRows(selectedAsset)}
          />
        </SectionCard>

        <DemoDataResetPanel />
      </div>

      {persona.layer === "client" ? null : (
        <SectionCard
          action={<StatusPill tone="blue">Backend linked</StatusPill>}
          title={framing.backendTitle}
        >
          <DataTable
            columns={["capability", "backend_route", "status", "business_value"]}
            rows={backendConnectionRows}
          />
        </SectionCard>
      )}
        </div>
      ) : null}

      {activeTab === "portfolio" ? (
      <SectionCard title={framing.portfolioTitle}>
        <DataTable
          columns={[
            "asset_id",
            "asset_name",
            "asset_type",
            "data_mode",
            "country",
            "market",
            "capacity_mwh",
            "max_charge_power_mw",
            "max_discharge_power_mw",
          ]}
          rows={rows}
        />
      </SectionCard>
      ) : null}
    </>
  );
}

function getAssetPersonaFraming(personaId: PersonaId): AssetPersonaFraming {
  const defaults: AssetPersonaFraming = {
    archetypeTitle: "Supported asset archetype reference",
    backendTitle: "Asset backend connection map",
    blockersTitle: "Blocker details",
    decisionEyebrow: "Asset onboarding decision",
    decisionTitle: "Is this asset ready for automated trading?",
    description:
      "Confirm physical limits, market classification, evidence readiness, and automation gates before an asset enters automated trading.",
    eyebrow: "Asset registry",
    gatesTitle: "Onboarding gates",
    passportTitle: "Asset trading passport",
    portfolioTitle: "Registered portfolio",
    title: "Asset onboarding",
  };

  const frames: Partial<Record<PersonaId, AssetPersonaFraming>> = {
    asset_owner: {
      archetypeTitle: "Supported asset types",
      backendTitle: "Asset evidence source map",
      blockersTitle: "Owner readiness blockers",
      decisionEyebrow: "Owner asset readiness decision",
      decisionTitle: "Can the owner rely on this asset record?",
      description:
        "Show the asset owner whether physical limits, market classification, evidence completeness, and automation readiness are clear enough to trust revenue and reporting claims.",
      eyebrow: "Client evidence portal",
      gatesTitle: "Owner readiness checks",
      passportTitle: "Owner asset passport",
      portfolioTitle: "Owner asset portfolio",
      title: "Asset readiness",
    },
    project_developer: {
      archetypeTitle: "Development asset archetypes",
      backendTitle: "Development evidence source map",
      blockersTitle: "Development readiness blockers",
      decisionEyebrow: "Development asset decision",
      decisionTitle: "Is this asset defined well enough for project planning?",
      description:
        "Confirm technical envelope, market classification, metering assumptions, and evidence completeness before using the asset in scenarios, price assumptions, and bankability work.",
      eyebrow: "Development readiness",
      gatesTitle: "Development readiness gates",
      passportTitle: "Development asset passport",
      portfolioTitle: "Development asset registry",
      title: "Development asset readiness",
    },
    investor_lender: {
      archetypeTitle: "Bankability asset context",
      backendTitle: "Asset evidence source map",
      blockersTitle: "Diligence asset blockers",
      decisionEyebrow: "Bankability asset decision",
      decisionTitle: "Is the asset definition diligence-ready?",
      description:
        "Show investors and lenders whether physical limits, market classification, storage mode, and evidence completeness are strong enough to support bankability review.",
      eyebrow: "Bankability view",
      gatesTitle: "Diligence readiness checks",
      passportTitle: "Bankability asset passport",
      portfolioTitle: "Bankability asset registry",
      title: "Bankability asset evidence",
    },
    client_success: {
      archetypeTitle: "Client asset context",
      backendTitle: "Client evidence source map",
      blockersTitle: "Client delivery blockers",
      decisionEyebrow: "Client asset explanation decision",
      decisionTitle: "Can client success explain this asset confidently?",
      description:
        "Package asset limits, market classification, evidence gaps, and automation readiness into a client-friendly asset context for reports and performance conversations.",
      eyebrow: "Client delivery",
      gatesTitle: "Client explanation checks",
      passportTitle: "Client asset passport",
      portfolioTitle: "Client asset list",
      title: "Client asset context",
    },
    market_operations: {
      archetypeTitle: "Operational asset archetypes",
      backendTitle: "Asset backend connection map",
      blockersTitle: "Operational registry blockers",
      decisionEyebrow: "Market operations asset decision",
      decisionTitle: "Is this asset configured for market operations?",
      description:
        "Validate market classification, asset limits, registry evidence, and automation dependencies before connectors, market rules, and route certification rely on the asset.",
      eyebrow: "Market operations",
      gatesTitle: "Operational onboarding gates",
      passportTitle: "Operational asset passport",
      portfolioTitle: "Operational asset registry",
      title: "Asset operations registry",
    },
    automation_operator: {
      archetypeTitle: "Automation-supported asset types",
      backendTitle: "Automation asset source map",
      blockersTitle: "Automation onboarding blockers",
      decisionEyebrow: "Automation asset decision",
      decisionTitle: "Can this asset enter the automation control plane?",
      description:
        "Check physical limits, evidence readiness, classification, and control-plane blockers before the asset can move from onboarding into automated trading workflows.",
      eyebrow: "Internal automation OS",
      gatesTitle: "Automation onboarding gates",
      passportTitle: "Automation asset passport",
      portfolioTitle: "Automation asset registry",
      title: "Automation asset onboarding",
    },
    risk_compliance: {
      archetypeTitle: "Governed asset archetypes",
      backendTitle: "Asset governance source map",
      blockersTitle: "Asset governance blockers",
      decisionEyebrow: "Asset governance decision",
      decisionTitle: "Is the asset record governed enough for approval?",
      description:
        "Review asset master data, storage classification, data completeness, and automation blockers before approving trading, reports, or compliance evidence.",
      eyebrow: "Risk & compliance",
      gatesTitle: "Asset governance gates",
      passportTitle: "Governed asset passport",
      portfolioTitle: "Governed asset registry",
      title: "Asset governance",
    },
  };

  return frames[personaId] ?? defaults;
}

function formatAssetRow(asset: Asset) {
  return {
    ...asset,
    asset_name:
      asset.asset_name ??
      asset.site_name ??
      asset.client_name ??
      asset.asset_id,
    asset_type: getAssetTypeLabel(asset),
    data_mode: formatDataMode(asset.data_mode),
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
      field: "Asset type",
      value: getAssetTypeLabel(asset),
    },
    {
      field: "Asset subtype",
      value: getAssetSubtypeLabel(asset) ?? "-",
    },
    {
      field: "Data mode",
      value: formatDataMode(asset?.data_mode),
    },
    {
      field: "Data source",
      value: asset?.data_source ?? "-",
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

function buildDataProfileRows(asset?: Asset): TableRow[] {
  const profile = asset?.data_profile ?? {};

  return [
    {
      field: "Profile",
      value: profile.label ?? profile.profile_id ?? "-",
    },
    {
      field: "Description",
      value:
        profile.description ??
        "No data profile description is configured for this asset.",
    },
    {
      field: "Forecast source",
      value: profile.forecast_source ?? asset?.forecast_file ?? "-",
    },
    {
      field: "Market data",
      value: profile.market_data_mode ?? "-",
    },
    {
      field: "Telemetry",
      value: profile.telemetry_mode ?? "-",
    },
    {
      field: "Execution adapter",
      value: profile.execution_adapter ?? "-",
    },
    {
      field: "Settlement",
      value: profile.settlement_mode ?? "-",
    },
    {
      field: "Production ready",
      value: profile.production_ready ? "yes" : "no",
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

function getAssetTypeLabel(asset?: Asset) {
  return formatEnumLabel(asset?.asset_type ?? "grid_scale_battery");
}

function getAssetSubtypeLabel(asset?: Asset) {
  return asset?.asset_subtype ? formatEnumLabel(asset.asset_subtype) : null;
}

function formatDataMode(dataMode?: string) {
  return formatEnumLabel(dataMode ?? "mock");
}

function formatEnumLabel(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
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
