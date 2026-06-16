"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type { JsonObject, TableRow, TradingOrchestratorResponse } from "@/types/api";

type OrchestratorPersonaFraming = {
  auditTitle: string;
  blockersTitle: string;
  bridgeTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  evidenceTitle: string;
  eyebrow: string;
  linksTitle: string;
  runTitle: string;
  title: string;
  workflowTitle: string;
};

const orchestratorTabs = [
  {
    id: "control",
    label: "Control",
    helper: "Bridge, next action, and links into the execution workflow.",
  },
  {
    id: "workflow",
    label: "Workflow",
    helper: "Current workflow steps plus blockers and review items.",
  },
  {
    id: "evidence",
    label: "Evidence",
    helper: "Backend evidence, audit trail, and last run result.",
  },
] as const;

type OrchestratorTabId = (typeof orchestratorTabs)[number]["id"];

export default function TradingOrchestratorPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();
  const [activeTab, setActiveTab] = useState<OrchestratorTabId>("control");
  const framing = getOrchestratorPersonaFraming(personaId);

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
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
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
        eyebrow={framing.decisionEyebrow}
        nextAction={
          nextAction?.message ??
          "Run the orchestrator to progress the next automated trading step."
        }
        title={framing.decisionTitle}
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

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={orchestratorTabs}
      />

      {activeTab === "control" ? (
        <div className="space-y-5">
          <SectionCard title={framing.bridgeTitle}>
            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <DataTable
                columns={["decision_input", "value"]}
                rows={[
                  {
                    decision_input: "Control purpose",
                    value:
                      "Selects the next automated trading step so the platform moves from signal to proposal, allocation, validation, approval, and submission without siloed operator handoffs.",
                  },
                  {
                    decision_input: "Current owner",
                    value: nextAction?.owner ?? "not assigned",
                  },
                  {
                    decision_input: "Current action",
                    value: nextAction?.action ?? "-",
                  },
                  {
                    decision_input: "Run endpoint",
                    value: `/assets/${selectedAssetId}/execution/orchestrator/run`,
                  },
                ]}
              />
              <DataTable
                columns={["capability", "backend_route", "status", "business_value"]}
                rows={orchestratorBridgeRows(selectedAssetId, evidence, data?.orchestrator_status)}
              />
            </div>
          </SectionCard>

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
              title={framing.runTitle}
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

            <SectionCard title={framing.linksTitle}>
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
        </div>
      ) : null}

      {activeTab === "workflow" ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)]">
          <SectionCard
            action={<StatusPill tone={stageTone(data?.orchestrator_status)}>{data?.orchestrator_status ?? "-"}</StatusPill>}
            title={framing.workflowTitle}
          >
            <DataTable
              columns={["step", "label", "status", "message"]}
              rows={formatWorkflow(activeWorkflow.length ? activeWorkflow : workflow.slice(0, 8))}
            />
          </SectionCard>

          <SectionCard
            action={<StatusPill tone={blockers.length ? "amber" : "emerald"}>{blockers.length}</StatusPill>}
            title={framing.blockersTitle}
          >
            <DataTable
              columns={["source", "status", "blocker"]}
              rows={blockerRows}
            />
          </SectionCard>
        </div>
      ) : null}

      {activeTab === "evidence" ? (
        <div className="space-y-5">
          <div className="grid gap-5 xl:grid-cols-2">
            <SectionCard title={framing.evidenceTitle}>
              <DataTable
                columns={["metric", "value"]}
                rows={formatEvidence(evidence).slice(0, 12)}
              />
            </SectionCard>

            <SectionCard title={framing.auditTitle}>
              <DataTable
                columns={["event", "actor", "status", "note"]}
                rows={(data?.audit ?? []).slice(0, 8)}
              />
            </SectionCard>
          </div>

          {data?.executed_actions?.length ? (
            <SectionCard title="Last run result">
              <DataTable
                columns={["action", "status", "message", "record_id"]}
                rows={data.executed_actions}
              />
            </SectionCard>
          ) : null}
        </div>
      ) : null}
    </>
  );
}

