"use client";

import { ExternalLink } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { API_BASE_URL, apiGet } from "@/lib/api";
import type { MonthlyReportResponse } from "@/types/api";

export default function ReportsPage() {
  const latest = useQuery({
    queryFn: () => apiGet<MonthlyReportResponse>("/reports/monthly/latest"),
    queryKey: ["monthly-report-latest"],
  });

  const reportName = String(latest.data?.report_name ?? "-");
  const reportUrl = `${API_BASE_URL}/reports/monthly/latest/view`;

  return (
    <>
      <PageHeading
        description="Client-facing reporting should eventually be generated as branded PDFs and secure web reports. This page links to the current backend HTML report."
        eyebrow="Management reporting"
        title="Reports"
      />

      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <KpiCard label="Latest report" value={reportName} />
        <KpiCard label="Report status" value={latest.data?.status ?? "-"} />
        <KpiCard accent="blue" label="Format" value="HTML" />
      </div>

      <SectionCard title="Latest monthly report">
        {latest.data?.status === "ok" ? (
          <a
            className="inline-flex items-center gap-2 rounded-md border border-sky-400/30 bg-sky-400/10 px-4 py-2 text-sm font-semibold text-sky-100 hover:bg-sky-400/20"
            href={reportUrl}
            rel="noreferrer"
            target="_blank"
          >
            Open report
            <ExternalLink className="h-4 w-4" />
          </a>
        ) : (
          <div className="text-sm text-slate-400">
            {latest.data?.message ?? "No report is available yet."}
          </div>
        )}
      </SectionCard>
    </>
  );
}
