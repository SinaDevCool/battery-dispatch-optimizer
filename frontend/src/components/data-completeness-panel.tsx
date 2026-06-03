import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type { DataCompletenessResponse, TableRow } from "@/types/api";

export function DataCompletenessPanel({
  data,
  title = "Data completeness",
}: {
  data?: DataCompletenessResponse;
  title?: string;
}) {
  const checks = data?.checks ?? [];
  const rows = checks.map((check) => ({
    check: check.label ?? check.check_id ?? "-",
    status: check.status ?? "-",
    record_id: check.record_id ?? "-",
    message: check.message ?? "-",
  }));
  const nextActions = (data?.next_actions ?? [])
    .filter((action) => action && action !== "-")
    .map((action) => ({ next_action: action }));

  return (
    <SectionCard
      action={<ReadinessPill readiness={data?.readiness} />}
      title={title}
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <KpiCard
          accent={scoreAccent(data?.score)}
          label="Evidence score"
          value={`${data?.score ?? 0}/100`}
          helper={`${data?.complete_count ?? 0} of ${data?.check_count ?? 0} checks complete`}
        />
        <KpiCard
          accent="emerald"
          label="Complete evidence"
          value={data?.complete_count ?? 0}
          helper="Backend records available"
        />
        <KpiCard
          accent={(data?.missing_count ?? 0) > 0 ? "amber" : "emerald"}
          label="Open evidence gaps"
          value={data?.missing_count ?? 0}
          helper="Missing business proof points"
        />
      </div>

      <DataTable
        columns={["check", "status", "record_id", "message"]}
        rows={rows}
      />

      {nextActions.length ? (
        <div className="mt-4 rounded-lg border border-amber-400/25 bg-amber-400/5 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-amber-100">
            <AlertTriangle className="h-4 w-4" />
            Next actions to make the asset bankable
          </div>
          <DataTable columns={["next_action"]} rows={nextActions as TableRow[]} />
        </div>
      ) : (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-emerald-400/25 bg-emerald-400/5 p-4 text-sm text-emerald-100">
          <CheckCircle2 className="h-4 w-4" />
          All core decision evidence exists for this asset.
        </div>
      )}
    </SectionCard>
  );
}

function ReadinessPill({ readiness }: { readiness?: string }) {
  if (readiness === "decision_ready") {
    return <StatusPill tone="emerald">Decision ready</StatusPill>;
  }

  if (readiness === "usable_with_gaps") {
    return <StatusPill tone="amber">Usable with gaps</StatusPill>;
  }

  return <StatusPill tone="red">Setup required</StatusPill>;
}

function scoreAccent(score?: number) {
  if ((score ?? 0) >= 85) {
    return "emerald";
  }

  if ((score ?? 0) >= 55) {
    return "amber";
  }

  return "red";
}
