"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ActionButton } from "@/components/action-button";
import {
  AssetDataProfileSection,
  buildAssetDataProfileEvidence,
} from "@/components/asset-data-profile-section";
import { useAssetContext } from "@/components/asset-provider";
import { DispatchChart } from "@/components/charts/dispatch-chart";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet, apiPost } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type {
  AssetPhysics,
  AssetSignalRunResponse,
  ExecutionProposalResponse,
  ExecutionReadinessResponse,
  LatestSignalResponse,
  MultiMarketAllocationResponse,
  OptimizersResponse,
  SignalSummary,
  TableRow,
} from "@/types/api";

const dispatchTabs = [
  {
    id: "schedule",
    label: "Schedule",
    helper: "Chart, active windows, and charge/discharge schedule used for bid conversion.",
  },
  {
    id: "physical-proof",
    label: "Physical Proof",
    helper: "SOC, battery physics, validation checks, and selected asset profile.",
  },
  {
    id: "bid-handoff",
    label: "Bid Handoff",
    helper: "Backend handoff to market allocation, proposal generation, and risk gates.",
  },
] as const;

type DispatchTabId = (typeof dispatchTabs)[number]["id"];

type DispatchPersonaFraming = {
  analyticsTitle: string;
  bridgeTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  eyebrow: string;
  nextActionClear: string;
  nextActionMissing: string;
  runLabel: string;
  scheduleTitle: string;
  summaryTitle: string;
  title: string;
  whyThisPageMatters: string;
};

