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
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type {
  AutomationPolicy,
  AutomationControlStatusResponse,
  AutomationPolicyEvaluationResponse,
  AutomationPolicyHistoryResponse,
  AutomationPolicyResponse,
  JsonValue,
  TableRow,
} from "@/types/api";

export default function AutomationPoliciesPage() {
  const { selectedAssetId } = useAssetContext();

  const policy = useQuery({
    queryFn: () =>
      apiGet<AutomationPolicyResponse>(
        `/assets/${selectedAssetId}/execution/automation-policy`,
      ),
    queryKey: ["automation-policy", selectedAssetId],
  });

  const automationControl = useQuery({
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["automation-control-status", selectedAssetId],
  });

  const evaluation = useQuery({
    queryFn: () =>
      apiGet<AutomationPolicyEvaluationResponse>(
        `/assets/${selectedAssetId}/execution/automation-policy/evaluation`,
      ),
    queryKey: ["automation-policy-evaluation", selectedAssetId],
  });

  const history = useQuery({
    queryFn: () =>
      apiGet<AutomationPolicyHistoryResponse>(
        `/assets/${selectedAssetId}/execution/automation-policies?limit=10`,
      ),
    queryKey: ["automation-policy-history", selectedAssetId],
  });

  const currentPolicy = policy.data?.policy;
  const riskLimits = currentPolicy?.risk_limits ?? {};
  const confidencePolicy = currentPolicy?.confidence_policy ?? {};
  const approvalPolicy = currentPolicy?.approval_policy ?? {};
  const simulationPolicy = currentPolicy?.simulation_policy ?? {};
  const fallbackPolicy = currentPolicy?.fallback_policy ?? {};
  const policyDecision = evaluation.data?.policy_decision;
  const checks = evaluation.data?.checks ?? [];
  const summary = evaluation.data?.summary ?? {};
  const control = automationControl.data;
  const humanGate = control?.human_gate ?? {};
  const nextAutomationAction = control?.next_automation_action ?? {};
  const blockerRows = (control?.blockers ?? []).slice(0, 6);
  const criticalCheckRows = checks
    .filter((check) => check.status !== "passed")
    .slice(0, 6);

  const refetchPolicy = () =>
    Promise.all([
      policy.refetch(),
      evaluation.refetch(),
      history.refetch(),
      automationControl.refetch(),
    ]);

  return (
    <>
      <PageHeading
        description="Control automated battery trading by mode: advisory, paper trading, supervised automation, and limited live automation with hard risk, confidence, connector, and human-gate constraints."
        eyebrow="Trading operations"
        title="Automation control plane"
      />

      <DecisionBrief
        blockers={blockerRows.map((blocker) =>
          String(blocker.message ?? blocker.key ?? "Automation blocker"),
        )}
        className="mb-6"
        decision={
          <>
            {policyDecision ?? "Policy pending"}
            <span className="text-slate-500"> / </span>
            {control?.automation_mode ?? currentPolicy?.automation_mode ?? "mode pending"}
          </>
        }
        evidence={[
          `${summary.passed ?? 0} policy gate(s) passed.`,
          `${summary.blocked ?? 0} blocked and ${summary.review ?? 0} review gate(s).`,
          control?.live_trading_allowed
            ? "Limited live submission is permitted by the control plane."
            : "Live submission remains gated by policy evidence.",
        ]}
        eyebrow="Automation policy decision"
        nextAction={
          nextAutomationAction.message ??
          "Evaluate policy gates before changing automated trading mode."
        }
        title="Can the asset trade automatically?"
        tone={policyDecision === "blocked" ? "red" : blockerRows.length ? "amber" : "emerald"}
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={controlModeTone(control?.automation_mode)}
          helper={control?.live_trading_allowed ? "Live submission permitted by control plane" : "Live submission gated"}
          label="Trading mode"
          value={control?.automation_mode ?? currentPolicy?.automation_mode ?? "-"}
        />
        <KpiCard
          accent={decisionTone(policyDecision)}
          helper={`${summary.blocked ?? 0} blocked / ${summary.review ?? 0} review gate(s)`}
          label="Policy decision"
          value={policyDecision ?? "-"}
        />
        <KpiCard
          accent={control?.paper_trading_allowed ? "emerald" : "slate"}
          helper={nextAutomationAction.message ?? "No automation action evaluated"}
          label="Next auto action"
          value={nextAutomationAction.label ?? "-"}
        />
        <KpiCard
          accent={humanGateTone(humanGate.status)}
          helper={humanGate.required ? "Human gate remains part of automation policy" : "No human gate required"}
          label="Human gate"
          value={String(humanGate.status ?? "-")}
        />
      </div>

      <div className="mb-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.75fr)]">
        <SectionCard
          action={<StatusPill tone={controlModeTone(control?.automation_mode)}>{control?.automation_mode ?? "-"}</StatusPill>}
          title="Automated trading status"
        >
          <div className="grid gap-3 md:grid-cols-3">
            <PolicyRow
              label="Paper trading"
              tone={control?.paper_trading_allowed ? "emerald" : "slate"}
              value={control?.paper_trading_allowed ? "allowed" : "gated"}
            />
            <PolicyRow
              label="Supervised auto"
              tone={control?.supervised_trading_allowed ? "emerald" : "amber"}
              value={control?.supervised_trading_allowed ? "allowed" : "gated"}
            />
            <PolicyRow
              label="Limited live auto"
              tone={control?.live_trading_allowed ? "emerald" : "red"}
              value={control?.live_trading_allowed ? "allowed" : "blocked"}
            />
            <PolicyRow
              label="Readiness"
              tone={control?.readiness_status === "blocked" ? "red" : "blue"}
              value={`${formatNumber(control?.readiness_score, 1)} / ${control?.readiness_status ?? "-"}`}
            />
            <PolicyRow
              label="Connector"
              tone={control?.evidence?.live_submission_enabled ? "emerald" : "amber"}
              value={control?.connector_status ?? "-"}
            />
            <PolicyRow
              label="Primary market"
              tone={control?.primary_market ? "blue" : "slate"}
              value={control?.primary_market?.market_name ?? "-"}
            />
          </div>
        </SectionCard>

        <SectionCard title="Automation evidence">
          <DataTable
            columns={["evidence", "record", "status"]}
            rows={[
              {
                evidence: "Policy",
                record: control?.evidence?.automation_policy_id ?? "-",
                status: control?.evidence?.automation_policy_source ?? policy.data?.source,
              },
              {
                evidence: "Proposal",
                record: control?.evidence?.execution_proposal_id ?? "-",
                status: control?.evidence?.execution_proposal_id ? "available" : "missing",
              },
              {
                evidence: "Paper trade",
                record: control?.evidence?.paper_trade_id ?? "-",
                status: control?.paper_trading_allowed ? "allowed" : "required",
              },
              {
                evidence: "Approval gate",
                record: control?.evidence?.approval_id ?? "-",
                status: humanGate.status ?? "-",
              },
              {
                evidence: "Submission",
                record: control?.evidence?.market_submission_id ?? "-",
                status: control?.live_trading_allowed ? "live allowed" : "not live",
              },
            ]}
          />
        </SectionCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.75fr)]">
        <SectionCard
          action={
            <ActionButton
              endpoint={`/assets/${selectedAssetId}/execution/automation-policy/default`}
              label="Save supervised baseline"
              refetch={refetchPolicy}
              variant="primary"
            />
          }
          title="Automation control envelope"
        >
          <div className="grid gap-3 md:grid-cols-2">
            <PolicyRow
              label="Policy version"
              tone="blue"
              value={currentPolicy?.policy_version ?? "-"}
            />
            <PolicyRow
              label="Updated"
              tone="slate"
              value={formatDateTime(currentPolicy?.updated_at)}
            />
            <PolicyRow
              label="Human gate"
              tone={approvalPolicy.require_human_approval ? "blue" : "amber"}
              value={approvalPolicy.require_human_approval ? "required" : "not required"}
            />
            <PolicyRow
              label="Paper validation"
              tone={simulationPolicy.require_paper_trade ? "blue" : "amber"}
              value={simulationPolicy.require_paper_trade ? "required" : "optional"}
            />
            <PolicyRow
              label="Fallback mode"
              tone="amber"
              value={fallbackPolicy.mode ?? "-"}
            />
            <PolicyRow
              label="Policy source"
              tone={policy.data?.source === "database" ? "emerald" : "slate"}
              value={policy.data?.source ?? "-"}
            />
          </div>
        </SectionCard>

        <SectionCard title="Automated trading workflow">
          <div className="space-y-3">
            <WorkflowLink
              href="/market-signals"
              label="Ingest market signals"
              value="Automated trigger source"
            />
            <WorkflowLink
              href="/execution/market-allocation"
              label="Select market route"
              value="Policy-filtered allocation"
            />
            <WorkflowLink
              href="/execution/risk-approval"
              label="Evaluate automation gates"
              value={policyDecision ?? "Policy not evaluated"}
            />
            <WorkflowLink
              href="/execution/simulation"
              label="Run automatic paper market"
              value={simulationPolicy.require_paper_trade ? "Required" : "Optional"}
            />
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Risk and confidence thresholds">
          <DataTable
            columns={["policy_area", "limit", "value", "automation_effect"]}
            rows={[
              {
                automation_effect: "Blocks expected-loss breach",
                limit: "Max daily loss",
                policy_area: "Risk",
                value: formatCurrency(riskLimits.max_daily_loss_eur),
              },
              {
                automation_effect: "Blocks oversized bids",
                limit: "Max order power",
                policy_area: "Risk",
                value: `${formatNumber(riskLimits.max_order_power_mw, 2)} MW`,
              },
              {
                automation_effect: "Caps asset wear in automated strategies",
                limit: "Max cycles per day",
                policy_area: "Risk",
                value: formatNumber(riskLimits.max_cycles_per_day, 2),
              },
              {
                automation_effect: "Requires human review below threshold",
                limit: "Min confidence score",
                policy_area: "Forecast",
                value: `${formatNumber(confidencePolicy.min_confidence_score, 0)}/100`,
              },
              {
                automation_effect: "Routes medium/low evidence to safer modes",
                limit: "Min confidence band",
                policy_area: "Forecast",
                value: confidencePolicy.min_confidence_band ?? "-",
              },
              {
                automation_effect: "Requires second review for large tickets",
                limit: "Four eyes above",
                policy_area: "Approval",
                value: `${formatNumber(approvalPolicy.four_eyes_required_above_power_mw, 2)} MW`,
              },
            ]}
          />
        </SectionCard>

        <SectionCard title="Allowed German market routes">
          <DataTable
            columns={["adapter_id", "role", "automation_scope", "policy_status"]}
            rows={formatMarketRoles(currentPolicy)}
          />
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={decisionTone(policyDecision)}>{policyDecision ?? "-"}</StatusPill>}
          title="Policy exceptions"
        >
          <DataTable
            columns={["check", "status", "message", "context"]}
            rows={formatChecks(criticalCheckRows.length ? criticalCheckRows : checks.slice(0, 6))}
          />
        </SectionCard>

        <SectionCard title="Automation blockers and next action">
          <DataTable
            columns={["source", "key", "status", "message"]}
            rows={
              blockerRows.length
                ? blockerRows
                : [
                    {
                      key: nextAutomationAction.action ?? "-",
                      message: nextAutomationAction.message ?? "No automation blocker reported.",
                      source: nextAutomationAction.owner ?? "automation_control",
                      status: "next",
                    },
                  ]
            }
          />
        </SectionCard>
      </div>

      <div className="mt-5">
        <SectionCard title="Policy history">
          <DataTable
            columns={[
              "automation_policy_id",
              "updated_at",
              "policy_version",
              "automation_mode",
              "max_daily_loss_eur",
              "max_order_power_mw",
              "min_confidence_score",
              "fallback_mode",
            ]}
            rows={formatHistory(history.data?.policies ?? []).slice(0, 6)}
          />
        </SectionCard>
      </div>
    </>
  );
}

