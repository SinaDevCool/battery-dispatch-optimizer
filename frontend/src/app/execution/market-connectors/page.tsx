"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
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
  LiveAdapterHandshakeEnvActivationGuide,
  LiveAdapterHandshakeEnvItem,
  LiveAdapterHandshakeHistoryResponse,
  OfficialApiComplianceRoute,
  OfficialApiEvidenceRequirement,
  OfficialApiEvidenceVaultResponse,
  PersistenceReadinessResponse,
  RouteAutomationCertification,
  TableRow,
} from "@/types/api";

export default function MarketConnectorsPage() {
  const { selectedAssetId } = useAssetContext();

  const connectors = useQuery({
    queryFn: () =>
      apiGet<MarketConnectorReadinessResponse>(
        `/execution/market-connectors/readiness?country=Germany&asset_id=${selectedAssetId}`,
      ),
    queryKey: ["market-connectors-readiness", selectedAssetId],
  });

  const persistence = useQuery({
    queryFn: () =>
      apiGet<PersistenceReadinessResponse>("/system/persistence-readiness"),
    queryKey: ["system-persistence-readiness"],
  });

  const handshakeHistory = useQuery({
    queryFn: () =>
      apiGet<LiveAdapterHandshakeHistoryResponse>(
        `/execution/market-connectors/live-handshake/history?asset_id=${selectedAssetId}&limit=6`,
      ),
    queryKey: ["market-connectors-live-handshake-history", selectedAssetId],
  });

  const officialEvidence = useQuery({
    queryFn: () =>
      apiGet<OfficialApiEvidenceVaultResponse>(
        "/execution/market-connectors/official-api-evidence?country=Germany",
      ),
    queryKey: ["market-connectors-official-api-evidence"],
  });

  const data = connectors.data;
  const officialEvidenceData = officialEvidence.data;
  const officialEvidenceSummary = officialEvidenceData?.summary ?? {};
  const persistenceData = persistence.data;
  const persistenceSummary = persistenceData?.summary ?? {};
  const summary = data?.summary ?? {};
  const rows = data?.integrations ?? data?.connectors ?? [];
  const marketRows = rows.filter((row) => row.integration_type === "market_connector");
  const routeCertifications = data?.route_certifications ?? [];
  const officialApiCompliance = data?.official_api_compliance ?? [];
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
            `${summary.configured_market_lifecycle_count ?? 0} route lifecycle(s) configured; next gate ${formatDateTime(summary.next_gate_closure_at)}.`,
            `${summary.preview_contract_ready_count ?? 0} connector contract(s) have full preview method coverage.`,
            `${summary.official_api_compliant_route_count ?? 0}/${summary.official_api_route_count ?? 0} route(s) meet official EPEX/regelleistung API gates.`,
            `${summary.paper_certified_count ?? 0} route(s) certified for automated paper execution; ${summary.supervised_live_certified_count ?? 0} for supervised live.`,
            `${summary.certified_route_count ?? 0}/${summary.route_certification_count ?? 0} route(s) have route-level automation certification.`,
            `${summary.supervised_live_candidate_count ?? 0} route(s) clear the supervised-live gate; ${summary.paper_ready_live_blocked_count ?? 0} are paper-ready but live-blocked.`,
            `${summary.configured_credential_count ?? 0}/${summary.credential_count ?? 0} credential item(s) configured.`,
            `${summary.handshake_ready_count ?? 0}/${summary.handshake_target_count ?? 0} live adapter handshake target(s) are dry-run ready.`,
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

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-8">
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
          accent={Number(summary.configured_market_lifecycle_count ?? 0) ? "emerald" : "amber"}
          helper={`Next gate ${formatDateTime(summary.next_gate_closure_at)}`}
          label="Lifecycle rules"
          value={summary.configured_market_lifecycle_count ?? 0}
        />
        <KpiCard
          accent={Number(summary.credentials_required_count ?? 0) ? "amber" : "emerald"}
          helper={`${summary.configured_credential_count ?? 0}/${summary.credential_count ?? 0} onboarding items configured`}
          label="Credentials"
          value={data?.credential_readiness_status ?? summary.credentials_required_count ?? "-"}
        />
        <KpiCard
          accent={officialApiTone(data?.official_api_compliance_status)}
          helper={`${officialEvidenceSummary.approved_evidence_count ?? summary.official_api_passed_check_count ?? 0}/${officialEvidenceSummary.required_evidence_count ?? summary.official_api_check_count ?? 0} official evidence records approved`}
          label="Official API"
          value={data?.official_api_compliance_status ?? "-"}
        />
        <KpiCard
          accent={Number(summary.missing_method_count ?? 0) ? "amber" : "emerald"}
          helper={`${summary.preview_contract_ready_count ?? 0} full preview / ${summary.partial_contract_count ?? 0} partial`}
          label="Connector contract"
          value={data?.connector_contract_status ?? "-"}
        />
        <KpiCard
          accent={routeCertificationTone(data?.route_certification_status)}
          helper={`${summary.ready_for_drill_count ?? 0} ready for drill / ${summary.drill_failed_count ?? 0} failed`}
          label="Route certification"
          value={data?.route_certification_status ?? "-"}
        />
        <KpiCard
          accent={certificationTone(data?.sandbox_certification_status)}
          helper={`${summary.paper_certified_count ?? 0} paper / ${summary.supervised_live_certified_count ?? 0} supervised live`}
          label="Sandbox certification"
          value={data?.sandbox_certification_status ?? "-"}
        />
        <KpiCard
          accent={supervisedGateTone(data?.supervised_live_gate_status)}
          helper={`${summary.supervised_live_candidate_count ?? 0} candidate / ${summary.paper_ready_live_blocked_count ?? 0} blocked`}
          label="Supervised live gate"
          value={data?.supervised_live_gate_status ?? "-"}
        />
        <KpiCard
          accent={handshakeTone(data?.handshake_readiness_status)}
          helper={`${summary.env_configured_count ?? 0}/${summary.env_checklist_count ?? 0} env items configured`}
          label="Live handshake"
          value={data?.handshake_readiness_status ?? "-"}
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

      <SectionCard
        action={
          <StatusPill tone={officialApiTone(data?.official_api_compliance_status)}>
            {data?.official_api_compliance_status?.replaceAll("_", " ") ?? "-"}
          </StatusPill>
        }
        className="mt-5"
        title="Official API compliance"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Compliant routes
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {summary.official_api_compliant_route_count ?? 0}/{summary.official_api_route_count ?? 0}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              EPEX MATS, EPEX M7, and regelleistung BSP API gates.
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Official check score
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {formatNumber(summary.average_official_api_compliance_score, 1)}/100
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              Routes fail closed until all required official checks pass.
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Blocked routes
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {summary.official_api_blocked_route_count ?? 0}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              Missing official docs, access, conformance, schemas, or certificates.
            </div>
          </div>
        </div>
        <DataTable
          columns={[
            "adapter_id",
            "official_system",
            "official_api_compliance_status",
            "official_api_compliance_score",
            "official_api_passed",
            "access_model",
            "required_access_modes",
            "fail_closed",
            "official_api_next_action",
          ]}
          rows={formatOfficialApiRows(officialApiCompliance)}
        />
      </SectionCard>

      <SectionCard
        action={
          <StatusPill tone={evidenceVaultTone(officialEvidenceData?.evidence_vault_status)}>
            {officialEvidenceData?.evidence_vault_status?.replaceAll("_", " ") ?? "loading"}
          </StatusPill>
        }
        className="mt-5"
        title="Official evidence vault"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Approved proof
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {officialEvidenceSummary.approved_evidence_count ?? 0}/{officialEvidenceSummary.required_evidence_count ?? 0}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              Official docs, exchange/TSO access, conformance, and schema evidence.
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Missing
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {officialEvidenceSummary.missing_evidence_count ?? 0}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              Live automation stays fail-closed while proof is missing.
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Review
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {officialEvidenceSummary.review_evidence_count ?? 0}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              Uploaded proof exists but has not been approved.
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Expired
            </div>
            <div className="mt-2 text-lg font-semibold text-white">
              {officialEvidenceSummary.expired_evidence_count ?? 0}
            </div>
            <div className="mt-1 text-xs leading-5 text-slate-400">
              Evidence must be renewed before it can unlock trading.
            </div>
          </div>
        </div>
        <DataTable
          columns={[
            "adapter_id",
            "official_system",
            "requirement_id",
            "label",
            "evidence_readiness",
            "evidence_status",
            "evidence_owner",
            "evidence_reference",
            "recorded_at",
            "expires_at",
            "review_at",
            "unlocks_mode",
            "required_env_keys",
            "next_action",
          ]}
          rows={formatOfficialEvidenceRows(officialEvidenceData?.requirements ?? [])}
        />
      </SectionCard>

      <SectionCard
        action={
          <StatusPill tone={routeCertificationTone(data?.route_certification_status)}>
            {data?.route_certification_status?.replaceAll("_", " ") ?? "-"}
          </StatusPill>
        }
        className="mt-5"
        title="Route automation certification"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {routeCertifications.slice(0, 6).map((route) => (
            <div
              className="rounded-lg border border-slate-800 bg-slate-900/45 p-4"
              key={route.adapter_id ?? route.market_segment}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-100">
                    {route.adapter_name ?? route.adapter_id}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {route.market_segment?.replaceAll("_", " ") ?? route.venue ?? "market route"}
                  </div>
                </div>
                <StatusPill tone={routeCertificationTone(route.route_certification_stage)}>
                  {route.route_certification_stage?.replaceAll("_", " ") ?? "not evaluated"}
                </StatusPill>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
                <RouteCertMetric label="Score" value={`${formatNumber(route.route_certification_score, 1)}/100`} />
                <RouteCertMetric label="Drill" value={route.latest_route_drill_status ?? "-"} />
                <RouteCertMetric label="Targets" value={route.latest_route_drill_target_count ?? "-"} />
              </div>
              <div className="mt-4 text-xs leading-5 text-slate-400">
                {route.route_certification_next_action ?? "Review route certification evidence."}
              </div>
            </div>
          ))}
        </div>
        <DataTable
          columns={[
            "adapter_id",
            "route_certification_stage",
            "route_certification_score",
            "latest_route_drill_status",
            "certified_for_paper",
            "certified_for_supervised",
            "certified_for_live",
            "route_certification_blockers",
            "route_certification_next_action",
          ]}
          rows={formatRouteCertificationRows(routeCertifications)}
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
              "trading_clock_status",
              "gate_closure_label",
              "automation_lane",
              "production_readiness_tier",
              "official_api_compliance_status",
              "connector_contract_status",
              "sandbox_certification_status",
              "supervised_live_gate_status",
              "route_certification_stage",
              "route_handshake_status",
              "route_credential_status",
              "method_coverage",
              "readiness_score",
              "automation_blocking_level",
              "next_deadline_action",
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

      <SectionCard
        action={
          <StatusPill tone={contractTone(data?.connector_contract_status)}>
            {data?.connector_contract_status ?? "-"}
          </StatusPill>
        }
        className="mt-5"
        title="Connector contract coverage"
      >
        <DataTable
          columns={[
            "adapter_id",
            "connector_family",
            "connector_contract_status",
            "implemented_methods",
            "missing_methods",
            "live_method_count",
            "raw_reference_fields",
            "contract_next_action",
          ]}
          rows={formatConnectorContractRows(marketRows)}
        />
      </SectionCard>

      <SectionCard
        action={
          <StatusPill tone={certificationTone(data?.sandbox_certification_status)}>
            {data?.sandbox_certification_status ?? "-"}
          </StatusPill>
        }
        className="mt-5"
        title="Live connector sandbox certification"
      >
        <DataTable
          columns={[
            "adapter_id",
            "market_segment",
            "sandbox_certification_status",
            "certified_for_paper",
            "certified_for_supervised_live",
            "passed_method_count",
            "blocked_reasons",
            "next_certification_action",
          ]}
          rows={formatCertificationRows(marketRows)}
        />
      </SectionCard>

      <SectionCard
        action={
          <StatusPill tone={supervisedGateTone(data?.supervised_live_gate_status)}>
            {data?.supervised_live_gate_status ?? "-"}
          </StatusPill>
        }
        className="mt-5"
        title="Supervised live readiness gate"
      >
        <DataTable
          columns={[
            "adapter_id",
            "market_segment",
            "supervised_live_gate_status",
            "gate_score",
            "gate_passed_count",
            "supervised_live_candidate",
            "supervised_live_blockers",
            "supervised_live_next_action",
          ]}
          rows={formatSupervisedGateRows(marketRows)}
        />
      </SectionCard>

      <SectionCard className="mt-5" title="Credential onboarding by route">
        <DataTable
          columns={[
            "adapter_id",
            "market_segment",
            "route_credential_status",
            "route_missing_credentials",
            "route_missing_env_keys",
            "route_onboarding_next_action",
          ]}
          rows={formatRouteCredentialRows(marketRows)}
        />
      </SectionCard>

      <SectionCard
        action={
          <div className="flex flex-wrap items-start gap-2">
            <ActionButton
              endpoint={`/execution/market-connectors/live-handshake/run?asset_id=${selectedAssetId}&country=Germany`}
              label="Run drill"
              refetch={() => Promise.all([connectors.refetch(), handshakeHistory.refetch()])}
              variant="primary"
            />
            <StatusPill tone={handshakeTone(data?.handshake_readiness_status)}>
              {data?.handshake_readiness_status ?? "-"}
            </StatusPill>
          </div>
        }
        className="mt-5"
        title="Live adapter handshake readiness"
      >
        <div className="space-y-4">
          <DataTable
            columns={[
              "adapter_id",
              "market_segment",
              "route_handshake_status",
              "route_handshake_ready",
              "route_handshake_targets",
              "route_handshake_blockers",
              "route_handshake_next_action",
            ]}
            rows={formatHandshakeRows(rows)}
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
          <DataTable
            columns={[
              "route_label",
              "market_family",
              "activation_status",
              "configured",
              "next_unlock_label",
              "missing_env_keys",
              "secret_env_keys",
              "drill",
            ]}
            rows={formatActivationGuideRows(data?.handshake_env_activation_guide ?? [])}
          />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(data?.handshake_env_activation_guide ?? []).map((route) => (
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
                  {route.handshake_drill_enabled_after_setup && route.route_drill_endpoint ? (
                    <ActionButton
                      endpoint={route.route_drill_endpoint}
                      label="Run route drill"
                      refetch={() => Promise.all([connectors.refetch(), handshakeHistory.refetch()])}
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
          <DataTable
            columns={[
              "route_label",
              "safe_deployment_steps",
              "secret_values_exposed",
            ]}
            rows={formatActivationGuideSteps(data?.handshake_env_activation_guide ?? [])}
          />
          <DataTable
            columns={[
              "target",
              "item_type",
              "status",
              "env_keys",
              "required_value",
              "configured_env_key",
              "blocks_routes",
              "next_action",
            ]}
            rows={formatHandshakeEnvRows(data?.handshake_env_checklist ?? [])}
          />
        </div>
      </SectionCard>

      <div className="mt-5 grid gap-5 xl:grid-cols-3">
        <SectionCard title="Wholesale routes: EPEX">
          <DataTable
            columns={[
              "adapter_id",
              "market_segment",
              "gate_closure_label",
              "order_style",
              "connector_contract_status",
              "production_readiness_tier",
              "automation_blocking_level",
              "next_deadline_action",
            ]}
            rows={formatConnectorRows(wholesaleRows).slice(0, 5)}
          />
        </SectionCard>

        <SectionCard title="Ancillary services: regelleistung">
          <DataTable
            columns={[
              "adapter_id",
              "market_segment",
              "gate_closure_label",
              "order_style",
              "connector_contract_status",
              "production_readiness_tier",
              "automation_blocking_level",
              "next_deadline_action",
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

function RouteCertMetric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950/45 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 break-words text-xs font-semibold text-slate-100">
        {value}
      </div>
    </div>
  );
}

function formatConnectorRows(rows: MarketConnectorReadiness[]) {
  return rows.map((row) => ({
    ...row,
    automation_lane: row.automation_lane?.replaceAll("_", " ") ?? "-",
    connector_contract_status: row.connector_contract_status?.replaceAll("_", " ") ?? "-",
    gate_closure_label: row.gate_closure_label ?? "-",
    method_coverage: row.method_coverage ? `${formatNumber(row.method_coverage, 1)}%` : "-",
    next_deadline_action: row.next_deadline_action ?? row.next_integration_action ?? "-",
    official_api_compliance_status: row.official_api_compliance_status?.replaceAll("_", " ") ?? "-",
    order_style: row.order_style?.replaceAll("_", " ") ?? "-",
    readiness_score: formatNumber(row.readiness_score, 1),
    route_credential_status: row.route_credential_status?.replaceAll("_", " ") ?? "-",
    route_certification_stage: row.route_certification_stage?.replaceAll("_", " ") ?? "-",
    route_handshake_status: row.route_handshake_status?.replaceAll("_", " ") ?? "-",
    sandbox_certification_status: row.sandbox_certification_status?.replaceAll("_", " ") ?? "-",
    supervised_live_gate_status: row.supervised_live_gate_status?.replaceAll("_", " ") ?? "-",
    trading_clock_status: row.trading_clock_status?.replaceAll("_", " ") ?? "-",
  }));
}

function formatOfficialApiRows(rows: OfficialApiComplianceRoute[]): TableRow[] {
  return rows.map((row) => ({
    access_model: row.access_model?.replaceAll("_", " ") ?? "-",
    adapter_id: row.adapter_id,
    fail_closed: row.fail_closed ? "yes" : "no",
    official_api_compliance_score: `${formatNumber(row.official_api_compliance_score, 1)}/100`,
    official_api_compliance_status: row.official_api_compliance_status?.replaceAll("_", " ") ?? "-",
    official_api_next_action: row.official_api_next_action ?? "-",
    official_api_passed: `${row.official_api_passed_count ?? 0}/${row.official_api_check_count ?? 0}`,
    official_system: row.official_system ?? "-",
    required_access_modes: compactList(row.required_access_modes),
  }));
}

function formatOfficialEvidenceRows(rows: OfficialApiEvidenceRequirement[]): TableRow[] {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    evidence_owner: row.evidence_owner ?? "-",
    evidence_readiness: row.evidence_readiness?.replaceAll("_", " ") ?? "-",
    evidence_reference: row.evidence_reference ?? "-",
    evidence_status: row.evidence_status?.replaceAll("_", " ") ?? "-",
    expires_at: formatDateTime(row.expires_at),
    label: row.label ?? "-",
    next_action: row.next_action ?? "-",
    official_system: row.official_system ?? "-",
    recorded_at: formatDateTime(row.recorded_at),
    requirement_id: row.requirement_id ?? "-",
    required_env_keys: compactList(row.required_env_keys),
    review_at: formatDateTime(row.review_at),
    unlocks_mode: row.unlocks_mode?.replaceAll("_", " ") ?? "-",
  }));
}

function formatRouteCertificationRows(rows: RouteAutomationCertification[]): TableRow[] {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    certified_for_live: row.certified_for_live ? "yes" : "no",
    certified_for_paper: row.certified_for_paper ? "yes" : "no",
    certified_for_supervised: row.certified_for_supervised ? "yes" : "no",
    latest_route_drill_status: row.latest_route_drill_status ?? "-",
    route_certification_blockers: compactList(row.route_certification_blockers),
    route_certification_next_action: row.route_certification_next_action ?? "-",
    route_certification_score: `${formatNumber(row.route_certification_score, 1)}/100`,
    route_certification_stage: row.route_certification_stage?.replaceAll("_", " ") ?? "-",
  }));
}

