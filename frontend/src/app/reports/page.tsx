"use client";

import { ExternalLink } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ActionButton } from "@/components/action-button";
import {
  AssetDataProfileSection,
  buildAssetDataProfileEvidence,
} from "@/components/asset-data-profile-section";
import { useAssetContext } from "@/components/asset-provider";
import { DataCompletenessPanel } from "@/components/data-completeness-panel";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import {
  buildArtifactSourceRows,
  EvidenceSourceSection,
} from "@/components/evidence-source-section";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { ProofCardGrid } from "@/components/proof-card-grid";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { usePersona } from "@/components/persona-provider";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { useApiBaseUrl } from "@/hooks/use-api-base-url";
import { apiGet } from "@/lib/api";
import { demoStatusTone, formatDemoStatus } from "@/lib/demo-status";
import type {
  ApiEnvelope,
  ClientEvidenceSummaryResponse,
  DataCompletenessResponse,
  InvestorReadinessResponse,
  MonthlyReportListResponse,
  MonthlyReportResponse,
  Asset,
  TableRow,
} from "@/types/api";
import type { PersonaId } from "@/lib/personas";

type ScenarioReportResponse = ApiEnvelope<{
  metadata?: TableRow;
  results?: TableRow[];
  scenario_proof?: {
    kpis?: TableRow[];
    rows?: TableRow[];
  };
  scenario_file?: string;
  stress_proof?: {
    kpis?: TableRow[];
    rows?: TableRow[];
  };
  stress_file?: string;
}>;

const reportTabs = [
  {
    helper: "Investment thesis, readiness score, and asset-specific investor story.",
    id: "memo",
    label: "Memo",
  },
  {
    helper: "Evidence package, proof sources, and mock-to-production boundary.",
    id: "proof",
    label: "Proof",
  },
  {
    helper: "Downside, finance, and scenario appendices for deeper diligence.",
    id: "appendix",
    label: "Appendix",
  },
  {
    helper: "Latest report, evidence readiness, delivery gaps, backend map, and archive.",
    id: "delivery",
    label: "Delivery",
  },
] as const;

type ReportTabId = (typeof reportTabs)[number]["id"];

