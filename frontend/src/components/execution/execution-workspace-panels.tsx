import { Activity, Send, ShieldCheck, UserCheck } from "lucide-react";

import { ActionButton } from "@/components/action-button";
import { DataTable } from "@/components/data-table";
import { ExecutionMetric } from "@/components/execution/execution-metric";
import { AssetTelemetryPanel } from "@/components/execution/market-evidence-panels";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  AssetMarketAdapterStatusResponse,
  AssetTelemetryResponse,
  AutomationEvent,
  ExecutionApproval,
  ExecutionProposal,
  ExecutionReadinessResponse,
  JsonObject,
  TableRow,
} from "@/types/api";

type RefetchExecution = () => Promise<unknown>;

export function ExecutionOverviewPanel({
  approvalData,
  automationStatus,
  bids,
  hardBlockers,
  marketAdapterStatus,
  paperTrade,
  proposal,
  readiness,
  refetchExecution,
  selectedAssetId,
  submission,
  telemetryData,
}: {
  approvalData?: ExecutionApproval | null;
  automationStatus?: string;
  bids: TableRow[];
  hardBlockers: string[];
  marketAdapterStatus?: AssetMarketAdapterStatusResponse;
  paperTrade?: TableRow | null;
  proposal?: ExecutionProposal | null;
  readiness?: ExecutionReadinessResponse;
  refetchExecution: RefetchExecution;
  selectedAssetId: string;
  submission?: TableRow | null;
  telemetryData: AssetTelemetryResponse["telemetry"];
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
      <SectionCard
        action={<StatusPill tone={automationTone(automationStatus)}>{automationStatus ?? "not evaluated"}</StatusPill>}
        title="Automation command sequence"
      >
        <div className="mb-5 flex flex-wrap gap-3">
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/proposal/build`}
            label="Build proposal"
            refetch={refetchExecution}
            variant="primary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/approval/request`}
            label="Request human gate"
            refetch={refetchExecution}
            variant="secondary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/approval/approve`}
            label="Clear human gate"
            refetch={refetchExecution}
            variant="secondary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/paper-trade/run`}
            label="Run auto paper"
            refetch={refetchExecution}
            variant="secondary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/demo-submit`}
            label="Simulate submission"
            refetch={refetchExecution}
            variant="secondary"
          />
        </div>
        <div className="grid gap-3 md:grid-cols-5">
          <WorkflowStep icon={<Activity className="h-4 w-4" />} label="Signal" status={proposal?.signal_id ? "complete" : "pending"} />
          <WorkflowStep icon={<ShieldCheck className="h-4 w-4" />} label="Risk" status={hardBlockers.length ? "blocked" : bids.length ? "complete" : "pending"} />
          <WorkflowStep icon={<UserCheck className="h-4 w-4" />} label="Human gate" status={approvalData?.status === "approved" ? "complete" : "required"} />
          <WorkflowStep icon={<Activity className="h-4 w-4" />} label="Paper" status={paperTrade ? "complete" : "pending"} />
          <WorkflowStep icon={<Send className="h-4 w-4" />} label="Submit" status={submission ? "complete" : "disabled"} />
        </div>
      </SectionCard>

      <div className="space-y-5">
        <SectionCard
          action={<StatusPill tone={readinessTone(readiness?.readiness_status)}>{readiness?.readiness_status ?? "not evaluated"}</StatusPill>}
          title="Automation evidence snapshot"
        >
          <div className="grid gap-3 md:grid-cols-2">
            <ExecutionMetric
              label="Readiness score"
              value={formatNumber(readiness?.readiness_score, 1)}
            />
            <ExecutionMetric
              label="Connected markets"
              value={formatNumber(marketAdapterStatus?.connected_adapter_count, 0)}
            />
            <ExecutionMetric
              label="SOC"
              value={`${formatNumber(telemetryData?.soc_percent, 1)}%`}
            />
            <ExecutionMetric
              label="Draft bids"
              value={formatNumber(bids.length, 0)}
            />
          </div>
          <div className="mt-4">
            <DataTable
              columns={["evidence", "status", "automation_use"]}
              rows={[
                {
                  automation_use: "Blocks live submission when readiness is red",
                  evidence: "Execution readiness",
                  status: readiness?.readiness_status ?? "-",
                },
                {
                  automation_use: "Selects whether EPEX or ancillary routes can be submitted",
                  evidence: "Market adapters",
                  status: marketAdapterStatus?.market_adapter_status ?? "-",
                },
                {
                  automation_use: "Validates physical ability to follow automated orders",
                  evidence: "Asset telemetry",
                  status: telemetryData?.availability_status ?? "missing",
                },
                {
                  automation_use: "Carries the proposed automated order package",
                  evidence: "Bid package",
                  status: proposal?.status ?? "-",
                },
              ]}
            />
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

export function ExecutionRiskApprovalPanel({
  approvalData,
  automationBlockers,
  automationStatus,
  confidence,
  guardrailSummary,
  guardrails,
  hardBlockers,
  refetchExecution,
  selectedAssetId,
}: {
  approvalData?: ExecutionApproval | null;
  automationBlockers: string[];
  automationStatus?: string;
  confidence?: JsonObject;
  guardrailSummary: JsonObject;
  guardrails: TableRow[];
  hardBlockers: string[];
  refetchExecution: RefetchExecution;
  selectedAssetId: string;
}) {
  const riskPolicy = confidence?.risk_policy as JsonObject | undefined;

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
      <div className="space-y-5">
        <SectionCard
          action={<StatusPill tone={automationTone(automationStatus)}>{automationStatus ?? "not evaluated"}</StatusPill>}
          title="Automation guardrails"
        >
          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <ExecutionMetric label="Passed" value={formatNumber(guardrailSummary.passed, 0)} />
            <ExecutionMetric label="Review" value={formatNumber(guardrailSummary.review, 0)} />
            <ExecutionMetric label="Blocked" value={formatNumber(guardrailSummary.blocked, 0)} />
          </div>
          <DataTable columns={["guardrail", "status", "message", "context"]} rows={guardrails.slice(0, 8)} />
        </SectionCard>
        <SectionCard
          action={<StatusPill tone={confidenceTone(confidence?.confidence_band)}>{String(confidence?.confidence_band ?? "unscored")}</StatusPill>}
          title="Forecast confidence"
        >
          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <ExecutionMetric label="Confidence score" value={formatNumber(confidence?.confidence_score, 1)} />
            <ExecutionMetric label="Volume multiplier" value={formatNumber(riskPolicy?.volume_multiplier, 2)} />
            <ExecutionMetric label="Automation" value={String(confidence?.automation_eligibility ?? "-")} />
          </div>
          <DataTable
            columns={[
              "forecast_actual_id",
              "forecast_model",
              "mae_eur_per_mwh",
              "rmse_eur_per_mwh",
              "revenue_delta_eur",
              "score",
            ]}
            rows={((confidence?.evidence as TableRow[]) ?? []).slice(0, 8)}
          />
        </SectionCard>
      </div>
      <div className="space-y-5">
        <SectionCard
          action={<StatusPill tone={approvalTone(approvalData?.status)}>{approvalData?.status ?? "missing"}</StatusPill>}
          title="Human automation gate"
        >
          <div className="mb-4 flex flex-wrap gap-3">
            <ActionButton endpoint={`/assets/${selectedAssetId}/execution/approval/request`} label="Request human gate" refetch={refetchExecution} variant="primary" />
            <ActionButton endpoint={`/assets/${selectedAssetId}/execution/approval/approve`} label="Clear gate" refetch={refetchExecution} variant="secondary" />
            <ActionButton endpoint={`/assets/${selectedAssetId}/execution/approval/reject`} label="Block gate" refetch={refetchExecution} variant="secondary" />
          </div>
          <DataTable
            columns={[
              "approval_id",
              "execution_proposal_id",
              "status",
              "requested_by",
              "requested_at",
              "decided_by",
              "decided_at",
              "reason",
            ]}
            rows={approvalData ? [approvalData] : []}
          />
        </SectionCard>
        <SectionCard
          action={<StatusPill tone={hardBlockers.length ? "red" : "blue"}>{hardBlockers.length}</StatusPill>}
          title="Hard blockers"
        >
          <DataTable
            columns={["blocker"]}
            rows={hardBlockers.slice(0, 6).map((blocker) => ({ blocker }))}
          />
        </SectionCard>
        <SectionCard action={<StatusPill tone="amber">{automationBlockers.length}</StatusPill>} title="Automation blockers">
          <DataTable
            columns={["blocker"]}
            rows={automationBlockers.slice(0, 6).map((blocker) => ({ blocker }))}
          />
        </SectionCard>
      </div>
    </div>
  );
}

