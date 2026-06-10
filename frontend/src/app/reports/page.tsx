"use client";

import { ExternalLink } from "lucide-react";
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
import { usePersona } from "@/components/persona-provider";
import { useApiBaseUrl } from "@/hooks/use-api-base-url";
import { apiGet } from "@/lib/api";
import type {
  DataCompletenessResponse,
  MonthlyReportListResponse,
  MonthlyReportResponse,
} from "@/types/api";
import type { PersonaId } from "@/lib/personas";

export default function ReportsPage() {
  const apiBaseUrl = useApiBaseUrl();
  const { selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();

  const latest = useQuery({
    queryFn: () =>
      apiGet<MonthlyReportResponse>(
        `/reports/monthly/latest?asset_id=${selectedAssetId}`,
      ),
    queryKey: ["monthly-report-latest", selectedAssetId],
  });

  const archive = useQuery({
    queryFn: () =>
      apiGet<MonthlyReportListResponse>(
        `/reports/monthly/list?asset_id=${selectedAssetId}`,
      ),
    queryKey: ["monthly-report-list", selectedAssetId],
  });

  const completeness = useQuery({
    queryFn: () =>
      apiGet<DataCompletenessResponse>(
        `/assets/${selectedAssetId}/data-completeness`,
      ),
    queryKey: ["reports-data-completeness", selectedAssetId],
  });

  const reportName = String(latest.data?.report_name ?? "-");
  const viewerRoute =
    latest.data?.viewer_route ??
    `/reports/monthly/latest/view?asset_id=${selectedAssetId}`;
  const reportUrl = `${apiBaseUrl}${viewerRoute}`;
  const refetchReports = () =>
    Promise.all([
      latest.refetch(),
      archive.refetch(),
      completeness.refetch(),
    ]);
  const reportDecision = buildReportDecision({
    completeness: completeness.data,
    personaId,
    reportStatus: latest.data?.status,
    reportName,
  });
  const deliveryGapRows = buildDeliveryGapRows({
    completeness: completeness.data,
    reportStatus: latest.data?.status,
  });
  const backendConnectionRows = buildBackendConnectionRows({
    archiveCount: archive.data?.report_count,
    completeness: completeness.data,
    reportStatus: latest.data?.status,
    selectedAssetId,
  });
  const deliveryState = reportDecision.blockers.length
    ? "Draft"
    : "Client ready";

  return (
    <>
      <PageHeading
        description={reportDecision.pageDescription}
        eyebrow={reportDecision.pageEyebrow}
        title={reportDecision.pageTitle}
      />

      <DecisionBrief
        action={
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/reports/monthly/generate`}
            label="Generate client report"
            refetch={refetchReports}
            variant="primary"
          />
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

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Latest report" value={reportName} />
        <KpiCard
          accent={deliveryState === "Client ready" ? "emerald" : "amber"}
          label="Client delivery state"
          value={deliveryState}
          helper={latest.data?.status === "ok" ? "HTML report available" : "Report not generated"}
        />
        <KpiCard
          accent={
            Number(completeness.data?.missing_count ?? 0) > 0
              ? "amber"
              : "emerald"
          }
          label="Evidence score"
          value={`${completeness.data?.score ?? "-"} / 100`}
          helper={`${completeness.data?.complete_count ?? 0} of ${completeness.data?.check_count ?? 0} checks complete`}
        />
        <KpiCard
          accent="blue"
          label="Archive count"
          value={archive.data?.report_count ?? 0}
          helper="Persisted report files"
        />
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <SectionCard
          action={
            <div className="flex flex-wrap items-center gap-2">
              {latest.data?.status === "ok" ? (
                <StatusPill tone="emerald">Available</StatusPill>
              ) : (
                <StatusPill tone="amber">Not generated</StatusPill>
              )}
              <ActionButton
                endpoint={`/assets/${selectedAssetId}/reports/monthly/generate`}
                label="Generate"
                refetch={refetchReports}
                variant="secondary"
              />
            </div>
          }
          title="Latest monthly report"
        >
          {latest.data?.status === "ok" ? (
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
                rows={[
                  { field: "Report name", value: reportName },
                  { field: "Report file", value: latest.data.report_file ?? "-" },
                  { field: "Delivery status", value: "Draft HTML" },
                  {
                    field: "Viewer route",
                    value: viewerRoute,
                  },
                  {
                    field: "Asset scope",
                    value: latest.data.asset_id ?? selectedAssetId,
                  },
                ]}
              />
            </div>
          ) : (
            <div className="text-sm text-slate-400">
              {latest.data?.message ?? "No report is available yet."}
            </div>
          )}
        </SectionCard>

        <DataCompletenessPanel
          data={completeness.data}
          title="Report evidence readiness"
        />
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
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

        <SectionCard
          action={<StatusPill tone="blue">Backend linked</StatusPill>}
          title="Backend connection map"
        >
          <DataTable
            columns={["capability", "backend_route", "status", "business_value"]}
            rows={backendConnectionRows}
          />
        </SectionCard>
      </div>

      <SectionCard title="Report archive">
        <DataTable
          columns={["report_name", "report_file"]}
          rows={archive.data?.reports ?? []}
        />
      </SectionCard>
    </>
  );
}

function buildReportDecision({
  completeness,
  personaId,
  reportName,
  reportStatus,
}: {
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
    ],
    nextAction:
      blockers[0] ??
      framing.readyNextAction,
    title: framing.decisionTitle,
    tone: blockers.length ? "amber" as const : "emerald" as const,
  };
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
