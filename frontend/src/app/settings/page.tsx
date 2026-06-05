"use client";

import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataCompletenessPanel } from "@/components/data-completeness-panel";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  ClientConfigResponse,
  DataCompletenessResponse,
  JsonObject,
  TableRow,
} from "@/types/api";

export default function SettingsPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();

  const config = useQuery({
    queryFn: () => apiGet<ClientConfigResponse>("/client/config"),
    queryKey: ["client-config"],
  });

  const completeness = useQuery({
    queryFn: () =>
      apiGet<DataCompletenessResponse>(
        `/assets/${selectedAssetId}/data-completeness`,
      ),
    queryKey: ["settings-data-completeness", selectedAssetId],
  });

  const clientConfig = config.data?.config ?? {};
  const batteryConfig = objectValue(clientConfig.battery_config);
  const strategyConfig = objectValue(clientConfig.strategy_config);
  const commercialConfig = objectValue(clientConfig.commercial_config);
  const assetBatteryConfig = objectValue(selectedAsset?.battery_config);
  const assetRegulatoryConfig = objectValue(selectedAsset?.regulatory_config);
  const evidenceChecks = completeness.data?.checks ?? [];
  const missingEvidence = evidenceChecks.filter((check) => check.status !== "complete");
  const automationMode = selectedAsset?.auto_trading_enabled ? "Enabled" : "Disabled";

  return (
    <>
      <PageHeading
        description="Configuration is shown read-only until role-based permissions, approval workflow, and audit logging are added. These sections translate backend config into product-level operating assumptions."
        eyebrow="Configuration"
        title="Settings"
      />

      <DecisionBrief
        blockers={[
          selectedAsset?.forecast_file ? null : "Forecast file is missing.",
          selectedAsset?.approval_mode ? null : "Approval mode is not configured.",
          missingEvidence.length ? `${missingEvidence.length} configuration evidence gap(s) remain.` : null,
        ].filter(Boolean) as string[]}
        className="mb-6"
        decision={
          <>
            {missingEvidence.length ? "Configuration review required" : "Configuration ready"}
            <span className="text-slate-500"> / </span>
            {automationMode}
          </>
        }
        evidence={[
          `Asset: ${displayValue(selectedAsset?.asset_name ?? selectedAssetId)}.`,
          `Market profile: ${displayValue(selectedAsset?.market_profile_id ?? clientConfig.market_profile_id)}.`,
          `Capacity: ${formatNumber(assetBatteryConfig.capacity_mwh ?? batteryConfig.capacity_mwh, 2)} MWh.`,
        ]}
        eyebrow="Configuration automation gate"
        nextAction={
          missingEvidence.length
            ? "Complete missing configuration evidence before raising automation mode."
            : "Use these assumptions as the asset-level configuration source for automated trading."
        }
        title="Can this asset be automated from config?"
        tone={missingEvidence.length ? "amber" : "emerald"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent="blue"
          label="Selected asset"
          value={displayValue(selectedAsset?.asset_name ?? selectedAssetId)}
          helper={displayValue(selectedAsset?.asset_id ?? selectedAssetId)}
        />
        <KpiCard
          accent="blue"
          label="Market"
          value={displayValue(selectedAsset?.market ?? clientConfig.market)}
          helper={displayValue(selectedAsset?.market_profile_id ?? clientConfig.market_profile_id)}
        />
        <KpiCard
          accent="emerald"
          label="Capacity"
          value={`${formatNumber(assetBatteryConfig.capacity_mwh ?? batteryConfig.capacity_mwh, 2)} MWh`}
          helper={`${formatNumber(assetBatteryConfig.max_charge_power_mw ?? batteryConfig.max_charge_power_mw, 2)} MW charge`}
        />
        <KpiCard
          accent="amber"
          label="Config status"
          value={config.data?.status ?? "-"}
          helper={`Auto trading: ${automationMode}`}
        />
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Client and market profile">
          <DataTable
            columns={["field", "value"]}
            rows={[
              row("Client name", clientConfig.client_name),
              row("Site name", clientConfig.site_name),
              row("Country", selectedAsset?.country ?? clientConfig.country),
              row("Market", selectedAsset?.market ?? clientConfig.market),
              row(
                "Market profile",
                selectedAsset?.market_profile_id ?? clientConfig.market_profile_id,
              ),
              row("Forecast file", selectedAsset?.forecast_file),
            ]}
          />
        </SectionCard>

        <SectionCard title="Asset technical limits">
          <DataTable
            columns={["field", "value"]}
            rows={[
              row("Capacity", `${formatNumber(assetBatteryConfig.capacity_mwh ?? batteryConfig.capacity_mwh, 2)} MWh`),
              row("Initial SOC", `${formatNumber(assetBatteryConfig.initial_soc_mwh ?? batteryConfig.initial_soc_mwh, 2)} MWh`),
              row("Minimum SOC", `${formatNumber(assetBatteryConfig.min_soc_mwh ?? batteryConfig.min_soc_mwh, 2)} MWh`),
              row("Max charge power", `${formatNumber(assetBatteryConfig.max_charge_power_mw ?? batteryConfig.max_charge_power_mw, 2)} MW`),
              row("Max discharge power", `${formatNumber(assetBatteryConfig.max_discharge_power_mw ?? batteryConfig.max_discharge_power_mw, 2)} MW`),
              row("Charge efficiency", `${formatNumber(Number(assetBatteryConfig.charge_efficiency ?? batteryConfig.charge_efficiency) * 100, 1)}%`),
              row("Discharge efficiency", `${formatNumber(Number(assetBatteryConfig.discharge_efficiency ?? batteryConfig.discharge_efficiency) * 100, 1)}%`),
            ]}
          />
        </SectionCard>
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Dispatch strategy">
          <DataTable
            columns={["field", "value"]}
            rows={[
              row("Mode", strategyConfig.mode ?? "rule_based_dispatch"),
              row("Low price threshold", `${formatNumber(strategyConfig.low_price_threshold, 2)} EUR/MWh`),
              row("High price threshold", `${formatNumber(strategyConfig.high_price_threshold, 2)} EUR/MWh`),
              row("Timestep", `${formatNumber(strategyConfig.timestep_hours, 2)} h`),
              row("Forecast horizon", `${formatNumber(strategyConfig.forecast_horizon_hours, 0)} h`),
              row("Max cycles per day", strategyConfig.max_cycles_per_day),
            ]}
          />
        </SectionCard>

        <SectionCard title="Commercial assumptions">
          <DataTable
            columns={["field", "value"]}
            rows={[
              row("Trading fee", `${formatNumber(commercialConfig.trading_fee_eur_per_mwh, 2)} EUR/MWh`),
              row("Market access fee", `${formatNumber(commercialConfig.market_access_fee_eur_per_mwh, 2)} EUR/MWh`),
              row("Grid import fee", `${formatNumber(commercialConfig.grid_fee_import_eur_per_mwh, 2)} EUR/MWh`),
              row("Grid export fee", `${formatNumber(commercialConfig.grid_fee_export_eur_per_mwh, 2)} EUR/MWh`),
              row("Tax or levy", `${formatNumber(commercialConfig.tax_or_levy_eur_per_mwh, 2)} EUR/MWh`),
              row("Degradation cost", `${formatNumber(commercialConfig.degradation_cost_eur_per_mwh_throughput, 2)} EUR/MWh throughput`),
              row("Minimum spread", `${formatNumber(commercialConfig.minimum_required_spread_eur_per_mwh, 2)} EUR/MWh`),
            ]}
          />
        </SectionCard>
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Germany regulatory assumptions">
          <DataTable
            columns={["field", "value"]}
            rows={[
              row("Storage mode", assetRegulatoryConfig.storage_mode),
              row("Colocated", assetRegulatoryConfig.is_colocated),
              row("Charges from grid", assetRegulatoryConfig.charges_from_grid),
              row("Charges from renewables", assetRegulatoryConfig.charges_from_renewables),
              row("Exports stored renewable power", assetRegulatoryConfig.exports_stored_renewable_power),
              row("Uses EEG support", assetRegulatoryConfig.uses_eeg_support),
              row("Metering concept", assetRegulatoryConfig.metering_concept),
            ]}
          />
        </SectionCard>

        <SectionCard title="Revenue certainty assumptions">
          <DataTable
            columns={["field", "value"]}
            rows={[
              row("Forecast source", selectedAsset?.forecast_provider ?? "-"),
              row("Forecast file", selectedAsset?.forecast_file ?? "-"),
              row("Merchant floor", formatCurrency(selectedAsset?.merchant_floor_eur)),
              row("Auto trading mode", selectedAsset?.auto_trading_enabled ? "Enabled" : "Disabled"),
              row("Approval mode", selectedAsset?.approval_mode ?? "Human required"),
            ]}
          />
        </SectionCard>
      </div>

      <DataCompletenessPanel data={completeness.data} title="Configuration evidence readiness" />
    </>
  );
}

function objectValue(value: unknown): JsonObject {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as JsonObject;
  }

  return {};
}

function row(field: string, value: unknown): TableRow {
  return {
    field,
    value: normalizeValue(value),
  };
}

function normalizeValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "number" || typeof value === "string") {
    return value;
  }

  return JSON.stringify(value);
}

function displayValue(value: unknown) {
  return String(normalizeValue(value));
}
