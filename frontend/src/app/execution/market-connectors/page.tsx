"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatDateTime, formatNumber } from "@/lib/format";
import type {
  MarketConnectorReadiness,
  MarketConnectorReadinessResponse,
  TableRow,
} from "@/types/api";

export default function MarketConnectorsPage() {
  const connectors = useQuery({
    queryFn: () =>
      apiGet<MarketConnectorReadinessResponse>(
        "/execution/market-connectors/readiness?country=Germany",
      ),
    queryKey: ["market-connectors-readiness"],
  });

  const data = connectors.data;
  const summary = data?.summary ?? {};
  const rows = data?.connectors ?? [];

  return (
    <>
      <PageHeading
        description="Track the German market connector path from preview and paper mode toward supervised live EPEX and regelleistung trading."
        eyebrow="Trading operations"
        title="Market connectors"
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <KpiCard
          accent={statusTone(data?.connector_status)}
          helper="Portfolio connector status"
          label="Connector status"
          value={data?.connector_status ?? "-"}
        />
        <KpiCard
          accent="blue"
          helper="EPEX and regelleistung routes"
          label="Connectors"
          value={summary.connector_count ?? rows.length}
        />
        <KpiCard
          accent={Number(summary.production_ready_count ?? 0) ? "emerald" : "slate"}
          helper="Live submission routes"
          label="Production ready"
          value={summary.production_ready_count ?? 0}
        />
        <KpiCard
          accent={Number(summary.credentials_required_count ?? 0) ? "amber" : "emerald"}
          helper="Missing exchange/TSO secrets"
          label="Credentials required"
          value={summary.credentials_required_count ?? 0}
        />
        <KpiCard
          accent="blue"
          helper={`Generated ${formatDateTime(data?.generated_at)}`}
          label="Average readiness"
          value={`${formatNumber(summary.average_readiness_score, 1)}/100`}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.75fr)]">
        <SectionCard
          action={<StatusPill tone={statusTone(data?.connector_status)}>{data?.connector_status ?? "-"}</StatusPill>}
          title="Connector readiness matrix"
        >
          <DataTable
            columns={[
              "priority",
              "adapter_id",
              "venue",
              "market_segment",
              "production_readiness_tier",
              "readiness_score",
              "credential_status",
              "preview_available",
              "paper_supported",
              "live_submission",
              "next_integration_action",
            ]}
            rows={formatConnectorRows(rows)}
          />
        </SectionCard>

        <SectionCard title="Trading workflow impact">
          <div className="space-y-3">
            <WorkflowLink
              href="/execution/orchestrator"
              label="Trading Orchestrator"
              value="Uses connector status to pause or continue"
            />
            <WorkflowLink
              href="/execution/automation-policies"
              label="Automation Policies"
              value="Defines which connectors are allowed"
            />
            <WorkflowLink
              href="/execution/market-allocation"
              label="Market Allocation"
              value="Ranks only eligible market routes"
            />
            <WorkflowLink
              href="/market-rules"
              label="Market Rules"
              value="Shows gate and product constraints"
            />
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Missing connector controls">
          <DataTable
            columns={["adapter_id", "missing_credentials", "missing_controls"]}
            rows={formatMissingRows(rows)}
          />
        </SectionCard>

        <SectionCard title="Recommended integration actions">
          <DataTable
            columns={["priority", "action"]}
            rows={(data?.recommended_actions ?? []).map((action, index) => ({
              action,
              priority: index + 1,
            }))}
          />
        </SectionCard>
      </div>
    </>
  );
}

function WorkflowLink({
  href,
  label,
  value,
}: {
  href: string;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <Link
      className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3 transition hover:border-sky-400/40 hover:bg-sky-950/20"
      href={href}
    >
      <span className="text-sm font-medium text-slate-200">{label}</span>
      <span className="text-xs text-sky-200">{value}</span>
    </Link>
  );
}

function formatConnectorRows(rows: MarketConnectorReadiness[]) {
  return rows.map((row) => ({
    ...row,
    readiness_score: formatNumber(row.readiness_score, 1),
  }));
}

function formatMissingRows(rows: MarketConnectorReadiness[]): TableRow[] {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    missing_controls: row.missing_controls ?? [],
    missing_credentials: row.missing_credentials ?? [],
  }));
}

function statusTone(value: unknown) {
  if (value === "supervised_live_route_available") {
    return "emerald";
  }

  if (value === "preview_and_paper_ready") {
    return "blue";
  }

  if (value === "credentials_required") {
    return "amber";
  }

  if (value === "integration_required") {
    return "red";
  }

  return "slate";
}