export default function ReportsPage() {
  const apiBaseUrl = useApiBaseUrl();
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const isClientPersona = persona.layer === "client";
  const [showArchive, setShowArchive] = useState(false);
  const [activeTab, setActiveTab] = useState<ReportTabId>("memo");

  const clientEvidence = useQuery({
    queryFn: () =>
      apiGet<ClientEvidenceSummaryResponse>(
        `/assets/${selectedAssetId}/client-evidence-summary`,
      ),
    queryKey: ["client-evidence-summary", selectedAssetId],
  });

  const latest = useQuery({
    enabled: !isClientPersona,
    queryFn: () =>
      apiGet<MonthlyReportResponse>(
        `/reports/monthly/latest?asset_id=${selectedAssetId}`,
      ),
    queryKey: ["monthly-report-latest", selectedAssetId],
  });

  const archive = useQuery({
    enabled: showArchive,
    queryFn: () =>
      apiGet<MonthlyReportListResponse>(
        `/reports/monthly/list?asset_id=${selectedAssetId}`,
      ),
    queryKey: ["monthly-report-list", selectedAssetId],
  });

  const completeness = useQuery({
    enabled: !isClientPersona,
    queryFn: () =>
      apiGet<DataCompletenessResponse>(
        `/assets/${selectedAssetId}/data-completeness`,
      ),
    queryKey: ["reports-data-completeness", selectedAssetId],
  });

  const investorReadiness = useQuery({
    queryFn: () =>
      apiGet<InvestorReadinessResponse>(
        `/assets/${selectedAssetId}/investor-readiness`,
      ),
    queryKey: ["reports-investor-readiness", selectedAssetId],
  });

  const scenarios = useQuery({
    queryFn: () =>
      apiGet<ScenarioReportResponse>(
        `/assets/${selectedAssetId}/scenarios/latest`,
      ),
    queryKey: ["reports-scenarios-latest", selectedAssetId],
  });

  const stress = useQuery({
    queryFn: () =>
      apiGet<ScenarioReportResponse>(
        `/assets/${selectedAssetId}/stress/latest`,
      ),
    queryKey: ["reports-stress-latest", selectedAssetId],
  });

  const latestData = latest.data ?? clientEvidence.data?.latest_report;
  const completenessData =
    completeness.data ?? clientEvidence.data?.data_completeness;
  const readinessData = investorReadiness.data;
  const reportName = String(latestData?.report_name ?? "-");
  const reportTitle = String(
    latestData?.report_title ?? buildFriendlyReportTitle(reportName),
  );
  const reportPeriod = latestData?.report_period ?? getReportPeriod(reportName);
  const viewerRoute =
    latestData?.viewer_route ??
    `/reports/monthly/latest/view?asset_id=${selectedAssetId}`;
  const reportUrl = `${apiBaseUrl}${viewerRoute}`;
  const refetchReports = () =>
    Promise.all([
      clientEvidence.refetch(),
      latest.refetch(),
      completeness.refetch(),
      investorReadiness.refetch(),
      scenarios.refetch(),
      stress.refetch(),
      ...(showArchive ? [archive.refetch()] : []),
    ]);
  const reportDecision = buildReportDecision({
    asset: selectedAsset,
    completeness: completenessData,
    personaId,
    reportStatus: latestData?.status,
    reportName: reportTitle,
  });
  const deliveryGapRows = buildDeliveryGapRows({
    completeness: completenessData,
    reportStatus: latestData?.status,
  });
  const backendConnectionRows = buildBackendConnectionRows({
    archiveCount: archive.data?.report_count,
    completeness: completenessData,
    reportStatus: latestData?.status,
    selectedAssetId,
  });
  const backendReportProofKpis = normalizeReportProofKpis(
    clientEvidence.data?.report_proof?.kpis,
  );
  const visibleReportProofRows = clientEvidence.data?.report_proof?.rows ?? [];
  const deliveryState =
    clientEvidence.data?.summary?.delivery_status === "client_ready" ||
    !reportDecision.blockers.length
      ? "Client ready"
      : "Draft";
  const primaryDeliveryGap =
    deliveryGapRows.find((row) => row.gap !== "PDF delivery export") ??
    deliveryGapRows[0];
  const investmentMemoRows = buildInvestmentMemoRows({
    asset: selectedAsset,
    evidence: clientEvidence.data,
    readiness: readinessData,
    reportTitle,
  });
  const evidenceAppendixRows = buildEvidenceAppendixRows({
    evidence: clientEvidence.data,
    readiness: readinessData,
    selectedAssetId,
  });
  const productionDisclosureRows = buildProductionDisclosureRows({
    asset: selectedAsset,
    evidence: clientEvidence.data,
    readiness: readinessData,
    selectedAssetId,
  });
  const assetSpecificReportRows = buildAssetSpecificReportRows({
    asset: selectedAsset,
    readiness: readinessData,
  });
  const downsideAppendixRows = buildDownsideAppendixRows({
    readiness: readinessData,
    scenarios: scenarios.data,
    stress: stress.data,
  });
  const downsideAppendixTone = getDownsideAppendixTone(downsideAppendixRows);

  return (
    <>
      <PageHeading
        description={reportDecision.pageDescription}
        eyebrow={reportDecision.pageEyebrow}
        title={reportDecision.pageTitle}
      />

      <DecisionBrief
        action={
          isClientPersona ? (
            <StatusPill tone={deliveryState === "Client ready" ? "emerald" : "amber"}>
              {deliveryState}
            </StatusPill>
          ) : (
            <ActionButton
              endpoint={`/assets/${selectedAssetId}/reports/monthly/generate`}
              label="Generate client report"
              refetch={refetchReports}
              variant="primary"
            />
          )
        }
        blockers={reportDecision.blockers}
        className="mb-6"
        decision={reportDecision.decision}
        evidence={reportDecision.evidence}
        eyebrow="Client reporting decision"
        nextAction={reportDecision.nextAction}
        title={reportDecision.title}
        tone={reportDecision.tone}
      />

      {isClientPersona ? (
        <div className="mb-5 grid gap-4 md:grid-cols-3">
          <KpiCard
            accent={latestData?.status === "ok" ? "emerald" : "amber"}
            helper={latestData?.status === "ok" ? "HTML report available" : "Report not generated"}
            label="Investor report"
            value={reportTitle}
          />
          <KpiCard
            accent={deliveryState === "Client ready" ? "emerald" : "amber"}
            helper={primaryDeliveryGap?.next_action ?? "No open delivery blocker shown."}
            label="Delivery status"
            value={deliveryState}
          />
          <KpiCard
            accent={Number(completenessData?.missing_count ?? 0) > 0 ? "amber" : "emerald"}
            helper={`${completenessData?.complete_count ?? 0} of ${completenessData?.check_count ?? 0} checks complete`}
            label="Evidence readiness"
            value={`${completenessData?.score ?? "-"} / 100`}
          />
        </div>
      ) : (
        <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            helper={reportPeriod ? `Reporting period ${reportPeriod}` : "Selected asset report"}
            label="Latest report"
            value={reportTitle}
          />
          <KpiCard
            accent={deliveryState === "Client ready" ? "emerald" : "amber"}
            label="Delivery confidence"
            value={deliveryState}
            helper={latestData?.status === "ok" ? "HTML report available" : "Report not generated"}
          />
          <KpiCard
            accent={
              Number(completenessData?.missing_count ?? 0) > 0
                ? "amber"
                : "emerald"
            }
            label="Proof score"
            value={`${completenessData?.score ?? "-"} / 100`}
            helper={`${completenessData?.complete_count ?? 0} of ${completenessData?.check_count ?? 0} checks complete`}
          />
          <KpiCard
            accent="blue"
            label="Archive count"
            value={showArchive ? archive.data?.report_count ?? 0 : "not loaded"}
            helper="Load archive to inspect persisted report files"
          />
        </div>
      )}

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={reportTabs}
      />

      {activeTab === "memo" ? (
      <div className="space-y-5">
        <SectionCard
        action={
          <StatusPill tone={readinessTone(readinessData?.summary?.readiness_status)}>
            {formatReadinessStatus(readinessData?.summary?.readiness_status)}
          </StatusPill>
        }
        title="Investor memo"
      >
        <div className="mb-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,0.45fr)]">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Thesis
            </div>
            <p className="mt-3 text-base leading-7 text-slate-100">
              {readinessData?.story?.demo_thesis ?? reportDecision.decision}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
            <KpiCard
              accent={scoreAccent(readinessData?.summary?.readiness_score)}
              helper={readinessData?.summary?.recommended_next_action ?? reportDecision.nextAction}
              label="Investor readiness"
              value={
                readinessData?.summary?.readiness_score === undefined
                  ? "-"
                  : `${readinessData.summary.readiness_score}%`
              }
            />
            <KpiCard
              accent={Number(readinessData?.summary?.open_gap_count ?? 0) ? "amber" : "emerald"}
              helper={readinessData?.story?.risk_frame ?? "No investor risk frame loaded."}
              label="Open diligence gaps"
              value={readinessData?.summary?.open_gap_count ?? 0}
            />
          </div>
        </div>
        <DataTable
          columns={["memo_item", "evidence", "investor_meaning"]}
          rows={investmentMemoRows}
        />
      </SectionCard>

        <SectionCard
          action={<StatusPill tone="blue">{readinessData?.story?.investor_lens ?? "Investor lens"}</StatusPill>}
          title="Asset-specific investor framing"
        >
          <DataTable
            columns={["report_section", "asset_specific_message", "investor_question", "proof_source"]}
            rows={assetSpecificReportRows}
          />
        </SectionCard>
      </div>
      ) : null}

      {activeTab === "proof" ? (
      <div className="space-y-5">
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <SectionCard
          action={<StatusPill tone="blue">Diligence proof</StatusPill>}
          title="What the report proves"
        >
          <ProofCardGrid
            fields={[
              { key: "investor_meaning", label: "Investor meaning" },
              { key: "backend_route", label: "Source route" },
            ]}
            rows={evidenceAppendixRows}
            titleKey="evidence_layer"
          />
        </SectionCard>

        <SectionCard
          action={<StatusPill tone={demoStatusTone(selectedAsset?.data_mode ?? "mock")}>{formatDemoStatus(selectedAsset?.data_mode ?? "mock")}</StatusPill>}
          title="Demo vs production boundary"
        >
          <p className="mb-4 text-sm leading-6 text-slate-400">
            The report is ready to demonstrate the investment story. Production-ready
            status still requires live forecasts, telemetry, execution adapters, settlement
            evidence, and signed delivery controls.
          </p>
          <DataTable
            columns={["evidence_layer", "current_mock_source", "production_source", "status"]}
            rows={productionDisclosureRows}
          />
        </SectionCard>
      </div>

      <AssetDataProfileSection
        asset={selectedAsset}
        title={isClientPersona ? "Report evidence profile" : "Selected asset report evidence"}
      />

      <EvidenceSourceSection
        asset={selectedAsset}
        rows={buildArtifactSourceRows({
          asset: selectedAsset,
          artifact: latestData as TableRow | undefined,
          metadata: {
            ...(clientEvidence.data?.metadata ?? latestData?.metadata ?? {}),
            asset_id: latestData?.metadata?.asset_id ?? latestData?.asset_id ?? selectedAssetId,
            asset_type: selectedAsset?.asset_type,
            data_mode: latestData?.metadata?.data_mode ?? selectedAsset?.data_mode ?? "mock",
            mock_or_production:
              latestData?.metadata?.mock_or_production ?? selectedAsset?.data_mode ?? "mock",
          },
        })}
        title="Can this case be delivered?"
      />

      <SectionCard
        action={<StatusPill tone={demoStatusTone(selectedAsset?.data_mode ?? "mock")}>{formatDemoStatus(selectedAsset?.data_mode ?? "mock")} report proof</StatusPill>}
        title="Report proof package"
      >
        <div className="mb-4 grid gap-4 md:grid-cols-3">
          {backendReportProofKpis.map((kpi) => (
            <KpiCard
              accent={kpi.accent}
              helper={kpi.helper}
              key={kpi.label}
              label={kpi.label}
              value={kpi.value}
            />
          ))}
        </div>
        <DataTable
          columns={["report_section", "mock_evidence", "investor_meaning", "production_upgrade"]}
          rows={visibleReportProofRows}
        />
      </SectionCard>
      </div>
      ) : null}

      {activeTab === "appendix" ? (
      <div className="space-y-5">
        <SectionCard
          action={<StatusPill tone={downsideAppendixTone}>Downside appendix</StatusPill>}
          title="Downside case appendix"
        >
          <DataTable
            columns={["downside_case", "result", "readiness_impact", "report_conclusion"]}
            rows={downsideAppendixRows}
          />
        </SectionCard>

        <SectionCard
          action={<StatusPill tone="blue">Finance assumptions</StatusPill>}
          title="Project economics appendix"
        >
          <ProofCardGrid
            fields={[
              { key: "value", label: "Mock value" },
              { key: "investor_meaning", label: "Investor meaning" },
              { key: "production_upgrade", label: "Production proof needed" },
            ]}
            rows={readinessData?.project_economics ?? []}
            titleKey="metric"
          />
        </SectionCard>
      </div>
      ) : null}

      {activeTab === "delivery" ? (
      <div className="space-y-5">
        <div className="grid gap-5 xl:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <SectionCard
          action={
            <div className="flex flex-wrap items-center gap-2">
              {latestData?.status === "ok" ? (
                <StatusPill tone="emerald">Available</StatusPill>
              ) : (
                <StatusPill tone="amber">Not generated</StatusPill>
              )}
              {!isClientPersona ? (
                <ActionButton
                  endpoint={`/assets/${selectedAssetId}/reports/monthly/generate`}
                  label="Generate"
                  refetch={refetchReports}
                  variant="secondary"
                />
              ) : null}
            </div>
          }
          title={isClientPersona ? "Client-ready report" : "Latest monthly report"}
        >
          {latestData?.status === "ok" ? (
            <div className="space-y-4">
              <a
                className="inline-flex items-center gap-2 rounded-md border border-sky-400/30 bg-sky-400/10 px-4 py-2 text-sm font-semibold text-sky-100 hover:bg-sky-400/20"
                href={reportUrl}
                rel="noreferrer"
                target="_blank"
              >
                Open report
                <ExternalLink className="h-4 w-4" />
              </a>
              <DataTable
                columns={["field", "value"]}
                rows={
                  isClientPersona
                    ? [
                        { field: "Report title", value: reportTitle },
                        { field: "Report period", value: reportPeriod ?? "-" },
                        { field: "Delivery status", value: deliveryState },
                        {
                          field: "Evidence score",
                          value: `${completenessData?.score ?? "-"} / 100`,
                        },
                        {
                          field: "Asset scope",
                          value: latestData.asset_id ?? selectedAssetId,
                        },
                      ]
                    : [
                        { field: "Report title", value: reportTitle },
                        { field: "Report period", value: reportPeriod ?? "-" },
                        { field: "Report file name", value: reportName },
                        { field: "Report file", value: latestData.report_file ?? "-" },
                        { field: "Delivery status", value: "Draft HTML" },
                        {
                          field: "Viewer route",
                          value: viewerRoute,
                        },
                        {
                          field: "Asset scope",
                          value: latestData.asset_id ?? selectedAssetId,
                        },
                      ]
                }
              />
            </div>
          ) : (
            <div className="text-sm text-slate-400">
              {latestData?.message ?? "No report is available yet."}
            </div>
          )}
        </SectionCard>

        <DataCompletenessPanel
          data={completenessData}
          title="Report evidence readiness"
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <SectionCard
          action={
            <StatusPill tone={deliveryGapRows.length ? "amber" : "emerald"}>
              {deliveryGapRows.length ? `${deliveryGapRows.length} gap(s)` : "Clear"}
            </StatusPill>
          }
          title="Client delivery gaps"
        >
          <DataTable
            columns={["gap", "status", "next_action"]}
            rows={
              deliveryGapRows.length
                ? deliveryGapRows
                : [
                    {
                      gap: "Client delivery pack",
                      status: "ready",
                      next_action:
                        "Use the latest report and archive as the delivery evidence.",
                    },
                  ]
            }
          />
        </SectionCard>

        {isClientPersona ? (
          <SectionCard
            action={<StatusPill tone={deliveryState === "Client ready" ? "emerald" : "amber"}>{deliveryState}</StatusPill>}
            title="Delivery summary"
          >
            <DataTable
              columns={["field", "value"]}
              rows={[
                {
                  field: "Primary next action",
                  value: primaryDeliveryGap?.next_action ?? reportDecision.nextAction,
                },
                {
                  field: "Open evidence gaps",
                  value: completenessData?.missing_count ?? 0,
                },
                {
                  field: "Archive evidence",
                  value: showArchive
                    ? `${archive.data?.report_count ?? 0} saved report(s)`
                    : "Load previous reports to inspect archive evidence.",
                },
                {
                  field: "Client narrative",
                  value: reportDecision.evidence.at(-1) ?? "-",
                },
              ]}
            />
          </SectionCard>
        ) : (
          <SectionCard
            action={<StatusPill tone="blue">Backend linked</StatusPill>}
            title="Backend connection map"
          >
            <DataTable
              columns={["capability", "backend_route", "status", "business_value"]}
              rows={backendConnectionRows}
            />
          </SectionCard>
        )}
      </div>

      <SectionCard
        action={
          <button
            className="rounded-md border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-xs font-semibold text-sky-100 transition hover:bg-sky-400/20"
            onClick={() => setShowArchive(true)}
            type="button"
          >
            {showArchive ? "Archive loaded" : "Load archive"}
          </button>
        }
        title={isClientPersona ? "Previous reports" : "Report archive"}
      >
        {showArchive ? (
          <DataTable
            columns={["report_title", "report_period", "report_file"]}
            rows={(archive.data?.reports ?? []).map((row) => ({
              ...row,
              report_title:
                row.report_title ?? buildFriendlyReportTitle(String(row.report_name ?? "")),
              report_period:
                row.report_period ?? getReportPeriod(String(row.report_name ?? "")) ?? "-",
            }))}
          />
        ) : (
          <div className="text-sm text-slate-400">
            Previous reports are loaded on demand to keep the report readiness view fast.
          </div>
        )}
      </SectionCard>
      </div>
      ) : null}
    </>
  );
}