function formatRouteCredentialRows(rows: MarketConnectorReadiness[]): TableRow[] {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    market_segment: row.market_segment?.replaceAll("_", " ") ?? "-",
    route_credential_status: row.route_credential_status?.replaceAll("_", " ") ?? "-",
    route_missing_credentials: compactList(row.route_missing_credentials),
    route_missing_env_keys: compactList(row.route_missing_env_keys),
    route_onboarding_next_action: row.route_onboarding_next_action ?? "-",
  }));
}

function formatHandshakeRows(rows: MarketConnectorReadiness[]): TableRow[] {
  return rows
    .filter((row) => row.route_handshake_status)
    .map((row) => ({
      adapter_id: row.adapter_id,
      market_segment: row.market_segment?.replaceAll("_", " ") ?? "-",
      route_handshake_blockers: compactList(row.route_handshake_blockers),
      route_handshake_next_action: row.route_handshake_next_action ?? "-",
      route_handshake_ready: row.route_handshake_ready ? "yes" : "no",
      route_handshake_status: row.route_handshake_status?.replaceAll("_", " ") ?? "-",
      route_handshake_targets: compactList(row.route_handshake_targets),
    }));
}

function formatHandshakeHistoryRows(rows: TableRow[]): TableRow[] {
  return rows.map((row) => ({
    action: String(row.action ?? "-").replaceAll("_", " "),
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
    blocks_routes: compactList(item.blocks_routes),
    configured_env_key: item.configured_env_key ?? "-",
    env_keys: compactList(item.env_keys),
    item_type: item.item_type ?? "-",
    next_action: item.next_action ?? "-",
    required_value: item.required_value ?? "-",
    status: item.status ?? "-",
    target: item.target ?? item.target_id ?? "-",
  }));
}