export function ExecutionSimulationPanel({
  paperFills,
  paperHistoryRows,
  paperTradeRunCount,
  refetchExecution,
  selectedAssetId,
  submission,
  submissionSummary,
}: {
  paperFills: TableRow[];
  paperHistoryRows: TableRow[];
  paperTradeRunCount: number;
  refetchExecution: RefetchExecution;
  selectedAssetId: string;
  submission?: TableRow | null;
  submissionSummary: JsonObject;
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <div className="space-y-5">
        <SectionCard
          action={<ActionButton endpoint={`/assets/${selectedAssetId}/execution/paper-trade/run`} label="Run paper trade" refetch={refetchExecution} variant="primary" />}
          title="Latest automatic paper trade"
        >
          <DataTable
            columns={[
              "delivery_time",
              "market_product_id",
              "side",
              "filled_volume_mwh",
              "fill_price_eur_mwh",
              "notional_eur",
              "status",
            ]}
            rows={paperFills.slice(0, 8)}
          />
        </SectionCard>
        <SectionCard
          action={<StatusPill tone={paperTradeRunCount ? "emerald" : "slate"}>{paperTradeRunCount} run(s)</StatusPill>}
          title="Paper trade history"
        >
          <DataTable
            columns={[
              "paper_trade_id",
              "generated_at",
              "status",
              "filled_order_count",
              "paper_pnl_eur",
              "paper_vs_expected_delta_eur",
            ]}
            rows={paperHistoryRows.slice(0, 6)}
          />
        </SectionCard>
      </div>
      <SectionCard
        action={<ActionButton endpoint={`/assets/${selectedAssetId}/execution/demo-submit`} label="Simulate bid submission" refetch={refetchExecution} variant="primary" />}
        title="Simulated market submission"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <ExecutionMetric label="Submitted" value={formatNumber(submissionSummary.submitted_bid_count, 0)} />
          <ExecutionMetric label="Accepted" value={formatNumber(submissionSummary.accepted_bid_count, 0)} />
          <ExecutionMetric label="Awarded notional" value={formatCurrency(submissionSummary.notional_eur)} />
        </div>
        <DataTable columns={["step", "label", "status", "owner"]} rows={((submission?.lifecycle as TableRow[]) ?? []).slice(0, 6)} />
      </SectionCard>
    </div>
  );
}