function buildInvestmentMemoRows({
  asset,
  evidence,
  readiness,
  reportTitle,
}: {
  asset?: Asset;
  evidence?: ClientEvidenceSummaryResponse;
  readiness?: InvestorReadinessResponse;
  reportTitle: string;
}): TableRow[] {
  const checkpoints = readiness?.checkpoints ?? [];
  const physical = checkpoints.find((checkpoint) => checkpoint.id === "physical-operation");
  const revenue = checkpoints.find((checkpoint) => checkpoint.id === "revenue-case");
  const execution = checkpoints.find((checkpoint) => checkpoint.id === "execution-safety");
  const proof = checkpoints.find((checkpoint) => checkpoint.id === "investor-proof");

  return [
    {
      evidence: readiness?.story?.demo_thesis ?? "Investor readiness thesis is not loaded.",
      investor_meaning: "The report opens with the asset thesis an investor should remember.",
      memo_item: "Investment thesis",
    },
    {
      evidence: `${readiness?.summary?.readiness_score ?? "-"}% / ${formatReadinessStatus(readiness?.summary?.readiness_status)}`,
      investor_meaning: "Readiness is computed by the backend, not assembled only in the report UI.",
      memo_item: "Readiness decision",
    },
    {
      evidence: revenue?.evidence ?? `${evidence?.summary?.modelled_revenue_eur ?? "-"} modelled revenue`,
      investor_meaning: "The commercial claim is tied to revenue stack evidence and product eligibility.",
      memo_item: "Revenue case",
    },
    {
      evidence: physical?.evidence ?? "Physical dispatch proof is not loaded.",
      investor_meaning: "The report shows the battery can physically follow the value case.",
      memo_item: "Physical proof",
    },
    {
      evidence: execution?.evidence ?? evidence?.summary?.execution_readiness_status ?? "-",
      investor_meaning: "Execution is presented as gated readiness, not an unsupported live-trading claim.",
      memo_item: "Execution state",
    },
    {
      evidence: proof?.evidence ?? `${evidence?.summary?.open_gap_count ?? "-"} open gap(s)`,
      investor_meaning: "Open gaps are visible before the report is treated as diligence-ready.",
      memo_item: "Investor proof",
    },
    {
      evidence: reportTitle,
      investor_meaning: `${getAssetReportLabel(asset)} report content should match the selected asset type.`,
      memo_item: "Report artifact",
    },
  ];
}