function formatActivationGuideRows(rows: LiveAdapterHandshakeEnvActivationGuide[]): TableRow[] {
  return rows.map((row) => ({
    activation_status: row.activation_status,
    configured: `${row.configured_count ?? 0}/${row.required_count ?? 0}`,
    drill: row.handshake_drill_enabled_after_setup ? "enabled after recheck" : "locked until setup",
    market_family: row.market_family,
    missing_env_keys: compactList(row.missing_env_keys),
    next_unlock_label: row.next_unlock_label,
    route_label: row.route_label,
    secret_env_keys: compactList(row.secret_env_keys),
  }));
}

function formatActivationGuideSteps(rows: LiveAdapterHandshakeEnvActivationGuide[]): TableRow[] {
  return rows.map((row) => ({
    route_label: row.route_label,
    safe_deployment_steps: compactList(row.safe_deployment_steps),
    secret_values_exposed: row.secret_values_exposed ? "yes" : "no",
  }));
}

function formatConnectorContractRows(rows: MarketConnectorReadiness[]): TableRow[] {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    connector_contract_status: row.connector_contract_status?.replaceAll("_", " ") ?? "-",
    connector_family: row.connector_family?.replaceAll("_", " ") ?? "-",
    contract_next_action: row.contract_next_action ?? row.next_integration_action ?? "-",
    implemented_methods: compactList(row.implemented_methods),
    live_method_count: row.live_method_count ?? 0,
    missing_methods: compactList(row.missing_methods),
    raw_reference_fields: compactList(row.raw_reference_fields),
  }));
}

