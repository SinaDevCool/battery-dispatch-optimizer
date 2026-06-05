"use client";

import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DispatchChart } from "@/components/charts/dispatch-chart";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { LatestSignalResponse } from "@/types/api";

export default function DispatchPage() {
  const { selectedAssetId } = useAssetContext();

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["dispatch-signal", selectedAssetId],
  });

  const summary = signal.data?.data?.summary ?? {};
  const dispatch = signal.data?.data?.dispatch ?? [];
  const chargeRows = dispatch.filter((row) => row.action === "charge");
  const dischargeRows = dispatch.filter((row) => row.action === "discharge");
  const activeRows = dispatch.filter((row) => row.action !== "idle");
  const bidWindowRows = (activeRows.length ? activeRows : dispatch)
    .slice(0, 24)
    .map((row) => ({
      ...row,
      automation_role:
        row.action === "charge"
          ? "buy / charge window"
          : row.action === "discharge"
            ? "sell / discharge window"
            : "hold evidence",
    }));
  const dispatchBias = classifyDispatchBias(
    Number(summary.charged_mwh ?? 0),
    Number(summary.discharged_mwh ?? 0),
  );

  return (
    <>
      <PageHeading
        description="Translate the latest optimization signal into the physical charge, discharge, hold, and state-of-charge schedule that bid generation can trust."
        eyebrow="Optimization"
        title="Trading Schedule"
      />

      {signal.error ? <ErrorState message="Could not load latest dispatch signal." /> : null}

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/signal/run-latest`}
          label="Generate latest signal"
          refetch={() => signal.refetch()}
          variant="primary"
        />
      </div>

      <DecisionBrief
        blockers={
          dispatch.length
            ? []
            : ["No dispatch schedule is available for bid conversion."]
        }
        className="mb-6"
        decision={
          <>
            {String(summary.signal ?? "No signal")}
            <span className="text-slate-500"> / </span>
            {dispatchBias}
          </>
        }
        evidence={[
          `${activeRows.length} active interval(s) available for bid conversion.`,
          `${formatNumber(summary.charged_mwh, 2)} MWh charged and ${formatNumber(summary.discharged_mwh, 2)} MWh discharged.`,
          `${formatCurrency(summary.total_pnl_eur)} expected dispatch economics.`,
        ]}
        eyebrow="Schedule intent"
        nextAction="Use this schedule as physical evidence for proposal generation, then validate against forecast confidence and risk gates before automated submission."
        title="Dispatch-to-bid decision"
        tone={summary.signal === "ACTION" ? "emerald" : "amber"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard label="Signal" value={summary.signal ?? "-"} />
        <KpiCard accent="emerald" label="Total PnL" value={formatCurrency(summary.total_pnl_eur)} />
        <KpiCard label="Active windows" value={`${activeRows.length}/${dispatch.length}`} />
        <KpiCard label="Bid direction" value={dispatchBias} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <SectionCard title="Dispatch analytics">
          {dispatch.length ? <DispatchChart rows={dispatch} /> : <ErrorState message="No dispatch rows found." />}
        </SectionCard>

        <SectionCard title="Bid conversion summary">
          <DataTable
            columns={["field", "value"]}
            rows={[
              { field: "Charge windows", value: chargeRows.length },
              { field: "Discharge windows", value: dischargeRows.length },
              { field: "Idle intervals", value: dispatch.length - activeRows.length },
              { field: "First charge", value: chargeRows[0]?.timestamp ?? "-" },
              { field: "First discharge", value: dischargeRows[0]?.timestamp ?? "-" },
            ]}
          />
        </SectionCard>
      </div>

      <div className="mt-5">
        <SectionCard title="Automation schedule windows">
          <DataTable
            columns={[
              "timestamp",
              "price",
              "action",
              "automation_role",
              "soc_mwh",
              "pnl_eur",
              "total_pnl_eur",
            ]}
            rows={bidWindowRows}
          />
        </SectionCard>
      </div>
    </>
  );
}

function classifyDispatchBias(chargedMwh: number, dischargedMwh: number) {
  if (chargedMwh > dischargedMwh * 1.1) {
    return "charge bias";
  }

  if (dischargedMwh > chargedMwh * 1.1) {
    return "discharge bias";
  }

  return "balanced schedule";
}