function buildEvidenceAppendixRows({
  evidence,
  readiness,
  selectedAssetId,
}: {
  evidence?: ClientEvidenceSummaryResponse;
  readiness?: InvestorReadinessResponse;
  selectedAssetId: string;
}): TableRow[] {
  const sourceRows = readiness?.source_rows ?? [];
  const checkpoints = readiness?.checkpoints ?? [];

  return [
    ...sourceRows.map((row) => {
      const sourceRoute = String(row.backend_route ?? "");
      const checkpoint = checkpoints.find((candidate) =>
        sourceRoute.includes(String(candidate.id ?? "").split("-")[0]),
      );

      return {
        backend_route: row.backend_route,
        evidence_layer: row.evidence_layer,
        investor_meaning:
          row.what_investor_sees ?? checkpoint?.proof_to_show ?? "Backend evidence source.",
        status: checkpoint?.status ?? "linked",
      };
    }),
    {
      backend_route: `/assets/${selectedAssetId}/client-evidence-summary`,
      evidence_layer: "Report proof",
      investor_meaning: "Packages revenue, regulatory, execution, settlement, and open gaps into the report view.",
      status: evidence?.summary?.delivery_status ?? "not_loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/investor-readiness`,
      evidence_layer: "Investment memo",
      investor_meaning: "Provides the backend readiness decision used by this report memo.",
      status: readiness?.summary?.readiness_status ?? "not_loaded",
    },
  ];
}