function formatCertificationRows(rows: MarketConnectorReadiness[]): TableRow[] {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    blocked_reasons: compactList(row.blocked_reasons),
    certified_for_paper: row.certified_for_paper ? "yes" : "no",
    certified_for_supervised_live: row.certified_for_supervised_live ? "yes" : "no",
    market_segment: row.market_segment?.replaceAll("_", " ") ?? "-",
    next_certification_action: row.next_certification_action ?? "-",
    passed_method_count: `${row.passed_method_count ?? 0}/${row.method_count ?? row.connector_methods?.length ?? "-"}`,
    sandbox_certification_status: row.sandbox_certification_status?.replaceAll("_", " ") ?? "-",
  }));
}

function formatSupervisedGateRows(rows: MarketConnectorReadiness[]): TableRow[] {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    gate_passed_count: `${row.gate_passed_count ?? 0}/${row.gate_check_count ?? "-"}`,
    gate_score: row.gate_score ? `${formatNumber(row.gate_score, 1)}%` : "-",
    market_segment: row.market_segment?.replaceAll("_", " ") ?? "-",
    supervised_live_blockers: compactList(row.supervised_live_blockers),
    supervised_live_candidate: row.supervised_live_candidate ? "yes" : "no",
    supervised_live_gate_status: row.supervised_live_gate_status?.replaceAll("_", " ") ?? "-",
    supervised_live_next_action: row.supervised_live_next_action ?? "-",
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
      missing_methods: row.missing_methods?.join(" | ") || "-",
    }));
}

