"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { DataTable } from "@/components/data-table";
import { DecisionBrief, type DecisionBriefTone } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatDateTime, formatNumber } from "@/lib/format";
import type {
  MarketConnectorReadiness,
  MarketConnectorReadinessResponse,
  PersistenceReadinessResponse,
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

  const persistence = useQuery({
    queryFn: () =>
      apiGet<PersistenceReadinessResponse>("/system/persistence-readiness"),
    queryKey: ["system-persistence-readiness"],
  });

  const data = connectors.data;
  const persistenceData = persistence.data;
  const persistenceSummary = persistenceData?.summary ?? {};
  const summary = data?.summary ?? {};
  const rows = data?.integrations ?? data?.connectors ?? [];
  const marketRows = rows.filter((row) => row.integration_type === "market_connector");
  const wholesaleRows = rows.filter((row) => row.family === "wholesale");
  const ancillaryRows = rows.filter((row) => row.family === "ancillary");
  const dataRows = rows.filter((row) =>
    ["asset", "data", "settlement"].includes(String(row.family)),
  );
  const connectorBlockers = buildConnectorBlockers(rows, data, persistenceData);
  const recommendedActions = [
    ...(data?.recommended_actions ?? []),
    ...(persistenceData?.recommended_actions ?? []),
  ];

  return (
    <>
      <PageHeading
        description="Track the live-automation integration path across forecasts, prices, EMS telemetry, EPEX wholesale markets, regelleistung ancillary services, and settlement evidence."
        eyebrow="Automated trading"
        title="Data & Connector Readiness"
      />

      <div className="mb-6">
        <DecisionBrief
          blockers={connectorBlockers.slice(0, 4)}
          decision={
            Number(summary.production_ready_count ?? 0) > 0
              ? `${summary.production_ready_count} market route(s) can support production automation.`
              : "Automation cannot reach a production market route yet."
          }
          evidence={[
            `${summary.epex_count ?? wholesaleRows.length} EPEX route(s), ${summary.ancillary_count ?? ancillaryRows.length} ancillary route(s).`,
            `${summary.credentials_required_count ?? 0} credential gap(s) and ${persistenceSummary.blocked ?? 0} persistence blocker(s).`,
            `Average readiness ${formatNumber(summary.average_readiness_score, 1)}/100.`,
          ]}
          eyebrow="Market access decision"
          nextAction={
            recommendedActions[0] ??
            "Connect price, telemetry, exchange, TSO, and settlement evidence before live automation."
          }
          title="Can automation reach the market?"
          tone={connectorDecisionTone(data, persistenceData)}
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <KpiCard
          accent={statusTone(data?.connector_status)}
          helper="Portfolio connector status"
          label="Connector status"
          value={data?.connector_status ?? "-"}
        />
        <KpiCard
          accent="blue"
          helper={`${summary.epex_count ?? wholesaleRows.length} EPEX / ${summary.ancillary_count ?? ancillaryRows.length} ancillary`}
          label="Market routes"
          value={marketRows.length}
        />
        <KpiCard
          accent={Number(summary.production_ready_count ?? 0) ? "emerald" : "slate"}
          helper="Live submission routes"
          label="Production ready"
          value={summary.production_ready_count ?? 0}
        />
        <KpiCard
          accent={Number(summary.credentials_required_count ?? 0) ? "amber" : "emerald"}
          helper="Missing data, exchange, or TSO secrets"
          label="Credentials required"
          value={summary.credentials_required_count ?? 0}
        />
        <KpiCard
          accent="blue"
          helper={`Generated ${formatDateTime(data?.generated_at)}`}
          label="Average readiness"
          value={`${formatNumber(summary.average_readiness_score, 1)}/100`}
        />
        <KpiCard
          accent={persistenceTone(persistenceData?.persistence_status)}
          helper={`${persistenceSummary.blocked ?? 0} blocked persistence checks`}
          label="Persistence"
          value={persistenceData?.persistence_status ?? "-"}
        />
      </div>

      <SectionCard
        action={
          <StatusPill tone={persistenceTone(persistenceData?.persistence_status)}>
            {persistenceData?.automation_blocking_level ?? "not blocking"}
          </StatusPill>
        }
        className="mb-5"
        title="Persistence readiness"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Database
            </div>
            <div className="mt-2 break-all text-xs leading-5 text-slate-300">
              {persistenceData?.database_file ?? "-"}
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Passed
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {persistenceSummary.passed ?? 0}
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Blocked
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {persistenceSummary.blocked ?? 0}
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Missing tables
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {persistenceSummary.missing_tables?.length ?? 0}
            </div>
          </div>
        </div>
        <DataTable
          columns={["check", "label", "status", "message", "evidence"]}
          rows={(persistenceData?.checks ?? []).slice(0, 6)}
        />
      </SectionCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.75fr)]">
        <SectionCard
          action={<StatusPill tone={statusTone(data?.connector_status)}>{data?.connector_status ?? "-"}</StatusPill>}
          title="Live automation integration matrix"
        >
          <DataTable
            columns={[
              "priority",
              "adapter_id",
              "family",
              "venue",
              "market_segment",
              "production_readiness_tier",
              "readiness_score",
              "automation_blocking_level",
              "next_integration_action",
            ]}
            rows={formatConnectorRows(rows).slice(0, 10)}
          />
        </SectionCard>

        <SectionCard title="Trading workflow impact">
          <div className="space-y-3">
            <WorkflowLink
              href="/forecasts"
              label="Forecast & Price Evidence"
              value="Blocks paper and supervised automation if stale"
            />
            <WorkflowLink
              href="/execution/audit"
              label="EMS Telemetry"
              value="Blocks limited live automation"
            />
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

      <div className="mt-5 grid gap-5 xl:grid-cols-3">
        <SectionCard title="Wholesale routes: EPEX">
          <DataTable
            columns={[
              "adapter_id",
              "market_segment",
              "production_readiness_tier",
              "automation_blocking_level",
              "next_integration_action",
            ]}
            rows={formatConnectorRows(wholesaleRows).slice(0, 5)}
          />
        </SectionCard>

        <SectionCard title="Ancillary services: regelleistung">
          <DataTable
            columns={[
              "adapter_id",
              "market_segment",
              "production_readiness_tier",
              "automation_blocking_level",
              "next_integration_action",
            ]}
            rows={formatConnectorRows(ancillaryRows).slice(0, 5)}
          />
        </SectionCard>

        <SectionCard title="Data, EMS, and settlement">
          <DataTable
            columns={[
              "adapter_id",
              "family",
              "production_readiness_tier",
              "automation_blocking_level",
              "next_integration_action",
            ]}
            rows={formatConnectorRows(dataRows).slice(0, 5)}
          />
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Missing integration controls">
          <DataTable
            columns={["adapter_id", "family", "automation_blocking_level", "missing_credentials", "missing_controls"]}
            rows={formatMissingRows(rows).slice(0, 8)}
          />
        </SectionCard>

        <SectionCard title="Recommended integration actions">
          <DataTable
            columns={["priority", "action"]}
            rows={recommendedActions.slice(0, 8).map((action, index) => ({
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
  return rows
    .filter(
      (row) =>
        (row.missing_controls?.length ?? 0) > 0 ||
        (row.missing_credentials?.length ?? 0) > 0 ||
        row.automation_blocking_level === "blocked",
    )
    .map((row) => ({
      adapter_id: row.adapter_id,
      automation_blocking_level: row.automation_blocking_level,
      family: row.family,
      missing_controls: row.missing_controls?.join(" | ") || "-",
      missing_credentials: row.missing_credentials?.join(" | ") || "-",
    }));
}

function buildConnectorBlockers(
  rows: MarketConnectorReadiness[],
  data?: MarketConnectorReadinessResponse,
  persistence?: PersistenceReadinessResponse,
) {
  const blockers = [
    ...(rows
      .filter((row) => row.automation_blocking_level === "blocked")
      .map((row) => `${row.adapter_id}: ${row.next_integration_action ?? "integration required"}`)),
    ...(persistence?.checks ?? [])
      .filter((check) => check.status === "blocked")
      .map((check) => String(check.message ?? check.label ?? check.check ?? "Persistence blocker")),
  ];

  if (!Number(data?.summary?.production_ready_count ?? 0)) {
    blockers.unshift("No production-ready market connector is available.");
  }

  return blockers;
}

function connectorDecisionTone(
  data?: MarketConnectorReadinessResponse,
  persistence?: PersistenceReadinessResponse,
): DecisionBriefTone {
  if (persistence?.persistence_status === "blocked") {
    return "red";
  }

  if (Number(data?.summary?.production_ready_count ?? 0) > 0) {
    return "emerald";
  }

  if (data?.connector_status === "preview_and_paper_ready") {
    return "blue";
  }

  if (data?.connector_status === "credentials_required") {
    return "amber";
  }

  return "slate";
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

function persistenceTone(value: unknown) {
  if (value === "ready") {
    return "emerald";
  }

  if (value === "review") {
    return "amber";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}
