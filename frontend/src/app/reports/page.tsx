"use client";

import { ExternalLink } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataCompletenessPanel } from "@/components/data-completeness-panel";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { useApiBaseUrl } from "@/hooks/use-api-base-url";
import { apiGet } from "@/lib/api";
import type {
  DataCompletenessResponse,
  MonthlyReportListResponse,
  MonthlyReportResponse,
} from "@/types/api";

export default function ReportsPage() {
  const apiBaseUrl = useApiBaseUrl();
  const { selectedAssetId } = useAssetContext();

  const latest = useQuery({
    queryFn: () => apiGet<MonthlyReportResponse>("/reports/monthly/latest"),
    queryKey: ["monthly-report-latest"],
  });

  const archive = useQuery({
    queryFn: () => apiGet<MonthlyReportListResponse>("/reports/monthly/list"),
    queryKey: ["monthly-report-list"],
  });

  const completeness = useQuery({
    queryFn: () =>
      apiGet<DataCompletenessResponse>(
        `/assets/${selectedAssetId}/data-completeness`,
      ),
    queryKey: ["reports-data-completeness", selectedAssetId],
  });

  const reportName = String(latest.data?.report_name ?? "-");
  const reportUrl = `${apiBaseUrl}/reports/monthly/latest/view`;
  const reportDecision = buildReportDecision({
    completeness: completeness.data,
    reportStatus: latest.data?.status,
    reportName,
  });

  return (
    <>
      <PageHeading
        description="Management reporting should be backed by forecast, dispatch, revenue, regulatory, and execution evidence. This first web view links the current HTML report and shows whether the selected asset has enough evidence for a client-facing report."
        eyebrow="Management reporting"
        title="Reports"
      />

      <DecisionBrief
        blockers={reportDecision.blockers}
        className="mb-6"
        decision={reportDecision.decision}
        evidence={reportDecision.evidence}
        eyebrow="Client reporting decision"
        nextAction={reportDecision.nextAction}
        title="Is this report defensible for a client?"
        tone={reportDecision.tone}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Latest report" value={reportName} />
        <KpiCard label="Report status" value={latest.data?.status ?? "-"} />
        <KpiCard
          accent="blue"
          label="Archive count"
          value={archive.data?.report_count ?? 0}
          helper="Persisted report files"
        />
        <KpiCard
          accent={latest.data?.status === "ok" ? "emerald" : "amber"}
          label="Format"
          value="HTML"
          helper="PDF export should be added for client delivery"
        />
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <SectionCard
          action={
            latest.data?.status === "ok" ? (
              <StatusPill tone="emerald">Available</StatusPill>
            ) : (
              <StatusPill tone="amber">Not generated</StatusPill>
            )
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
  reportName,
  reportStatus,
}: {
  completeness?: DataCompletenessResponse;
  reportName: string;
  reportStatus?: string;
}) {
  const blockers = [
    reportStatus !== "ok" ? "No current monthly report is available." : null,
    Number(completeness?.missing_count ?? 0) > 0
      ? `${completeness?.missing_count} evidence gap(s) remain before client delivery.`
      : null,
  ].filter(Boolean) as string[];

  return {
    blockers,
    decision: blockers.length
      ? "Keep this report in draft until evidence gaps are cleared."
      : "Report evidence is ready for client-facing delivery.",
    evidence: [
      `Report ${reportName}`,
      `Evidence score ${completeness?.score ?? "-"} / 100`,
      `${completeness?.complete_count ?? 0} complete evidence check(s)`,
      `${completeness?.missing_count ?? 0} open evidence gap(s)`,
    ],
    nextAction:
      blockers[0] ??
      "Deliver the report and use the archive as the asset audit trail.",
    tone: blockers.length ? "amber" as const : "emerald" as const,
  };
}