export function ExecutionSettlementPanel({
  refetchExecution,
  selectedAssetId,
  settlementSummary,
  varianceDrivers,
}: {
  refetchExecution: RefetchExecution;
  selectedAssetId: string;
  settlementSummary: JsonObject;
  varianceDrivers: TableRow[];
}) {
  return (
    <div className="space-y-5">
      <SectionCard
        action={<ActionButton endpoint={`/assets/${selectedAssetId}/settlement/reconcile`} label="Reconcile settlement" refetch={refetchExecution} variant="primary" />}
        title="Settlement reconciliation"
      >
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <ExecutionMetric label="Expected PnL" value={formatCurrency(settlementSummary.expected_pnl_eur)} />
          <ExecutionMetric label="Paper PnL" value={formatCurrency(settlementSummary.paper_pnl_eur)} />
          <ExecutionMetric label="Realized PnL" value={formatCurrency(settlementSummary.realized_pnl_eur)} />
        </div>
        <DataTable columns={["driver", "severity", "delta_eur", "message"]} rows={varianceDrivers.slice(0, 8)} />
      </SectionCard>
    </div>
  );
}

export function ExecutionAuditPanel({
  auditRows,
  automationEvents,
  lifecycleRows,
  riskChecks,
  telemetryData,
}: {
  auditRows: TableRow[];
  automationEvents: AutomationEvent[];
  lifecycleRows: TableRow[];
  riskChecks: TableRow[];
  telemetryData: AssetTelemetryResponse["telemetry"];
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <SectionCard title="Bid lifecycle">
        <DataTable columns={["step", "label", "status", "owner"]} rows={lifecycleRows.slice(0, 6)} />
      </SectionCard>
      <SectionCard title="Backend risk checks">
        <DataTable columns={["check", "status", "message"]} rows={riskChecks.slice(0, 8)} />
      </SectionCard>

      <SectionCard
        action={<StatusPill tone={automationEvents.length ? "emerald" : "slate"}>{automationEvents.length}</StatusPill>}
        title="Automation event trail"
      >
        <DataTable
          columns={[
            "created_at",
            "event_type",
            "action",
            "status",
            "automation_mode_after",
            "strategy_mode_after",
            "error_type",
          ]}
          rows={automationEvents.slice(0, 8)}
        />
      </SectionCard>

      <SectionCard
        action={<StatusPill tone="blue">Pre-trade audit</StatusPill>}
        title="Execution audit trail"
      >
        <DataTable columns={["event", "actor", "status", "note"]} rows={auditRows.slice(0, 10)} />
      </SectionCard>
      <AssetTelemetryPanel telemetryData={telemetryData} />
    </div>
  );
}

function WorkflowStep({
  icon,
  label,
  status,
}: {
  icon: React.ReactNode;
  label: string;
  status: "blocked" | "complete" | "disabled" | "pending" | "required";
}) {
  const toneByStatus = {
    blocked: "red",
    complete: "emerald",
    disabled: "amber",
    pending: "slate",
    required: "blue",
  } as const;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <span className="text-sky-300">{icon}</span>
        {label}
      </div>
      <div className="mt-4">
        <StatusPill tone={toneByStatus[status]}>{status}</StatusPill>
      </div>
    </div>
  );
}

function confidenceTone(value: unknown) {
  if (value === "high") {
    return "emerald";
  }

  if (value === "medium") {
    return "blue";
  }

  if (value === "low") {
    return "amber";
  }

  return "slate";
}

function automationTone(value: unknown) {
  if (value === "supervised_live_candidate") {
    return "emerald";
  }

  if (value === "human_approval_required") {
    return "blue";
  }

  if (value === "paper_only") {
    return "amber";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function approvalTone(value: unknown) {
  if (value === "approved") {
    return "emerald";
  }

  if (value === "requested") {
    return "blue";
  }

  if (value === "rejected") {
    return "red";
  }

  return "slate";
}

function readinessTone(value: unknown) {
  if (value === "supervised_ready" || value === "ready") {
    return "emerald";
  }

  if (value === "operator_review_required" || value === "review") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}
