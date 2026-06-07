"use client";

import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataCompletenessPanel } from "@/components/data-completeness-panel";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  ClientConfigResponse,
  CredentialReadinessItem,
  CredentialReadinessResponse,
  CredentialRouteRequirement,
  DataCompletenessResponse,
  JsonObject,
  LiveAdapterHandshakeDrill,
  LiveAdapterHandshakeEnvActivationGuide,
  LiveAdapterHandshakeEnvItem,
  LiveAdapterHandshakeHistoryResponse,
  LiveAdapterHandshakeResponse,
  LiveAdapterHandshakeTarget,
  LiveAdapterRouteHandshake,
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

  const credentials = useQuery({
    queryFn: () => apiGet<CredentialReadinessResponse>("/system/credential-readiness"),
    queryKey: ["credential-readiness"],
  });

  const handshakes = useQuery({
    queryFn: () =>
      apiGet<LiveAdapterHandshakeResponse>(
        `/system/live-adapter-handshake?country=Germany&asset_id=${selectedAssetId}`,
      ),
    queryKey: ["live-adapter-handshake", selectedAssetId],
  });

  const handshakeHistory = useQuery({
    queryFn: () =>
      apiGet<LiveAdapterHandshakeHistoryResponse>(
        `/system/live-adapter-handshake/history?asset_id=${selectedAssetId}&limit=6`,
      ),
    queryKey: ["live-adapter-handshake-history", selectedAssetId],
  });

  const clientConfig = config.data?.config ?? {};
  const batteryConfig = objectValue(clientConfig.battery_config);
  const strategyConfig = objectValue(clientConfig.strategy_config);
  const commercialConfig = objectValue(clientConfig.commercial_config);
  const assetBatteryConfig = objectValue(selectedAsset?.battery_config);
  const assetRegulatoryConfig = objectValue(selectedAsset?.regulatory_config);
  const evidenceChecks = completeness.data?.checks ?? [];
  const missingEvidence = evidenceChecks.filter((check) => check.status !== "complete");
  const credentialSummary = credentials.data?.summary ?? {};
  const handshakeSummary = handshakes.data?.summary ?? {};
  const envActivationConfiguredRouteCount = Number(
    handshakeSummary.env_activation_configured_route_count ?? 0,
  );
  const envActivationSetupRouteCount = Number(
    handshakeSummary.env_activation_setup_required_route_count ?? 0,
  );
  const envChecklistCount = Number(handshakeSummary.env_checklist_count ?? 0);
  const envConfiguredCount = Number(handshakeSummary.env_configured_count ?? 0);
  const envMissingCount = Number(handshakeSummary.env_missing_count ?? 0);
  const missingCredentials = credentials.data?.credentials?.filter((item) => item.status !== "configured") ?? [];
  const handshakeBlockers = handshakes.data?.targets?.filter((item) => !["dry_run_ready", "real_ready"].includes(String(item.handshake_status))) ?? [];
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
          missingCredentials.length ? `${missingCredentials.length} credential onboarding item(s) remain.` : null,
          handshakeBlockers.length ? `${handshakeBlockers.length} live adapter handshake item(s) remain.` : null,
        ].filter(Boolean) as string[]}
        className="mb-6"
        decision={
          <>
            {missingEvidence.length || missingCredentials.length ? "Configuration review required" : "Configuration ready"}
            <span className="text-slate-500"> / </span>
            {automationMode}
          </>
        }
        evidence={[
          `Asset: ${displayValue(selectedAsset?.asset_name ?? selectedAssetId)}.`,
          `Market profile: ${displayValue(selectedAsset?.market_profile_id ?? clientConfig.market_profile_id)}.`,
          `Capacity: ${formatNumber(assetBatteryConfig.capacity_mwh ?? batteryConfig.capacity_mwh, 2)} MWh.`,
          `${credentialSummary.credential_ready_route_count ?? 0} route(s) have required credentials configured.`,
          `${handshakeSummary.handshake_ready_count ?? 0}/${handshakeSummary.handshake_target_count ?? 0} live adapter handshake target(s) are dry-run ready.`,
        ]}
        eyebrow="Configuration automation gate"
        nextAction={
          missingEvidence.length
            ? "Complete missing configuration evidence before raising automation mode."
            : missingCredentials.length
              ? "Complete credential onboarding before supervised live trading."
              : handshakeBlockers.length
                ? "Enable dry-run handshakes for market, EMS, data, and settlement adapters before supervised live trading."
            : "Use these assumptions as the asset-level configuration source for automated trading."
        }
        title="Can this asset be automated from config?"
        tone={missingEvidence.length || missingCredentials.length || handshakeBlockers.length ? "amber" : "emerald"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-6">
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
        <KpiCard
          accent={credentialTone(credentials.data?.credential_readiness_status)}
          label="Credential readiness"
          value={credentials.data?.credential_readiness_status ?? "-"}
          helper={`${credentialSummary.configured_credential_count ?? 0}/${credentialSummary.credential_count ?? 0} configured`}
        />
        <KpiCard
          accent={handshakeTone(handshakes.data?.handshake_readiness_status)}
          label="Live handshake"
          value={handshakes.data?.handshake_readiness_status ?? "-"}
          helper={`${handshakeSummary.env_configured_count ?? 0}/${handshakeSummary.env_checklist_count ?? 0} env items configured`}
        />
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <SectionCard
          action={
            <StatusPill tone={credentialTone(credentials.data?.credential_readiness_status)}>
              {credentials.data?.credential_readiness_status ?? "-"}
            </StatusPill>
          }
          title="Credential onboarding"
        >
          <DataTable
            columns={[
              "group",
              "label",
              "status",
              "configured_env_key",
              "accepted_env_keys",
              "blocks_mode",
              "next_action",
            ]}
            rows={formatCredentialRows(credentials.data?.credentials ?? [])}
          />
        </SectionCard>

        <SectionCard title="Route credential blockers">
          <DataTable
            columns={[
              "adapter_id",
              "credential_status",
              "configured",
              "missing_credentials",
              "missing_env_keys",
              "onboarding_next_action",
            ]}
            rows={formatCredentialRouteRows(credentials.data?.route_requirements ?? [])}
          />
        </SectionCard>
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)]">
        <SectionCard
          action={
            <div className="flex flex-wrap items-start gap-2">
              <ActionButton
                endpoint={`/system/live-adapter-handshake/run?asset_id=${selectedAssetId}&country=Germany`}
                label="Run drill"
                refetch={() => Promise.all([handshakes.refetch(), handshakeHistory.refetch()])}
                variant="primary"
              />
              <StatusPill tone={handshakeTone(handshakes.data?.handshake_readiness_status)}>
                {handshakes.data?.handshake_readiness_status ?? "-"}
              </StatusPill>
            </div>
          }
          title="Live adapter handshake"
        >
          <DataTable
            columns={[
              "group",
              "target",
              "handshake_status",
              "endpoint_status",
              "credential_status",
              "handshake_mode",
              "latest_drill",
              "no_order_submission",
              "next_handshake_action",
            ]}
            rows={formatHandshakeRows(handshakes.data?.targets ?? [])}
          />
        </SectionCard>

        <SectionCard title="Route handshake blockers">
          <div className="space-y-4">
            <DataTable
              columns={[
                "adapter_id",
                "route_handshake_status",
                "ready_targets",
                "route_handshake_blockers",
                "route_handshake_next_action",
              ]}
              rows={formatHandshakeRouteRows(handshakes.data?.routes ?? [])}
            />
            <DataTable
              columns={[
                "created_at",
                "status",
                "action",
                "route_id",
                "passed_count",
                "blocked_count",
                "order_submission_performed",
              ]}
              rows={formatHandshakeHistoryRows(handshakeHistory.data?.drills ?? [])}
            />
          </div>
        </SectionCard>
      </div>

      <SectionCard
        action={
          <StatusPill tone={Number(handshakeSummary.env_missing_count ?? 0) ? "amber" : "emerald"}>
            {handshakeSummary.env_missing_count ?? 0} missing
          </StatusPill>
        }
        className="mb-5"
        title="Guided live environment activation"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <KpiCard
            accent={envActivationSetupRouteCount ? "amber" : "emerald"}
            helper={`${envActivationConfiguredRouteCount} configured`}
            label="Routes needing setup"
            value={envActivationSetupRouteCount}
          />
          <KpiCard
            accent="blue"
            helper="Secret values are never rendered"
            label="Secret handling"
            value="hidden"
          />
          <KpiCard
            accent={envMissingCount ? "amber" : "emerald"}
            helper={`${envConfiguredCount}/${envChecklistCount} configured`}
            label="Env checklist"
            value={envMissingCount}
          />
        </div>
        <DataTable
          columns={[
            "route_label",
            "market_family",
            "activation_status",
            "configured",
            "mode_status",
            "endpoint_status",
            "next_unlock_label",
            "missing_env_keys",
            "secret_env_keys",
            "drill",
          ]}
          rows={formatHandshakeActivationRows(handshakes.data?.env_activation_guide ?? [])}
        />
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(handshakes.data?.env_activation_guide ?? []).map((route) => (
            <div
              className="rounded-lg border border-slate-800 bg-slate-900/45 p-4"
              key={route.adapter_id ?? route.route_label}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-100">
                    {route.route_label ?? route.adapter_id}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {route.market_family ?? "market route"} / {route.activation_status ?? "not evaluated"}
                  </div>
                </div>
                <StatusPill tone={route.handshake_drill_enabled_after_setup ? "emerald" : "amber"}>
                  {route.handshake_drill_enabled_after_setup ? "drill ready" : "setup locked"}
                </StatusPill>
              </div>
              <div className="mt-4 text-xs leading-5 text-slate-400">
                {route.next_action ?? "Complete setup before running a route drill."}
              </div>
              <div className="mt-4">
                {route.handshake_drill_enabled_after_setup && route.system_route_drill_endpoint ? (
                  <ActionButton
                    endpoint={route.system_route_drill_endpoint}
                    label="Run route drill"
                    refetch={() => Promise.all([handshakes.refetch(), handshakeHistory.refetch()])}
                    variant="primary"
                  />
                ) : (
                  <StatusPill tone="blue">
                    {route.next_unlock_label ?? "Configure route"}
                  </StatusPill>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4">
          <DataTable
            columns={["route_label", "safe_deployment_steps", "secret_values_exposed"]}
            rows={formatHandshakeActivationSteps(handshakes.data?.env_activation_guide ?? [])}
          />
        </div>
      </SectionCard>

      <SectionCard
        action={
          <StatusPill tone={Number(handshakeSummary.env_missing_count ?? 0) ? "amber" : "emerald"}>
            raw checklist
          </StatusPill>
        }
        className="mb-5"
        title="Live handshake environment detail"
      >
        <DataTable
          columns={[
            "group",
            "target",
            "item_type",
            "status",
            "env_keys",
            "required_value",
            "configured_env_key",
            "secret",
            "blocks_routes",
            "next_action",
          ]}
          rows={formatHandshakeEnvRows(handshakes.data?.env_checklist ?? [])}
        />
      </SectionCard>

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

function formatCredentialRows(rows: CredentialReadinessItem[]): TableRow[] {
  return rows.map((item) => ({
    accepted_env_keys: listValue(item.accepted_env_keys),
    blocks_mode: item.blocks_mode?.replaceAll("_", " ") ?? "-",
    configured_env_key: item.configured_env_key ?? "-",
    group: item.group ?? "-",
    label: item.label ?? item.credential_id ?? "-",
    next_action: item.next_action ?? "-",
    status: item.status ?? "-",
  }));
}

function formatCredentialRouteRows(rows: CredentialRouteRequirement[]): TableRow[] {
  return rows.map((route) => ({
    adapter_id: route.adapter_id,
    configured: `${route.configured_credential_count ?? 0}/${route.required_credential_count ?? 0}`,
    credential_status: route.credential_status ?? "-",
    missing_credentials: listValue(route.missing_credentials),
    missing_env_keys: listValue(route.missing_env_keys),
    onboarding_next_action: route.onboarding_next_action ?? "-",
  }));
}

function formatHandshakeRows(rows: LiveAdapterHandshakeTarget[]): TableRow[] {
  return rows.map((item) => ({
    credential_status: item.credential_status?.replaceAll("_", " ") ?? "-",
    endpoint_status: item.endpoint_status?.replaceAll("_", " ") ?? "-",
    group: item.group ?? "-",
    handshake_mode: item.handshake_mode?.replaceAll("_", " ") ?? "-",
    handshake_status: item.handshake_status?.replaceAll("_", " ") ?? "-",
    latest_drill: item.latest_drill_status
      ? `${item.latest_drill_status} @ ${item.latest_drill_at ?? "-"}`
      : "-",
    next_handshake_action: item.next_handshake_action ?? "-",
    no_order_submission: item.no_order_submission ? "yes" : "no",
    target: item.label ?? item.target_id ?? "-",
  }));
}

function formatHandshakeHistoryRows(rows: LiveAdapterHandshakeDrill[]): TableRow[] {
  return rows.map((row) => ({
    action: row.action?.replaceAll("_", " ") ?? "-",
    blocked_count: row.blocked_count ?? 0,
    created_at: row.created_at ?? "-",
    order_submission_performed: row.order_submission_performed ? "yes" : "no",
    passed_count: row.passed_count ?? 0,
    route_id: row.route_id ?? "-",
    status: row.status ?? "-",
  }));
}

function formatHandshakeEnvRows(rows: LiveAdapterHandshakeEnvItem[]): TableRow[] {
  return rows.map((item) => ({
    blocks_routes: listValue(item.blocks_routes),
    configured_env_key: item.configured_env_key ?? "-",
    env_keys: listValue(item.env_keys),
    group: item.group ?? "-",
    item_type: item.item_type ?? "-",
    next_action: item.next_action ?? "-",
    required_value: item.required_value ?? "-",
    secret: item.secret ? "yes" : "no",
    status: item.status ?? "-",
    target: item.target ?? item.target_id ?? "-",
  }));
}

function formatHandshakeRouteRows(rows: LiveAdapterRouteHandshake[]): TableRow[] {
  return rows.map((route) => ({
    adapter_id: route.adapter_id,
    ready_targets: `${route.route_handshake_ready_count ?? 0}/${route.route_handshake_target_count ?? 0}`,
    route_handshake_blockers: listValue(route.route_handshake_blockers),
    route_handshake_next_action: route.route_handshake_next_action ?? "-",
    route_handshake_status: route.route_handshake_status?.replaceAll("_", " ") ?? "-",
  }));
}

function listValue(items?: string[]) {
  if (!items?.length) {
    return "-";
  }

  return items.join(" | ");
}

function formatHandshakeActivationRows(
  rows: LiveAdapterHandshakeEnvActivationGuide[],
): TableRow[] {
  return rows.map((row) => ({
    activation_status: row.activation_status,
    configured: `${row.configured_count ?? 0}/${row.required_count ?? 0}`,
    drill: row.handshake_drill_enabled_after_setup ? "enabled after recheck" : "locked until setup",
    endpoint_status: row.endpoint_status,
    market_family: row.market_family,
    missing_env_keys: row.missing_env_keys ?? [],
    mode_status: row.mode_status,
    next_unlock_label: row.next_unlock_label,
    route_label: row.route_label,
    secret_env_keys: row.secret_env_keys ?? [],
  }));
}

function formatHandshakeActivationSteps(
  rows: LiveAdapterHandshakeEnvActivationGuide[],
): TableRow[] {
  return rows.map((row) => ({
    route_label: row.route_label,
    safe_deployment_steps: row.safe_deployment_steps ?? [],
    secret_values_exposed: row.secret_values_exposed ? "yes" : "no",
  }));
}

function credentialTone(value: unknown) {
  if (value === "credentials_configured") {
    return "emerald";
  }

  if (value === "partial_credentials") {
    return "amber";
  }

  if (value === "credentials_missing") {
    return "red";
  }

  return "slate";
}

function handshakeTone(value: unknown) {
  if (value === "handshake_ready") {
    return "emerald";
  }

  if (value === "partial_handshake_ready") {
    return "blue";
  }

  if (value === "handshake_blocked" || value === "handshake_disabled") {
    return "amber";
  }

  return "slate";
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