function getOrchestratorPersonaFraming(
  personaId: PersonaId,
): OrchestratorPersonaFraming {
  const defaults: OrchestratorPersonaFraming = {
    auditTitle: "Orchestrator audit",
    blockersTitle: "Blockers and review items",
    bridgeTitle: "Orchestrator-to-execution bridge",
    decisionEyebrow: "Orchestration decision",
    decisionTitle: "What should automation do next?",
    description:
      "Coordinate the automated trading workflow from market signal through proposal, policy, market allocation, paper validation, approval, and supervised submission readiness.",
    evidenceTitle: "Execution evidence",
    eyebrow: "Trading operations",
    linksTitle: "Workflow links",
    runTitle: "Automation decision",
    title: "Trading orchestrator",
    workflowTitle: "Workflow state",
  };

  const frames: Partial<Record<PersonaId, OrchestratorPersonaFraming>> = {
    automation_operator: {
      auditTitle: "Automation run audit",
      blockersTitle: "Operator blockers and review items",
      bridgeTitle: "Automation runbook bridge",
      decisionEyebrow: "Operator orchestration decision",
      decisionTitle: "Which automation step should run next?",
      description:
        "Operate the end-to-end automation runbook from signal to proposal, route, policy, paper validation, approval, and supervised submission readiness.",
      evidenceTitle: "Automation run evidence",
      eyebrow: "Internal automation OS",
      linksTitle: "Operator workflow links",
      runTitle: "Next automation run step",
      title: "Automation orchestrator",
      workflowTitle: "Automation workflow state",
    },
    trading_desk: {
      auditTitle: "Desk handoff audit",
      blockersTitle: "Desk blockers and review items",
      bridgeTitle: "Signal-to-desk handoff bridge",
      decisionEyebrow: "Desk orchestration decision",
      decisionTitle: "What should the desk do next?",
      description:
        "Show the trading desk where the workflow sits between signal, proposal, paper validation, approval, and supervised execution handoff.",
      evidenceTitle: "Desk execution evidence",
      eyebrow: "Trading desk",
      linksTitle: "Desk workflow links",
      runTitle: "Desk handoff decision",
      title: "Desk workflow orchestrator",
      workflowTitle: "Desk workflow state",
    },
    risk_compliance: {
      auditTitle: "Governance orchestration audit",
      blockersTitle: "Governance blockers and review items",
      bridgeTitle: "Orchestration-to-governance bridge",
      decisionEyebrow: "Governance orchestration decision",
      decisionTitle: "Is the workflow allowed to progress?",
      description:
        "Trace each automation step through proposal, policy, paper validation, approval, and submission readiness so governance can defend why the workflow progressed or stopped.",
      evidenceTitle: "Governance execution evidence",
      eyebrow: "Risk & compliance",
      linksTitle: "Governance workflow links",
      runTitle: "Governed next-step decision",
      title: "Workflow governance orchestrator",
      workflowTitle: "Governed workflow state",
    },
    market_operations: {
      auditTitle: "Route operations audit",
      blockersTitle: "Route blockers and review items",
      bridgeTitle: "Orchestration-to-route bridge",
      decisionEyebrow: "Market operations orchestration decision",
      decisionTitle: "Which route or connector step blocks progress?",
      description:
        "Connect orchestration state to market route allocation, connector readiness, paper validation, and submission readiness so market operations can clear the right dependency.",
      evidenceTitle: "Route execution evidence",
      eyebrow: "Market operations",
      linksTitle: "Route workflow links",
      runTitle: "Route next-step decision",
      title: "Market route orchestrator",
      workflowTitle: "Route workflow state",
    },
  };

  return frames[personaId] ?? defaults;
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

function orchestratorBridgeRows(
  assetId: string,
  evidence: JsonObject,
  orchestratorStatus: string | undefined,
) {
  return [
    {
      backend_route: `/assets/${assetId}/execution/orchestrator/status`,
      business_value: "Combines every trading gate into one next-step decision.",
      capability: "Orchestration status",
      status: orchestratorStatus ?? "not loaded",
    },
    {
      backend_route: `/assets/${assetId}/signal/latest`,
      business_value: "Provides the trading signal that starts the workflow.",
      capability: "Market signal",
      status: String(evidence.signal ?? "-"),
    },
    {
      backend_route: `/assets/${assetId}/execution/automation-control/status`,
      business_value: "Prevents the orchestrator from escalating beyond approved automation mode.",
      capability: "Automation policy",
      status: String(evidence.policy_decision ?? "-"),
    },
    {
      backend_route: `/assets/${assetId}/execution/multi-market/allocation`,
      business_value: "Selects the market route before bid creation.",
      capability: "Market allocation",
      status: String(evidence.allocation_status ?? "-"),
    },
    {
      backend_route: `/assets/${assetId}/execution/proposal/latest`,
      business_value: "Turns dispatch into bid-ready order evidence.",
      capability: "Bid proposal",
      status: String(evidence.execution_proposal_id ?? "No proposal"),
    },
    {
      backend_route: `/assets/${assetId}/execution/paper-trade/latest`,
      business_value: "Validates the bid lifecycle before live submission.",
      capability: "Paper validation",
      status: String(evidence.paper_trade_id ?? "No paper trade"),
    },
    {
      backend_route: `/assets/${assetId}/execution/approval/latest`,
      business_value: "Applies human approval and four-eyes checks where policy requires it.",
      capability: "Risk and approval",
      status: String(evidence.approval_status ?? "No approval"),
    },
  ];
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