function compactList(items?: string[]) {
  if (!items?.length) {
    return "-";
  }

  return items.join(" | ");
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

function contractTone(value: unknown) {
  if (value === "live_contract_available") {
    return "emerald";
  }

  if (value === "preview_contracts_available") {
    return "blue";
  }

  if (value === "partial_contracts_available") {
    return "amber";
  }

  return "slate";
}

function officialApiTone(value: unknown) {
  if (value === "official_api_compliant" || value === "compliant") {
    return "emerald";
  }

  if (value === "partial_official_api_compliance") {
    return "amber";
  }

  if (value === "official_api_blocked" || value === "blocked") {
    return "red";
  }

  return "slate";
}

function evidenceVaultTone(value: unknown) {
  if (value === "official_evidence_complete") {
    return "emerald";
  }

  if (value === "partial_official_evidence") {
    return "amber";
  }

  if (value === "official_evidence_missing") {
    return "red";
  }

  return "slate";
}

function certificationTone(value: unknown) {
  if (value === "live_certified_route_available" || value === "supervised_live_certified_route_available") {
    return "emerald";
  }

  if (value === "paper_certified_routes_available") {
    return "blue";
  }

  if (value === "sandbox_blocked") {
    return "red";
  }

  return "slate";
}

function routeCertificationTone(value: unknown) {
  if (
    value === "certified_for_live" ||
    value === "live_certified_route_available" ||
    value === "certified_for_supervised" ||
    value === "supervised_certified_route_available"
  ) {
    return "emerald";
  }

  if (
    value === "certified_for_paper" ||
    value === "paper_certified_route_available" ||
    value === "routes_ready_for_drill" ||
    value === "ready_for_drill"
  ) {
    return "blue";
  }

  if (value === "route_drill_failed" || value === "drill_failed") {
    return "red";
  }

  if (value === "routes_not_configured" || value === "not_configured") {
    return "amber";
  }

  return "slate";
}

function supervisedGateTone(value: unknown) {
  if (value === "supervised_live_candidate_available") {
    return "emerald";
  }

  if (value === "paper_ready_live_blocked") {
    return "blue";
  }

  if (value === "supervised_live_blocked") {
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