function PolicyRow({
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

function formatMarketRoles(policy?: AutomationPolicy) {
  const allowed = new Set(policy?.allowed_markets ?? []);

  return (policy?.market_roles ?? []).map((row) => ({
    ...row,
    policy_status: allowed.has(String(row.adapter_id)) ? "allowed" : "disabled",
  }));
}

function formatChecks(rows: NonNullable<AutomationPolicyEvaluationResponse["checks"]>) {
  return rows.map((row) => ({
    ...row,
    context: compactContext(row.context),
  }));
}

function formatHistory(rows: TableRow[]) {
  return rows.map((row) => ({
    ...row,
    max_daily_loss_eur: formatCurrency(row.max_daily_loss_eur),
    max_order_power_mw: formatNumber(row.max_order_power_mw, 2),
    min_confidence_score: formatNumber(row.min_confidence_score, 0),
    updated_at: formatDateTime(row.updated_at),
  }));
}

function compactContext(context: JsonValue | undefined) {
  if (!context || typeof context !== "object" || Array.isArray(context)) {
    return "-";
  }

  return Object.entries(context)
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join(" | ");
}

function controlModeTone(value: unknown) {
  if (value === "live_auto_limited" || value === "supervised_auto") {
    return "emerald";
  }

  if (value === "paper_trading") {
    return "blue";
  }

  if (value === "live_auto_blocked") {
    return "red";
  }

  return "slate";
}

function humanGateTone(value: unknown) {
  if (value === "passed" || value === "not_required") {
    return "emerald";
  }

  if (value === "pending" || value === "required") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function decisionTone(value: unknown) {
  if (value === "supervised_live_candidate" || value === "paper_ready") {
    return "emerald";
  }

  if (value === "human_approval_required" || value === "paper_only") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}