function buildProductionDisclosureRows({
  asset,
  evidence,
  readiness,
  selectedAssetId,
}: {
  asset?: Asset;
  evidence?: ClientEvidenceSummaryResponse;
  readiness?: InvestorReadinessResponse;
  selectedAssetId: string;
}): TableRow[] {
  const profile = asset?.data_profile ?? {};

  return [
    {
      current_mock_source: profile.forecast_source ?? asset?.forecast_file ?? "mock forecast file",
      evidence_layer: "Forecast and market prices",
      production_source: "Live forecast provider, exchange prices, actual-price archive",
      status: readiness?.metadata?.data_mode ?? asset?.data_mode ?? "mock",
    },
    {
      current_mock_source: `/assets/${selectedAssetId}/signal/latest`,
      evidence_layer: "Dispatch and physical validation",
      production_source: "EMS telemetry, measured SOC, meter readings, outage state",
      status: checkpointStatus(readiness, "physical-operation"),
    },
    {
      current_mock_source: `/assets/${selectedAssetId}/revenue-summary`,
      evidence_layer: "Revenue case",
      production_source: "Executed trades, product eligibility records, fees, settlement revenue",
      status: checkpointStatus(readiness, "revenue-case"),
    },
    {
      current_mock_source: `/assets/${selectedAssetId}/execution-summary`,
      evidence_layer: "Execution safety",
      production_source: "Exchange adapters, credentials, approval workflow, paper/live submissions",
      status: checkpointStatus(readiness, "execution-safety"),
    },
    {
      current_mock_source: evidence?.metadata?.source_file ?? "local report evidence",
      evidence_layer: "Report and audit package",
      production_source: "Signed archive, PDF export, settlement pack, audit trail",
      status: evidence?.summary?.delivery_status ?? "not_loaded",
    },
  ];
}

function buildAssetSpecificReportRows({
  asset,
  readiness,
}: {
  asset?: Asset;
  readiness?: InvestorReadinessResponse;
}): TableRow[] {
  const assetType = String(asset?.asset_type ?? "");
  const diligenceRows = readiness?.diligence_rows ?? readiness?.story?.diligence_rows ?? [];

  if (assetType.includes("solar")) {
    return [
      {
        asset_specific_message: "Frame the asset as renewable shifting, not generic arbitrage.",
        investor_question: "Can the battery charge from solar and preserve renewable-origin evidence?",
        proof_source: checkpointEvidence(readiness, "physical-operation"),
        report_section: "Renewable origin",
      },
      {
        asset_specific_message: "Show shared solar and battery export limits before revenue is trusted.",
        investor_question: "Does the schedule fit the co-located site envelope?",
        proof_source: diligenceRows[0]?.mock_evidence ?? "-",
        report_section: "Physical envelope",
      },
      {
        asset_specific_message: "Tie revenue to solar shifting and optional market routes.",
        investor_question: "What value remains after green-metering constraints?",
        proof_source: checkpointEvidence(readiness, "revenue-case"),
        report_section: "Commercial case",
      },
    ];
  }

  if (assetType.includes("industrial") || assetType.includes("behind")) {
    return [
      {
        asset_specific_message: "Frame the asset as site bill protection first, market upside second.",
        investor_question: "Does the battery reduce peak exposure without harming site operations?",
        proof_source: checkpointEvidence(readiness, "physical-operation"),
        report_section: "Site value",
      },
      {
        asset_specific_message: "Separate site tariff/load assumptions from exchange-trading assumptions.",
        investor_question: "Which value is tariff-driven and which value is tradable?",
        proof_source: diligenceRows[1]?.mock_evidence ?? "-",
        report_section: "Savings split",
      },
      {
        asset_specific_message: "Show export permission and connection constraints before external market claims.",
        investor_question: "Can market participation happen without breaking behind-the-meter constraints?",
        proof_source: checkpointEvidence(readiness, "execution-safety"),
        report_section: "Optional market access",
      },
    ];
  }

  return [
    {
      asset_specific_message: "Frame the asset as a grid-scale spread capture case.",
      investor_question: "Can the battery physically cycle into high-value hours?",
      proof_source: checkpointEvidence(readiness, "physical-operation"),
      report_section: "Merchant operation",
    },
    {
      asset_specific_message: "Show revenue after physical movement, losses, fees, and eligibility gates.",
      investor_question: "Is the revenue backed by tradable products and validated dispatch?",
      proof_source: checkpointEvidence(readiness, "revenue-case"),
      report_section: "Revenue stack",
    },
    {
      asset_specific_message: "Keep live execution clearly gated until adapters and approvals are production-ready.",
      investor_question: "What is mock/paper-ready now, and what is still needed for production?",
      proof_source: checkpointEvidence(readiness, "execution-safety"),
      report_section: "Execution controls",
    },
  ];
}