export default function DispatchPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();
  const [activeTab, setActiveTab] = useState<DispatchTabId>("schedule");
  const [selectedOptimizer, setSelectedOptimizer] = useState("linear_program_v1");
  const [comparisonRows, setComparisonRows] = useState<TableRow[]>([]);
  const [comparisonStatus, setComparisonStatus] = useState<string | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const framing = getDispatchPersonaFraming(personaId);
  const assetDataProfileEvidence = buildAssetDataProfileEvidence(selectedAsset);

  const optimizers = useQuery({
    queryFn: () => apiGet<OptimizersResponse>("/battery/optimizers"),
    queryKey: ["battery-optimizers"],
  });

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
  const assetPhysics = signal.data?.data?.asset_physics;
  const optimization = signal.data?.data?.optimization;
  const validation = signal.data?.data?.validation;
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
  const physicalProofRows = buildPhysicalProofRows({
    assetPhysics,
    selectedAssetType: selectedAsset?.asset_type,
    summary,
    validation,
  });
  const visiblePhysicalProofRows = signal.data?.dispatch_proof?.rows?.length
    ? signal.data.dispatch_proof.rows
    : physicalProofRows;
  const scheduleColumns = buildScheduleColumns(selectedAsset?.asset_type);
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

  const runOptimizerComparison = async () => {
    setIsComparing(true);
    setComparisonStatus(null);

    try {
      const engines = ["rule_based_v1", "linear_program_v1"];
      const results = await Promise.all(
        engines.map((engine) =>
          apiPost<AssetSignalRunResponse>(
            `/assets/${selectedAssetId}/signal/run-latest?optimizer_engine=${encodeURIComponent(engine)}`,
          ),
        ),
      );

      setComparisonRows(
        results.map((result) => {
          const resultSummary = result.data?.summary ?? {};
          const resultOptimization = result.data?.optimization ?? {};
          return {
            active_intervals:
              Number(resultSummary.charge_hours ?? 0) +
              Number(resultSummary.discharge_hours ?? 0),
            charged_mwh: resultSummary.charged_mwh,
            discharged_mwh: resultSummary.discharged_mwh,
            engine: result.optimizer_engine ?? resultOptimization.optimizer_engine,
            method: resultOptimization.method ?? "-",
            objective_value_eur: resultOptimization.objective_value_eur,
            physics_model: result.data?.asset_physics?.physics_model,
            signal: resultSummary.signal,
            total_pnl_eur: resultSummary.total_pnl_eur,
          };
        }),
      );
      setSelectedOptimizer("linear_program_v1");
      setComparisonStatus("Comparison refreshed. Latest dispatch is saved with linear_program_v1.");
      await refetchDispatchEvidence();
    } catch (error) {
      setComparisonStatus(error instanceof Error ? error.message : "Comparison failed.");
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <>
      <PageHeading
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
      />

      {signal.error ? <ErrorState message="Could not load latest dispatch signal." /> : null}

      <div className="mb-6 grid gap-3 lg:grid-cols-[minmax(260px,380px)_auto_auto] lg:items-start">
        <label className="flex flex-col gap-2 rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
            Optimizer engine
          </span>
          <select
            className="h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm font-semibold text-slate-100 outline-none transition focus:border-sky-400"
            onChange={(event) => setSelectedOptimizer(event.target.value)}
            value={selectedOptimizer}
          >
            {(optimizers.data?.available_optimizers?.length
              ? optimizers.data.available_optimizers
              : ["linear_program_v1", "rule_based_v1"]
            ).map((engine) => (
              <option key={engine} value={engine}>
                {formatOptimizerLabel(engine)}
              </option>
            ))}
          </select>
        </label>

        <ActionButton
          endpoint={`/assets/${selectedAssetId}/signal/run-latest?optimizer_engine=${encodeURIComponent(selectedOptimizer)}`}
          label={`${framing.runLabel} (${formatOptimizerLabel(selectedOptimizer)})`}
          refetch={refetchDispatchEvidence}
          variant="primary"
        />

        <div className="flex flex-col gap-2">
          <button
            className="inline-flex h-10 items-center justify-center rounded-md border border-sky-400/30 bg-sky-400/10 px-3 text-xs font-semibold text-sky-100 transition hover:bg-sky-400/20 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isComparing}
            onClick={runOptimizerComparison}
            type="button"
          >
            {isComparing ? "Comparing..." : "Compare engines"}
          </button>
          {comparisonStatus ? (
            <div className="max-w-sm rounded-md border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs leading-5 text-slate-300">
              {comparisonStatus}
            </div>
          ) : null}
        </div>
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
          assetPhysics?.physics_model
            ? `Physics model: ${formatPhysicsLabel(assetPhysics.physics_model)}.`
            : "Physics model pending.",
          optimization?.optimizer_engine
            ? `Optimizer: ${formatOptimizerLabel(String(optimization.optimizer_engine))}.`
            : "Optimizer metadata pending.",
          ...assetDataProfileEvidence,
        ]}
        eyebrow={framing.decisionEyebrow}
        nextAction={dispatch.length ? framing.nextActionClear : framing.nextActionMissing}
        title={framing.decisionTitle}
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

      <div className="mb-5 grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(420px,1.1fr)]">
        <SectionCard title="Optimizer proof">
          <DataTable
            columns={["field", "value"]}
            rows={buildOptimizationProofRows(optimization)}
          />
        </SectionCard>

        <SectionCard title="Engine comparison">
          <DataTable
            columns={[
              "engine",
              "method",
              "signal",
              "total_pnl_eur",
              "objective_value_eur",
              "active_intervals",
              "physics_model",
            ]}
            rows={comparisonRows}
          />
        </SectionCard>
      </div>

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={dispatchTabs}
      />

      {activeTab === "schedule" ? (
        <div className="space-y-5">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
            <SectionCard title={framing.analyticsTitle}>
              {dispatch.length ? <DispatchChart rows={dispatch} /> : <ErrorState message="No dispatch rows found." />}
            </SectionCard>

            <SectionCard title={framing.summaryTitle}>
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

          <SectionCard title={framing.scheduleTitle}>
            <DataTable
              columns={scheduleColumns}
              rows={bidWindowRows}
            />
          </SectionCard>
        </div>
      ) : null}

      {activeTab === "physical-proof" ? (
        <div className="space-y-5">
          <AssetDataProfileSection
            asset={selectedAsset}
            title="Selected dispatch asset profile"
          />

          <SectionCard
            action={
              <StatusPill tone={validationTone(validation?.status)}>
                {validation?.status ? `Validation ${validation.status}` : "Validation pending"}
              </StatusPill>
            }
            title="Physical validation proof"
          >
            <DataTable
              columns={["physical_feature", "value", "investor_meaning"]}
              rows={visiblePhysicalProofRows}
            />
          </SectionCard>
        </div>
      ) : null}

      {activeTab === "bid-handoff" ? (
        <SectionCard
          action={
            <StatusPill tone={scheduleReady ? "emerald" : "amber"}>
              {dispatchBias}
            </StatusPill>
          }
          title={framing.bridgeTitle}
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
                  value: framing.whyThisPageMatters,
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
      ) : null}
    </>
  );
}

