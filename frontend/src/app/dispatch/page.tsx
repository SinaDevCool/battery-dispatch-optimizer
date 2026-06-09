"use client";

import Link from "next/link";
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
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  ExecutionProposalResponse,
  ExecutionReadinessResponse,
  LatestSignalResponse,
  MultiMarketAllocationResponse,
} from "@/types/api";

export default function DispatchPage() {
  const { selectedAssetId } = useAssetContext();

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["dispatch-signal", selectedAssetId],
  });

  const proposal = useQuery({
    queryFn: () =>
      apiGet<ExecutionProposalResponse>(
        `/assets/${selectedAssetId}/execution/proposal/latest`,
      ),
    queryKey: ["dispatch-proposal", selectedAssetId],
  });

  const allocation = useQuery({
    queryFn: () =>
      apiGet<MultiMarketAllocationResponse>(
        `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      ),
    queryKey: ["dispatch-market-allocation", selectedAssetId],
  });

  const readiness = useQuery({
    queryFn: () =>
      apiGet<ExecutionReadinessResponse>(
        `/assets/${selectedAssetId}/execution/readiness`,
      ),
    queryKey: ["dispatch-execution-readiness", selectedAssetId],
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
  const scheduleReady = dispatch.length > 0 && activeRows.length > 0;
  const orderPackageStatus = scheduleReady ? "ready for proposal" : "not ready";
  const backendConnectionRows = buildDispatchBackendConnectionRows({
    activeIntervals: activeRows.length,
    allocationStatus:
      allocation.data?.allocation_status ??
      allocation.data?.summary?.readiness_status,
    dispatchRows: dispatch.length,
    proposalStatus:
      proposal.data?.proposal?.status ??
      proposal.data?.status ??
      "not built",
    readinessStatus:
      readiness.data?.readiness_status ??
      readiness.data?.automation_status ??
      "not evaluated",
    selectedAssetId,
    signalStatus: signal.data?.status,
  });

  const refetchDispatchEvidence = () =>
    Promise.all([
      signal.refetch(),
      proposal.refetch(),
      allocation.refetch(),
      readiness.refetch(),
    ]);

  return (
    <>
      <PageHeading
        description="Convert the optimizer signal into charge, discharge, SOC, and PnL intervals that can become a bid proposal after forecast, market-route, and risk gates pass."
        eyebrow="Optimization"
        title="Dispatch-to-bid schedule"
      />

      {signal.error ? <ErrorState message="Could not load latest dispatch signal." /> : null}

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/signal/run-latest`}
          label="Generate latest signal"
          refetch={refetchDispatchEvidence}
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
        <KpiCard
          accent={scheduleReady ? "emerald" : "amber"}
          label="Order package"
          value={orderPackageStatus}
        />
      </div>

      <SectionCard
        action={
          <StatusPill tone={scheduleReady ? "emerald" : "amber"}>
            {dispatchBias}
          </StatusPill>
        }
        className="mb-5"
        title="Dispatch-to-order bridge"
      >
        <div className="grid gap-5 xl:grid-cols-[minmax(0,0.85fr)_minmax(420px,1.15fr)]">
          <DataTable
            columns={["decision_input", "value"]}
            rows={[
              {
                decision_input: "Order package status",
                value: orderPackageStatus,
              },
              {
                decision_input: "Physical action windows",
                value: `${chargeRows.length} charge / ${dischargeRows.length} discharge`,
              },
              {
                decision_input: "Next automation step",
                value: scheduleReady
                  ? "Build bid proposal and validate market route plus risk gates."
                  : "Generate a dispatch signal before creating any order package.",
              },
              {
                decision_input: "Why this page matters",
                value: "It turns optimizer economics into executable physical intervals.",
              },
            ]}
          />
          <DataTable
            columns={["capability", "backend_route", "status", "business_value"]}
            rows={backendConnectionRows}
          />
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            className="rounded-md border border-sky-400/35 bg-sky-400/10 px-3 py-2 text-sm font-semibold text-sky-100 transition hover:border-sky-300 hover:bg-sky-400/20"
            href="/execution/proposals"
          >
            Open bid proposals
          </Link>
          <Link
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white"
            href="/market-signals"
          >
            Check signal readiness
          </Link>
          <Link
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white"
            href="/execution/risk-approval"
          >
            Review risk gates
          </Link>
        </div>
      </SectionCard>

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

function buildDispatchBackendConnectionRows({
  activeIntervals,
  allocationStatus,
  dispatchRows,
  proposalStatus,
  readinessStatus,
  selectedAssetId,
  signalStatus,
}: {
  activeIntervals: number;
  allocationStatus?: string;
  dispatchRows: number;
  proposalStatus?: string;
  readinessStatus?: string;
  selectedAssetId: string;
  signalStatus?: string;
}) {
  return [
    {
      backend_route: `/assets/${selectedAssetId}/signal/latest`,
      business_value: "Loads the persisted optimization signal and physical dispatch intervals.",
      capability: "Latest dispatch signal",
      status: signalStatus ?? "not loaded",
    },
    {
      backend_route: `/assets/${selectedAssetId}/signal/run-latest`,
      business_value: "Creates a fresh dispatch schedule from forecast data before bid generation.",
      capability: "Signal generation",
      status: "available",
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/proposal/latest`,
      business_value: "Converts active dispatch intervals into draft market orders.",
      capability: "Bid proposal handoff",
      status: `${proposalStatus ?? "not built"} / ${activeIntervals} active interval(s)`,
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/multi-market/allocation`,
      business_value: "Selects the market route before the dispatch becomes an order package.",
      capability: "Market allocation dependency",
      status: allocationStatus ?? (dispatchRows ? "dispatch available" : "waiting for dispatch"),
    },
    {
      backend_route: `/assets/${selectedAssetId}/execution/readiness`,
      business_value: "Blocks live or supervised submission until guardrails and approval pass.",
      capability: "Risk gate dependency",
      status: readinessStatus ?? "required before automation",
    },
  ];
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
