import Link from "next/link";

import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";

export type TradingPipelineStageStatus =
  | "blocked"
  | "complete"
  | "current"
  | "ready"
  | "waiting";

export type TradingPipelineStageId =
  | "allocation"
  | "approval"
  | "eligibility"
  | "paper"
  | "proposal"
  | "settlement"
  | "signal"
  | "submission";

export type TradingPipelineStage = {
  blockerCount?: number;
  evidence?: string;
  href: string;
  id: TradingPipelineStageId;
  label: string;
  nextAction?: string;
  status: TradingPipelineStageStatus;
};

export function TradingAutomationPipeline({
  currentStageId,
  stages,
  title = "Trading automation pipeline",
}: {
  currentStageId?: TradingPipelineStageId;
  stages: TradingPipelineStage[];
  title?: string;
}) {
  const activeStage =
    stages.find((stage) => stage.id === currentStageId) ??
    stages.find((stage) => stage.status === "current") ??
    stages.find((stage) => stage.status === "ready");

  return (
    <SectionCard
      action={
        <StatusPill tone={pipelineTone(activeStage?.status)}>
          {activeStage?.label ?? "Pipeline"}
        </StatusPill>
      }
      title={title}
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-8">
        {stages.map((stage, index) => {
          const isActive = stage.id === currentStageId || stage.status === "current";

          return (
            <Link
              className={[
                "min-h-36 rounded-lg border bg-slate-900/45 p-3 transition",
                isActive
                  ? "border-sky-300/60 bg-sky-400/10"
                  : "border-slate-800 hover:border-sky-400/40 hover:bg-sky-950/20",
              ].join(" ")}
              href={stage.href}
              key={stage.id}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                  {index + 1}
                </span>
                <StatusPill tone={pipelineTone(stage.status)}>
                  {stage.status}
                </StatusPill>
              </div>
              <div className="mt-4 text-sm font-semibold text-slate-100">
                {stage.label}
              </div>
              <div className="mt-2 min-h-10 text-xs leading-5 text-slate-400">
                {stage.evidence ?? "Awaiting evidence"}
              </div>
              <div className="mt-3 flex items-center justify-between gap-3 border-t border-slate-800 pt-3 text-xs">
                <span className="text-slate-500">Blockers</span>
                <span className={stage.blockerCount ? "text-amber-200" : "text-emerald-200"}>
                  {stage.blockerCount ?? 0}
                </span>
              </div>
              {stage.nextAction ? (
                <div className="mt-2 truncate text-xs text-sky-200" title={stage.nextAction}>
                  {stage.nextAction}
                </div>
              ) : null}
            </Link>
          );
        })}
      </div>
    </SectionCard>
  );
}

export function buildTradingAutomationPipelineStages({
  allocationReady,
  approvalStatus,
  eligibilityReady,
  paperTradeReady,
  proposalReady,
  settlementReady,
  signalReady,
  submissionReady,
  values,
}: {
  allocationReady: boolean;
  approvalStatus?: string;
  eligibilityReady: boolean;
  paperTradeReady: boolean;
  proposalReady: boolean;
  settlementReady: boolean;
  signalReady: boolean;
  submissionReady: boolean;
  values?: Partial<Record<TradingPipelineStageId, {
    blockerCount?: number;
    evidence?: string;
    nextAction?: string;
  }>>;
}): TradingPipelineStage[] {
  const approvalComplete =
    approvalStatus === "approved" ||
    approvalStatus === "passed" ||
    approvalStatus === "not_required";
  const approvalBlocked = approvalStatus === "blocked" || approvalStatus === "rejected";

  const stages: TradingPipelineStage[] = [
    {
      href: "/market-signals",
      id: "signal",
      label: "Signal",
      status: signalReady ? "complete" : "ready",
    },
    {
      href: "/market-rules",
      id: "eligibility",
      label: "Eligibility",
      status: eligibilityReady ? "complete" : signalReady ? "ready" : "waiting",
    },
    {
      href: "/execution/market-allocation",
      id: "allocation",
      label: "Allocation",
      status: allocationReady ? "complete" : eligibilityReady ? "ready" : "waiting",
    },
    {
      href: "/execution/proposals",
      id: "proposal",
      label: "Proposal",
      status: proposalReady ? "complete" : allocationReady ? "ready" : "waiting",
    },
    {
      href: "/execution/simulation",
      id: "paper",
      label: "Paper",
      status: paperTradeReady ? "complete" : proposalReady ? "ready" : "waiting",
    },
    {
      href: "/execution/risk-approval",
      id: "approval",
      label: "Approval",
      status: approvalComplete
        ? "complete"
        : approvalBlocked
          ? "blocked"
          : paperTradeReady
            ? "ready"
            : "waiting",
    },
    {
      href: "/execution/orchestrator",
      id: "submission",
      label: "Submission",
      status: submissionReady ? "complete" : approvalComplete || paperTradeReady ? "ready" : "waiting",
    },
    {
      href: "/execution/settlement",
      id: "settlement",
      label: "Settlement",
      status: settlementReady ? "complete" : submissionReady ? "ready" : "waiting",
    },
  ];

  return stages.map((stage) => ({
    ...stage,
    ...values?.[stage.id],
  }));
}

function pipelineTone(value: unknown) {
  if (value === "complete") {
    return "emerald";
  }

  if (value === "current" || value === "ready") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}
