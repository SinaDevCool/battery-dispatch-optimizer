"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { JsonObject, TableRow, TradingOrchestratorResponse } from "@/types/api";

export default function TradingOrchestratorPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();

  const orchestrator = useQuery({
    queryFn: () =>
      apiGet<TradingOrchestratorResponse>(
        `/assets/${selectedAssetId}/execution/orchestrator/status`,
      ),
    queryKey: ["trading-orchestrator-status", selectedAssetId],
  });

  const data = orchestrator.data;
  const nextAction = data?.next_action;
  const evidence = data?.evidence ?? {};
  const workflow = data?.workflow ?? [];
  const blockers = data?.blockers ?? [];
  const activeWorkflow = workflow
    .filter((row) => row.status !== "complete")
    .slice(0, 8);
  const blockerRows = blockers.slice(0, 6);

  return (
    <>
      <PageHeading
        description="Coordinate the automated trading workflow from market signal through proposal, policy, market allocation, paper validation, approval, and supervised submission readiness."
        eyebrow="Trading operations"
        title="Trading orchestrator"
      />

      <DecisionBrief
        blockers={blockerRows.map((blocker) =>
          String(blocker.blocker ?? blocker.message ?? blocker.status ?? "Workflow blocker"),
        )}
        className="mb-6"
        decision={
          <>
            {data?.orchestrator_status ?? "orchestration pending"}
            <span className="text-slate-500"> / </span>
            {nextAction?.label ?? "next action pending"}
          </>
        }
        evidence={[
          `Current owner: ${nextAction?.owner ?? "not assigned"}.`,
          `Target market: ${nextAction?.target_market ?? evidence.primary_market ?? "-"}.`,
          `${workflow.length} workflow step(s) tracked across signal, proposal, policy, paper, approval, and submission.`,
        ]}
        eyebrow="Orchestration decision"
        nextAction={
          nextAction?.message ??
          "Run the orchestrator to progress the next automated trading step."
        }
        title="What should automation do next?"
        tone={blockerRows.length ? "amber" : stageTone(data?.orchestrator_status)}
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={stageTone(data?.orchestrator_status)}
          helper={data?.stage?.message ?? "Awaiting orchestration state"}
          label="Current stage"
          value={data?.orchestrator_status ?? "-"}
        />
        <KpiCard
          accent={actionTone(nextAction?.action)}
          helper={nextAction?.owner ?? "No owner assigned"}
          label="Next action"
          value={nextAction?.label ?? "-"}
        />
        <KpiCard
          accent={blockers.length ? "amber" : "emerald"}
          helper="Policy, readiness, guardrail, and market-route issues"
          label="Open blockers"
          value={blockers.length}
        />
        <KpiCard
          accent="blue"
          helper={selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId}
          label="Target market"
          value={nextAction?.target_market ?? String(evidence.primary_market ?? "-")}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.75fr)]">
        <SectionCard
          action={
            <ActionButton
              endpoint={`/assets/${selectedAssetId}/execution/orchestrator/run`}
              label="Run next step"
              refetch={() => orchestrator.refetch()}
              variant="primary"
            />
          }
          title="Automation decision"
        >
          <div className="grid gap-3 md:grid-cols-2">
            <DecisionRow
              label="Stage"
              tone={stageTone(data?.orchestrator_status)}
              value={data?.stage?.status ?? "-"}
            />
            <DecisionRow
              label="Action"
              tone={actionTone(nextAction?.action)}
              value={nextAction?.action ?? "-"}
            />
            <DecisionRow
              label="Owner"
              tone="blue"
              value={nextAction?.owner ?? "-"}
            />
            <DecisionRow
              label="Generated"
              tone="slate"
              value={formatDateTime(data?.generated_at)}
            />
          </div>
          <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/45 p-4 text-sm leading-6 text-slate-300">
            {nextAction?.message ?? "The orchestrator has not returned a next action yet."}
          </div>
        </SectionCard>

        <SectionCard title="Workflow links">
          <div className="space-y-3">
            <WorkflowLink href="/market-signals" label="Market Signals" value={String(evidence.signal ?? "-")} />
            <WorkflowLink href="/execution/automation-policies" label="Automation Policies" value={String(evidence.policy_decision ?? "-")} />
            <WorkflowLink href="/execution/market-allocation" label="Market Allocation" value={String(evidence.allocation_status ?? "-")} />
            <WorkflowLink href="/execution/proposals" label="Bid Proposals" value={String(evidence.execution_proposal_id ?? "No proposal")} />
            <WorkflowLink href="/execution/simulation" label="Simulation" value={String(evidence.paper_trade_id ?? "No paper trade")} />
            <WorkflowLink href="/execution/risk-approval" label="Risk & Approval" value={String(evidence.approval_status ?? "No approval")} />
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={stageTone(data?.orchestrator_status)}>{data?.orchestrator_status ?? "-"}</StatusPill>}
          title="Workflow state"
        >
          <DataTable
            columns={["step", "label", "status", "message"]}
            rows={formatWorkflow(activeWorkflow.length ? activeWorkflow : workflow.slice(0, 8))}
          />
        </SectionCard>

        <SectionCard
          action={<StatusPill tone={blockers.length ? "amber" : "emerald"}>{blockers.length}</StatusPill>}
          title="Blockers and review items"
        >
          <DataTable
            columns={["source", "status", "blocker"]}
            rows={blockerRows}
          />
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Execution evidence">
          <DataTable
            columns={["metric", "value"]}
            rows={formatEvidence(evidence).slice(0, 12)}
          />
        </SectionCard>

        <SectionCard title="Orchestrator audit">
          <DataTable
            columns={["event", "actor", "status", "note"]}
            rows={(data?.audit ?? []).slice(0, 8)}
          />
        </SectionCard>
      </div>

      {data?.executed_actions?.length ? (
        <div className="mt-5">
          <SectionCard title="Last run result">
            <DataTable
              columns={["action", "status", "message", "record_id"]}
              rows={data.executed_actions}
            />
          </SectionCard>
        </div>
      ) : null}
    </>
  );
}

function DecisionRow({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "amber" | "blue" | "emerald" | "red" | "slate";
  value: React.ReactNode;
}) {
  return (
    <div className="flex min-h-14 items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3">
      <span className="text-sm text-slate-300">{label}</span>
      <StatusPill tone={tone}>{value}</StatusPill>
    </div>
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

function formatWorkflow(rows: TableRow[]) {
  return rows.map((row) => ({
    ...row,
    message: row.message ?? "-",
  }));
}

function formatEvidence(evidence: JsonObject) {
  return Object.entries(evidence).map(([metric, value]) => ({
    metric,
    value: value === null || value === undefined || value === "" ? "-" : String(value),
  }));
}

function stageTone(value: unknown) {
  if (value === "supervised_submission_ready") {
    return "emerald";
  }

  if (
    value === "proposal_required" ||
    value === "paper_validation_required" ||
    value === "approval_required" ||
    value === "paper_mode_ready" ||
    value === "operator_review_required"
  ) {
    return "blue";
  }

  if (value === "waiting_for_signal") {
    return "amber";
  }

  if (value === "policy_blocked" || value === "market_route_blocked") {
    return "red";
  }

  return "slate";
}

function actionTone(value: unknown) {
  if (value === "prepare_supervised_submission") {
    return "emerald";
  }

  if (
    value === "build_proposal" ||
    value === "run_paper_trade" ||
    value === "request_approval" ||
    value === "hold_for_review"
  ) {
    return "blue";
  }

  if (value === "wait_for_signal") {
    return "amber";
  }

  if (value === "pause") {
    return "red";
  }

  return "slate";
}
