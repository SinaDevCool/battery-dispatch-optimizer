import type { ReactNode } from "react";

import { ActionButton } from "@/components/action-button";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency, formatNumber } from "@/lib/format";

type KpiTone = "amber" | "blue" | "emerald" | "red" | "slate";

type AutomationEvidence = {
  execution_proposal_id?: number | string | null;
  market_submission_id?: number | string | null;
  paper_trade_id?: number | string | null;
};

type AutomationControl = {
  automation_mode?: string | null;
  evidence?: AutomationEvidence | null;
  live_trading_allowed?: boolean | null;
  paper_trading_allowed?: boolean | null;
  supervised_trading_allowed?: boolean | null;
};

type AutomationAction = {
  action?: unknown;
  label?: ReactNode;
  message?: ReactNode;
  owner?: ReactNode;
};

export function ExecutionMissionSummary({
  automationStatus,
  blockers,
  control,
  decision,
  evidence,
  expectedPnl,
  guardrailBlocked,
  guardrailReview,
  humanGateRequired,
  humanGateStatus,
  isClientPersona,
  marketRoute,
  nextAutomationAction,
  primaryRouteHelper,
  profitPerMwDay,
  refetchExecution,
  selectedAssetId,
}: {
  automationStatus?: string;
  blockers: string[];
  control?: AutomationControl;
  decision: ReactNode;
  evidence: string[];
  expectedPnl: number;
  guardrailBlocked: number;
  guardrailReview: number;
  humanGateRequired: boolean;
  humanGateStatus?: unknown;
  isClientPersona: boolean;
  marketRoute?: string;
  nextAutomationAction: AutomationAction;
  primaryRouteHelper?: string;
  profitPerMwDay?: number;
  refetchExecution: () => Promise<unknown>;
  selectedAssetId: string;
}) {
  const blockerCount = blockers.length;

  return (
    <>
      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <KpiCard
          accent={controlModeTone(control?.automation_mode)}
          label={isClientPersona ? "Readiness mode" : "Automation mode"}
          value={control?.automation_mode ?? automationStatus ?? "-"}
          helper={
            isClientPersona
              ? control?.live_trading_allowed
                ? "Supervised execution is available"
                : "Execution remains gated"
              : control?.live_trading_allowed
                ? "Limited live auto allowed"
                : "Live auto gated"
          }
        />
        <KpiCard
          accent={actionTone(nextAutomationAction.action)}
          label={isClientPersona ? "Next step" : "Next auto action"}
          value={nextAutomationAction.label ?? "-"}
          helper={nextAutomationAction.owner ?? "Automation control"}
        />
        <KpiCard
          accent={expectedPnl >= 0 ? "emerald" : "red"}
          label={isClientPersona ? "Expected value" : "Expected PnL"}
          value={formatCurrency(expectedPnl)}
          helper={`${formatNumber(profitPerMwDay, 2)} EUR/MW-day`}
        />
        <KpiCard
          accent="blue"
          label="Market route"
          value={marketRoute ?? "-"}
          helper={primaryRouteHelper ?? "No route selected"}
        />
        <KpiCard
          accent={humanGateTone(humanGateStatus)}
          label={isClientPersona ? "Approval gate" : "Human gate"}
          value={String(humanGateStatus ?? "-")}
          helper={humanGateRequired ? "Required by policy" : "Not required"}
        />
        <KpiCard
          accent={blockerCount ? "red" : "emerald"}
          label="Blockers"
          value={blockerCount}
          helper={
            isClientPersona
              ? `${guardrailBlocked} blocker(s), ${guardrailReview} review item(s)`
              : `${guardrailBlocked} guardrail / ${guardrailReview} review`
          }
        />
      </div>

      <DecisionBrief
        blockers={blockers.slice(0, 4)}
        className="mb-6"
        decision={decision}
        evidence={evidence}
        eyebrow={isClientPersona ? "Execution readiness" : "Mission control"}
        nextAction={
          nextAutomationAction.message ??
          "No automated action has been evaluated yet."
        }
        title={
          isClientPersona
            ? "Can this asset advance toward approved execution?"
            : "Autonomous trading mission control"
        }
        tone={blockerCount ? "amber" : "emerald"}
      />

      {!isClientPersona ? (
        <SectionCard
          action={
            <div className="flex flex-wrap gap-2">
              <ActionButton
                endpoint={`/assets/${selectedAssetId}/execution/remediation/run-next`}
                label="Run next remediation"
                refetch={refetchExecution}
                variant="primary"
              />
              <ActionButton
                endpoint={`/assets/${selectedAssetId}/execution/orchestrator/run`}
                label="Run next auto action"
                refetch={refetchExecution}
              />
            </div>
          }
          className="mb-6"
          title="Automation engine"
        >
          <div className="grid gap-3 md:grid-cols-3">
            <SummaryTile
              eyebrow="Next action"
              title={nextAutomationAction.label ?? "-"}
              text={nextAutomationAction.message ?? "No automation action evaluated."}
            />
            <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                Mode permissions
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <StatusPill tone={control?.paper_trading_allowed ? "emerald" : "slate"}>
                  Paper
                </StatusPill>
                <StatusPill tone={control?.supervised_trading_allowed ? "emerald" : "slate"}>
                  Supervised
                </StatusPill>
                <StatusPill tone={control?.live_trading_allowed ? "emerald" : "red"}>
                  Live
                </StatusPill>
              </div>
            </div>
            <SummaryTile
              eyebrow="Evidence"
              title={`Proposal ${control?.evidence?.execution_proposal_id ?? "-"} / Paper ${control?.evidence?.paper_trade_id ?? "-"}`}
              text={`Human gate ${String(humanGateStatus ?? "-")} / Submission ${control?.evidence?.market_submission_id ?? "-"}`}
            />
          </div>
        </SectionCard>
      ) : null}
    </>
  );
}

function SummaryTile({
  eyebrow,
  text,
  title,
}: {
  eyebrow: string;
  text: ReactNode;
  title: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
        {eyebrow}
      </div>
      <div className="mt-2 text-sm font-semibold text-slate-100">
        {title}
      </div>
      <div className="mt-1 text-xs leading-5 text-slate-400">
        {text}
      </div>
    </div>
  );
}

function controlModeTone(value: unknown): KpiTone {
  if (value === "live" || value === "supervised_live") {
    return "emerald";
  }

  if (value === "blocked" || value === "disabled") {
    return "red";
  }

  if (value === "paper" || value === "paper_trading") {
    return "blue";
  }

  return "amber";
}

function actionTone(value: unknown): KpiTone {
  if (value === "submit_live" || value === "run_paper_trade" || value === "build_proposal") {
    return "emerald";
  }

  if (value === "blocked" || value === "stop") {
    return "red";
  }

  if (value === "request_human_gate" || value === "review") {
    return "amber";
  }

  return "blue";
}

function humanGateTone(value: unknown): KpiTone {
  if (value === "approved" || value === "not_required") {
    return "emerald";
  }

  if (value === "rejected" || value === "blocked") {
    return "red";
  }

  if (value === "requested" || value === "required") {
    return "amber";
  }

  return "blue";
}