function buildDownsideAppendixRows({
  readiness,
  scenarios,
  stress,
}: {
  readiness?: InvestorReadinessResponse;
  scenarios?: ScenarioReportResponse;
  stress?: ScenarioReportResponse;
}): TableRow[] {
  const stressRows = stress?.results ?? [];
  const prioritizedCases = [
    "Base case",
    "Low-price downside",
    "Dispatch underperformance",
    "Battery degradation / availability reduction",
  ];
  const selectedRows = [
    ...prioritizedCases
      .map((scenarioName) =>
        stressRows.find((row) => row.scenario_name === scenarioName),
      )
      .filter(Boolean),
    ...stressRows.filter((row) => row.stress_category === "asset_specific_downside"),
  ] as TableRow[];
  const uniqueRows = selectedRows.filter(
    (row, index, rows) =>
      rows.findIndex((candidate) => candidate.scenario_name === row.scenario_name) === index,
  );

  if (!uniqueRows.length) {
    return [
      {
        downside_case: "Scenario evidence missing",
        readiness_impact: `${readiness?.summary?.readiness_status ?? "not_loaded"} / ${readiness?.summary?.open_gap_count ?? "-"} open gap(s)`,
        report_conclusion: "Needs review before investor distribution.",
        result: scenarios?.status === "ok" ? "Sizing scenarios loaded; stress cases missing" : "No scenario or stress appendix loaded",
      },
    ];
  }

  return uniqueRows.map((row) => {
    const pnl = Number(row.total_pnl_eur ?? 0);
    const conclusion = getDownsideConclusion(row);

    return {
      downside_case: row.investor_case ?? row.scenario_name,
      readiness_impact:
        pnl < 0
          ? "Reduces revenue confidence; keep as an open diligence review item."
          : "Supports mock-data investor readiness for this asset.",
      report_conclusion: conclusion,
      result: `${formatReportMoney(row.total_pnl_eur)} / ${row.opportunity_level ?? "-"} / ${row.signal ?? "-"}`,
    };
  });
}

function getDownsideConclusion(row: TableRow) {
  const pnl = Number(row.total_pnl_eur ?? 0);
  const category = String(row.stress_category ?? "");

  if (pnl < 0) {
    return "Breaks downside economics in mock data; investor report should flag this before promotion.";
  }

  if (category.includes("downside") || category.includes("degradation")) {
    return "Needs review, but does not break the current mock investment case.";
  }

  if (category === "baseline") {
    return "Works as the base case reference for the appendix.";
  }

  return "Works in mock data and can stay as supporting sensitivity evidence.";
}

function getDownsideAppendixTone(rows: TableRow[]): ReportProofKpi["accent"] {
  if (
    rows.some((row) =>
      String(row.report_conclusion ?? "").toLowerCase().includes("breaks"),
    )
  ) {
    return "red";
  }

  if (
    rows.some((row) =>
      String(row.report_conclusion ?? "").toLowerCase().includes("review"),
    )
  ) {
    return "amber";
  }

  return "emerald";
}

function formatReportMoney(value: unknown) {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    currency: "EUR",
    maximumFractionDigits: 0,
    style: "currency",
  }).format(amount);
}

function buildReportDecision({
  asset,
  completeness,
  personaId,
  reportName,
  reportStatus,
}: {
  asset?: Asset;
  completeness?: DataCompletenessResponse;
  personaId: PersonaId;
  reportName: string;
  reportStatus?: string;
}) {
  const framing = getReportPersonaFraming(personaId);
  const blockers = [
    reportStatus !== "ok" ? "No current monthly report is available." : null,
    Number(completeness?.missing_count ?? 0) > 0
      ? `${completeness?.missing_count} evidence gap(s) remain before client delivery.`
      : null,
  ].filter(Boolean) as string[];

  return {
    blockers,
    pageDescription: framing.pageDescription,
    pageEyebrow: framing.pageEyebrow,
    pageTitle: framing.pageTitle,
    decision: blockers.length
      ? framing.draftDecision
      : framing.readyDecision,
    evidence: [
      `Report ${reportName}`,
      `Evidence score ${completeness?.score ?? "-"} / 100`,
      `${completeness?.complete_count ?? 0} complete evidence check(s)`,
      `${completeness?.missing_count ?? 0} open evidence gap(s)`,
      framing.evidenceUse,
      ...buildAssetDataProfileEvidence(asset),
    ],
    nextAction:
      blockers[0] ??
      framing.readyNextAction,
    title: framing.decisionTitle,
    tone: blockers.length ? "amber" as const : "emerald" as const,
  };
}