function buildOptimizationProofRows(optimization?: TableRow): TableRow[] {
  const proof = (optimization ?? {}) as TableRow;
  const objective = (proof.objective_function ?? {}) as TableRow;
  const constraints = (proof.constraints ?? {}) as TableRow;

  return [
    {
      field: "Engine",
      value: formatOptimizerLabel(String(proof.optimizer_engine ?? "-")),
    },
    {
      field: "Method",
      value: proof.method ?? "-",
    },
    {
      field: "Solver",
      value: proof.solver ?? "-",
    },
    {
      field: "Objective",
      value:
        typeof objective.expression === "string"
          ? objective.expression
          : "Run linear_program_v1 to show the objective function.",
    },
    {
      field: "Objective value",
      value: proof.objective_value_eur,
    },
    {
      field: "Constraint status",
      value: proof.constraint_status ?? "-",
    },
    {
      field: "SOC envelope",
      value:
        constraints.soc_min_mwh !== undefined && constraints.soc_max_mwh !== undefined
          ? `${constraints.soc_min_mwh} to ${constraints.soc_max_mwh} MWh`
          : "-",
    },
    {
      field: "No simultaneous charge/discharge",
      value: constraints.no_simultaneous_charge_discharge ?? "-",
    },
  ];
}

function formatOptimizerLabel(engine: string) {
  const labels: Record<string, string> = {
    linear_program_v1: "Linear program v1",
    linear_v1: "Linear v1",
    rule_based_v1: "Rule based v1",
  };

  return labels[engine] ?? engine.replaceAll("_", " ");
}

function buildScheduleColumns(assetType?: string) {
  const baseColumns = [
    "timestamp",
    "price",
    "action",
    "automation_role",
    "soc_mwh",
  ];

  if (assetType === "solar_colocated_battery") {
    return [
      ...baseColumns,
      "forecast_solar_mw",
      "renewable_charge_mwh",
      "grid_charge_mwh",
      "pnl_eur",
      "total_pnl_eur",
    ];
  }

  if (assetType === "industrial_behind_the_meter_battery") {
    return [
      ...baseColumns,
      "site_load_mw",
      "net_site_import_mwh",
      "peak_shaved_mwh",
      "pnl_eur",
      "total_pnl_eur",
    ];
  }

  return [...baseColumns, "pnl_eur", "total_pnl_eur"];
}

function buildPhysicalProofRows({
  assetPhysics,
  selectedAssetType,
  summary,
  validation,
}: {
  assetPhysics?: AssetPhysics;
  selectedAssetType?: string;
  summary: SignalSummary;
  validation?: TableRow;
}): TableRow[] {
  const rows: TableRow[] = [
    {
      physical_feature: "Validation status",
      value: validation?.status ?? "-",
      investor_meaning:
        validation?.status === "pass"
          ? "The mock dispatch passes SOC, power, PnL, and market-interval checks."
          : "Run or refresh the dispatch signal before relying on the physical proof.",
    },
    {
      physical_feature: "Validation issues",
      value: `${validation?.error_count ?? "-"} error(s) / ${validation?.warning_count ?? "-"} warning(s)`,
      investor_meaning:
        "Keeps mock evidence honest by showing whether physical constraints or data intervals failed validation.",
    },
    {
      physical_feature: "Physics model",
      value: formatPhysicsLabel(assetPhysics?.physics_model),
      investor_meaning:
        assetPhysics?.message ??
        "Dispatch physical model will appear after the selected asset signal is generated.",
    },
    {
      physical_feature: "Applied constraints",
      value: (assetPhysics?.constraints_applied ?? [])
        .map(formatPhysicsLabel)
        .join(", ") || "-",
      investor_meaning:
        "Shows which physical limits shaped the mock dispatch, beyond UI labels.",
    },
  ];

  if (selectedAssetType === "solar_colocated_battery") {
    rows.push({
      physical_feature: "Renewable-origin charge",
      value: `${formatNumber(summary.renewable_charge_mwh, 2)} MWh / ${formatNumber(Number(summary.renewable_charge_share ?? 0) * 100, 1)}%`,
      investor_meaning:
        "Confirms the solar demo charges from forecast solar energy instead of generic grid arbitrage.",
    });
  }

  if (selectedAssetType === "industrial_behind_the_meter_battery") {
    rows.push({
      physical_feature: "Peak shaved",
      value: `${formatNumber(summary.peak_shaved_mwh, 2)} MWh`,
      investor_meaning:
        "Confirms the industrial demo uses site load and peak limits, not only merchant price spread.",
    });
  }

  return rows;
}

