import { DataTable } from "@/components/data-table";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type { Asset, TableRow } from "@/types/api";

export function EvidenceSourceSection({
  asset,
  className,
  metadata,
  rows,
  title = "Evidence source",
}: {
  asset?: Asset;
  className?: string;
  metadata?: TableRow;
  rows?: TableRow[];
  title?: string;
}) {
  const dataMode = String(metadata?.data_mode ?? asset?.data_mode ?? "mock");

  return (
    <SectionCard
      action={
        <StatusPill tone={dataMode === "production" ? "emerald" : "blue"}>
          {formatMode(dataMode)}
        </StatusPill>
      }
      className={className}
      title={title}
    >
      <DataTable columns={["field", "value"]} rows={rows ?? buildEvidenceSourceRows(asset, metadata)} />
    </SectionCard>
  );
}

export function buildEvidenceSourceRows(
  asset?: Asset,
  metadata?: TableRow,
): TableRow[] {
  const profile = asset?.data_profile ?? {};

  return [
    {
      field: "Asset ID",
      value: metadata?.asset_id ?? asset?.asset_id ?? "-",
    },
    {
      field: "Asset type",
      value: formatEnum(metadata?.asset_type ?? asset?.asset_type),
    },
    {
      field: "Data mode",
      value: formatMode(String(metadata?.data_mode ?? asset?.data_mode ?? "mock")),
    },
    {
      field: "Mock or production",
      value: formatEnum(metadata?.mock_or_production ?? asset?.data_mode ?? "mock"),
    },
    {
      field: "Source file",
      value: metadata?.source_file ?? metadata?.forecast_file ?? profile.forecast_source ?? asset?.forecast_file ?? "-",
    },
    {
      field: "Generated at",
      value: metadata?.generated_at ?? metadata?.captured_at ?? metadata?.submitted_at ?? "-",
    },
    {
      field: "Production upgrade path",
      value: metadata?.production_upgrade_path ?? profile.production_upgrade_path ?? "-",
    },
  ];
}

export function buildArtifactSourceRows({
  asset,
  artifact,
  metadata,
}: {
  asset?: Asset;
  artifact?: TableRow;
  metadata?: TableRow;
}) {
  return [
    ...buildEvidenceSourceRows(asset, metadata).filter(
      (row) => row.field !== "Source file" && row.field !== "Generated at",
    ),
    {
      field: "Artifact",
      value: artifact?.report_title ?? artifact?.report_name ?? artifact?.status ?? "-",
    },
    {
      field: "Artifact file",
      value: artifact?.report_file ?? artifact?.scenario_file ?? artifact?.stress_file ?? "-",
    },
    {
      field: "Generated at",
      value: metadata?.generated_at ?? artifact?.generated_at ?? artifact?.captured_at ?? "-",
    },
  ];
}

function formatMode(value: string) {
  if (value === "mock") {
    return "Mock data";
  }

  if (value === "paper") {
    return "Paper trading";
  }

  if (value === "production") {
    return "Production";
  }

  return formatEnum(value);
}

function formatEnum(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return String(value).replaceAll("_", " ");
}