type ReportProofKpi = {
  accent: "amber" | "blue" | "emerald" | "red" | "slate";
  helper: string;
  label: string;
  value: React.ReactNode;
};

function normalizeReportProofKpis(rows?: TableRow[]): ReportProofKpi[] {
  return (rows ?? []).map((row) => ({
    accent: normalizeAccent(row.accent),
    helper: String(row.helper ?? ""),
    label: String(row.label ?? "Evidence"),
    value: normalizeKpiValue(row.value),
  }));
}

function normalizeKpiValue(value: TableRow[string]): React.ReactNode {
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  if (value === null || value === undefined) {
    return "-";
  }

  return JSON.stringify(value);
}

function normalizeAccent(value: unknown): ReportProofKpi["accent"] {
  if (
    value === "amber" ||
    value === "blue" ||
    value === "emerald" ||
    value === "red" ||
    value === "slate"
  ) {
    return value;
  }

  return "slate";
}

function scoreAccent(score: unknown): ReportProofKpi["accent"] {
  const value = Number(score);

  if (!Number.isFinite(value)) {
    return "slate";
  }

  if (value >= 80) {
    return "emerald";
  }

  if (value >= 50) {
    return "amber";
  }

  return "red";
}

function readinessTone(status: unknown): ReportProofKpi["accent"] {
  if (status === "ready") {
    return "emerald";
  }

  if (status === "blocked") {
    return "red";
  }

  return "amber";
}

function formatReadinessStatus(status: unknown) {
  if (status === "ready") {
    return "Ready";
  }

  if (status === "blocked") {
    return "Blocked";
  }

  if (status === "review") {
    return "Needs review";
  }

  return "Not loaded";
}

function checkpointStatus(readiness: InvestorReadinessResponse | undefined, checkpointId: string) {
  return (
    readiness?.checkpoints?.find((checkpoint) => checkpoint.id === checkpointId)
      ?.status ?? "not_loaded"
  );
}

function checkpointEvidence(readiness: InvestorReadinessResponse | undefined, checkpointId: string) {
  return (
    readiness?.checkpoints?.find((checkpoint) => checkpoint.id === checkpointId)
      ?.evidence ?? "-"
  );
}

function getAssetReportLabel(asset?: Asset) {
  const assetType = String(asset?.asset_type ?? "");

  if (assetType.includes("solar")) {
    return "Solar co-located battery";
  }

  if (assetType.includes("industrial") || assetType.includes("behind")) {
    return "Industrial behind-the-meter battery";
  }

  return "Grid-scale battery";
}

function buildFriendlyReportTitle(reportName: string) {
  if (!reportName || reportName === "-") {
    return "-";
  }

  const assetId = reportName.match(/^monthly_report_(.+)_\d{4}-\d{2}\.html$/)?.[1];
  const assetLabel = assetId
    ? assetId.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
    : "Portfolio";
  const period = getReportPeriod(reportName);

  return period
    ? `${assetLabel} investor evidence report - ${period}`
    : `${assetLabel} investor evidence report`;
}

function getReportPeriod(reportName: string) {
  return reportName.match(/_(\d{4}-\d{2})\.html$/)?.[1];
}