function validationTone(status?: unknown) {
  if (status === "pass") {
    return "emerald";
  }
  if (status === "fail") {
    return "red";
  }
  return "amber";
}

function formatPhysicsLabel(value?: string) {
  if (!value) {
    return "-";
  }

  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getDispatchPersonaFraming(personaId: PersonaId): DispatchPersonaFraming {
  const defaults: DispatchPersonaFraming = {
    analyticsTitle: "Dispatch analytics",
    bridgeTitle: "Dispatch-to-order bridge",
    decisionEyebrow: "Schedule intent",
    decisionTitle: "Dispatch-to-bid decision",
    description:
      "Convert the optimizer signal into charge, discharge, SOC, and PnL intervals that can become a bid proposal after forecast, market-route, and risk gates pass.",
    eyebrow: "Optimization",
    nextActionClear:
      "Use this schedule as physical evidence for proposal generation, then validate against forecast confidence and risk gates before automated submission.",
    nextActionMissing:
      "Generate a dispatch signal before creating any order package or commercial dispatch claim.",
    runLabel: "Generate latest signal",
    scheduleTitle: "Automation schedule windows",
    summaryTitle: "Bid conversion summary",
    title: "Dispatch-to-bid schedule",
    whyThisPageMatters:
      "It turns optimizer economics into executable physical intervals.",
  };

  const frames: Partial<Record<PersonaId, DispatchPersonaFraming>> = {
    trading_desk: {
      analyticsTitle: "Desk dispatch analytics",
      bridgeTitle: "Dispatch-to-bid bridge",
      decisionEyebrow: "Desk execution intent",
      decisionTitle: "Can this schedule become a bid package?",
      description:
        "Convert the optimizer signal into charge and discharge windows the desk can use for proposal generation after forecast, market-route, and risk gates pass.",
      eyebrow: "Trading desk",
      nextActionClear:
        "Build the bid proposal from active windows, then check market allocation and risk gates before supervised submission.",
      nextActionMissing:
        "Generate a dispatch signal before the desk builds or reviews any bid package.",
      runLabel: "Generate desk signal",
      scheduleTitle: "Desk order windows",
      summaryTitle: "Bid package summary",
      title: "Desk dispatch schedule",
      whyThisPageMatters:
        "It converts optimizer output into the physical buy, sell, or hold windows used by the trading desk.",
    },
    forecast_quant: {
      analyticsTitle: "Optimizer behavior analytics",
      bridgeTitle: "Forecast-to-dispatch bridge",
      decisionEyebrow: "Model behavior intent",
      decisionTitle: "Does the forecast produce a sensible dispatch plan?",
      description:
        "Inspect how forecast and optimizer assumptions translate into SOC movement, action windows, PnL, and active intervals before the model output is trusted.",
      eyebrow: "Model quality OS",
      nextActionClear:
        "Use the schedule to validate optimizer behavior, then connect it to forecast performance and scenario stress evidence.",
      nextActionMissing:
        "Generate a signal so model behavior can be inspected against forecast and price assumptions.",
      runLabel: "Generate model signal",
      scheduleTitle: "Model action windows",
      summaryTitle: "Optimizer behavior summary",
      title: "Model dispatch evidence",
      whyThisPageMatters:
        "It shows whether forecast output becomes a physically plausible and commercially useful dispatch plan.",
    },
    revenue_analyst: {
      analyticsTitle: "Commercial dispatch analytics",
      bridgeTitle: "Dispatch-to-revenue bridge",
      decisionEyebrow: "Commercial dispatch intent",
      decisionTitle: "Does this dispatch plan support the revenue case?",
      description:
        "Translate charge, discharge, SOC, and expected PnL intervals into commercial evidence for revenue assurance, allocation, and client reporting.",
      eyebrow: "Commercial analytics OS",
      nextActionClear:
        "Use this schedule to support revenue allocation, settlement assumptions, and owner or investor evidence.",
      nextActionMissing:
        "Generate a dispatch signal before using dispatch economics in revenue assurance or client reporting.",
      runLabel: "Generate revenue signal",
      scheduleTitle: "Revenue schedule windows",
      summaryTitle: "Commercial dispatch summary",
      title: "Revenue dispatch evidence",
      whyThisPageMatters:
        "It turns optimizer economics into time-based operating evidence that explains where revenue is expected to come from.",
    },
  };

  return frames[personaId] ?? defaults;
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
