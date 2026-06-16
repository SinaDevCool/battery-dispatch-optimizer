import { DataTable } from "@/components/data-table";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type { Asset, TableRow } from "@/types/api";

export function AssetDataProfileSection({
  asset,
  className,
  title = "Selected asset data profile",
}: {
  asset?: Asset;
  className?: string;
  title?: string;
}) {
  const dataMode = String(asset?.data_mode ?? "mock");

  return (
    <SectionCard
      action={<StatusPill tone={dataMode === "production" ? "emerald" : "blue"}>{formatDataMode(dataMode)}</StatusPill>}
      className={className}
      title={title}
    >
      <DataTable columns={["field", "value"]} rows={buildAssetDataProfileRows(asset)} />
    </SectionCard>
  );
}

export function buildAssetDataProfileEvidence(asset?: Asset) {
  const profile = asset?.data_profile ?? {};

  return [
    `Data mode: ${formatDataMode(asset?.data_mode)}.`,
    `Forecast source: ${formatProfileValue(profile.forecast_source ?? asset?.forecast_file)}.`,
    `Telemetry: ${formatProfileValue(profile.telemetry_mode)}.`,
    `Execution adapter: ${formatProfileValue(profile.execution_adapter)}.`,
    `Settlement: ${formatProfileValue(profile.settlement_mode)}.`,
  ];
}

export function buildAssetDataProfileRows(asset?: Asset): TableRow[] {
  const profile = asset?.data_profile ?? {};

  return [
    {
      field: "Asset",
      value: asset?.asset_name ?? asset?.site_name ?? asset?.asset_id ?? "Selected asset",
    },
    {
      field: "Asset type",
      value: formatEnumLabel(asset?.asset_type),
    },
    {
      field: "Asset subtype",
      value: formatEnumLabel(asset?.asset_subtype),
    },
    {
      field: "Data mode",
      value: formatDataMode(asset?.data_mode),
    },
    {
      field: "Mock profile",
      value: profile.label ?? asset?.data_source ?? "Configured mock profile",
    },
    {
      field: "Forecast source",
      value: formatProfileValue(profile.forecast_source ?? asset?.forecast_file),
    },
    {
      field: "Market data",
      value: formatProfileValue(profile.market_data_mode),
    },
    {
      field: "Telemetry",
      value: formatProfileValue(profile.telemetry_mode),
    },
    {
      field: "Execution adapter",
      value: formatProfileValue(profile.execution_adapter),
    },
    {
      field: "Settlement",
      value: formatProfileValue(profile.settlement_mode),
    },
    {
      field: "Production ready",
      value: profile.production_ready ?? false,
    },
  ];
}

export function formatDataMode(value?: string) {
  const normalized = String(value ?? "mock");

  if (normalized === "mock") {
    return "Mock data";
  }

  if (normalized === "paper") {
    return "Paper trading";
  }

  if (normalized === "production") {
    return "Production";
  }

  return formatEnumLabel(normalized);
}

function formatProfileValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "Not configured";
  }

  return String(value);
}

function formatEnumLabel(value?: string) {
  if (!value) {
    return "-";
  }

  return value
    .split("_")
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}