function getReportPersonaFraming(personaId: PersonaId) {
  const defaultFraming = {
    decisionTitle: "Is this report defensible for a client?",
    draftDecision: "Keep this report in draft until evidence gaps are cleared.",
    evidenceUse: "The report packages forecast, dispatch, revenue, regulatory, and execution evidence.",
    pageDescription:
      "Package forecast, dispatch, revenue, regulatory, and execution evidence into a defensible client report. This view makes the delivery state, open evidence gaps, archive, and backend source routes explicit.",
    pageEyebrow: "Management reporting",
    pageTitle: "Client reporting",
    readyDecision: "Report evidence is ready for client-facing delivery.",
    readyNextAction: "Deliver the report and use the archive as the asset audit trail.",
  };

  const personaFraming: Partial<Record<PersonaId, typeof defaultFraming>> = {
    asset_owner: {
      decisionTitle: "Can the owner trust this report?",
      draftDecision: "Keep this report in owner-review draft until value and evidence gaps are clear.",
      evidenceUse: "Owner value is supported by revenue, settlement, blockers, and audit evidence.",
      pageDescription:
        "Translate asset revenue, readiness, settlement proof, and open blockers into an owner-facing report that explains value creation and remaining risk.",
      pageEyebrow: "Owner reporting",
      pageTitle: "Owner value report",
      readyDecision: "Owner value evidence is ready to share.",
      readyNextAction: "Share the report with the owner and use the archive as proof of the current value case.",
    },
    investor_lender: {
      decisionTitle: "Is this report bankable enough for investment review?",
      draftDecision: "Keep this report in diligence draft until bankability evidence gaps are closed.",
      evidenceUse: "Bankability depends on revenue certainty, downside protection, settlement proof, and audit completeness.",
      pageDescription:
        "Package revenue certainty, downside protection, compliance evidence, settlement variance, and audit readiness for investment or lender review.",
      pageEyebrow: "Bankability reporting",
      pageTitle: "Investor evidence report",
      readyDecision: "The report is ready for investment or lender review.",
      readyNextAction: "Use the report as the bankability packet and keep settlement/audit evidence attached.",
    },
    project_developer: {
      decisionTitle: "Does this report prove development readiness?",
      draftDecision: "Keep this report in development draft until readiness gaps are resolved.",
      evidenceUse: "Development readiness depends on asset setup, forecast evidence, scenario economics, market eligibility, and regulation.",
      pageDescription:
        "Summarize pre-COD revenue, market eligibility, regulatory assumptions, forecast readiness, and financing evidence for development decisions.",
      pageEyebrow: "Development reporting",
      pageTitle: "Development readiness report",
      readyDecision: "Development readiness evidence is ready for stakeholder review.",
      readyNextAction: "Use the report to support development, financing, and market-readiness discussions.",
    },
    executive: {
      decisionTitle: "Is this report board-ready?",
      draftDecision: "Keep this report in executive draft until the major evidence gap is resolved.",
      evidenceUse: "Executive reporting should highlight portfolio value, maturity, risk, and the top blocker.",
      pageDescription:
        "Condense asset value, automation maturity, risk blockers, settlement evidence, and next actions into a board-ready management view.",
      pageEyebrow: "Executive reporting",
      pageTitle: "Board-ready report",
      readyDecision: "The report is ready for executive or board review.",
      readyNextAction: "Use the report for executive review and track the archive as the management evidence trail.",
    },
    client_success: {
      decisionTitle: "Can I send this report and explain the open gaps?",
      draftDecision: "Keep this report in client-success draft and explain the open evidence gap before sending.",
      evidenceUse: "Client success needs a clear narrative, open gaps, and next actions for the client conversation.",
      pageDescription:
        "Prepare a client-facing narrative with delivery status, evidence gaps, settlement/audit proof, and clear next actions.",
      pageEyebrow: "Client success reporting",
      pageTitle: "Client delivery report",
      readyDecision: "The report is ready to send to the client.",
      readyNextAction: "Send the report and use the delivery gaps section to guide the client conversation.",
    },
    risk_compliance: {
      decisionTitle: "Does this report satisfy governance review?",
      draftDecision: "Keep this report in governance draft until evidence and control gaps are resolved.",
      evidenceUse: "Governance review depends on traceable evidence, settlement proof, audit packet completeness, and assumptions.",
      pageDescription:
        "Review whether the client report has enough evidence, assumptions, settlement proof, and audit linkage for governance sign-off.",
      pageEyebrow: "Governance reporting",
      pageTitle: "Governance report review",
      readyDecision: "The report has enough evidence for governance review.",
      readyNextAction: "Use the report with Audit Evidence and Settlement Evidence for sign-off.",
    },
    revenue_analyst: {
      decisionTitle: "Does this report explain commercial value correctly?",
      draftDecision: "Keep this report in commercial draft until revenue assumptions and evidence gaps are clear.",
      evidenceUse: "Commercial reporting should connect revenue stack, hedge assumptions, settlement variance, and blocked value.",
      pageDescription:
        "Validate that the report correctly summarizes revenue stack, hedging assumptions, settlement feedback, and open commercial blockers.",
      pageEyebrow: "Commercial reporting",
      pageTitle: "Revenue evidence report",
      readyDecision: "The report is ready as a commercial value summary.",
      readyNextAction: "Use the report to explain revenue assumptions and update value cases from settlement feedback.",
    },
  };

  return personaFraming[personaId] ?? defaultFraming;
}

function buildDeliveryGapRows({
  completeness,
  reportStatus,
}: {
  completeness?: DataCompletenessResponse;
  reportStatus?: string;
}) {
  const rows = [];

  if (reportStatus !== "ok") {
    rows.push({
      gap: "Monthly report artifact",
      status: "missing",
      next_action: "Generate the monthly report before client delivery.",
    });
  }

  if (Number(completeness?.missing_count ?? 0) > 0) {
    rows.push({
      gap: "Evidence completeness",
      status: `${completeness?.missing_count} open gap(s)`,
      next_action:
        completeness?.next_actions?.[0] ??
        "Close missing forecast, dispatch, revenue, or execution evidence.",
    });
  }

  rows.push({
    gap: "PDF delivery export",
    status: "not connected",
    next_action:
      "HTML is available now; add a backend PDF export route before formal client delivery.",
  });

  return rows;
}

function buildBackendConnectionRows({
  archiveCount,
  completeness,
  reportStatus,
  selectedAssetId,
}: {
  archiveCount?: number;
  completeness?: DataCompletenessResponse;
  reportStatus?: string;
  selectedAssetId: string;
}) {
  return [
    {
      capability: "Latest report metadata",
      backend_route: `/reports/monthly/latest?asset_id=${selectedAssetId}`,
      status: reportStatus ?? "not_loaded",
      business_value: "Shows the current client-facing report artifact.",
    },
    {
      capability: "Generate selected-asset report",
      backend_route: `/assets/${selectedAssetId}/reports/monthly/generate`,
      status: "connected",
      business_value: "Builds a client report from the selected asset evidence stack.",
    },
    {
      capability: "HTML report viewer",
      backend_route: `/reports/monthly/latest/view?asset_id=${selectedAssetId}`,
      status: reportStatus === "ok" ? "available" : "not_available",
      business_value: "Lets a user inspect the generated report directly.",
    },
    {
      capability: "Report archive",
      backend_route: `/reports/monthly/list?asset_id=${selectedAssetId}`,
      status: `${archiveCount ?? 0} archived`,
      business_value: "Keeps a lightweight client reporting audit trail.",
    },
    {
      capability: "Evidence readiness",
      backend_route: `/assets/${selectedAssetId}/data-completeness`,
      status: completeness?.readiness ?? completeness?.status ?? "not_loaded",
      business_value: "Prevents reports from being sent without proof.",
    },
  ];
}
