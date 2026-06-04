"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/format";
import type {
  AutomationPolicy,
  AutomationPolicyEvaluationResponse,
  AutomationPolicyHistoryResponse,
  AutomationPolicyResponse,
  JsonValue,
  TableRow,
} from "@/types/api";

export default function AutomationPoliciesPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();

  const policy = useQuery({
    queryFn: () =>
      apiGet<AutomationPolicyResponse>(
        `/assets/${selectedAssetId}/execution/automation-policy`,
      ),
    queryKey: ["automation-policy", selectedAssetId],
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
  const allowedMarkets = currentPolicy?.allowed_markets ?? [];

  const refetchPolicy = () =>
    Promise.all([policy.refetch(), evaluation.refetch(), history.refetch()]);

  return (
    <>
      <PageHeading
        description="Define the supervised automation envelope for each asset: allowed markets, confidence gates, risk limits, paper-trade requirements, approval rules, and fallback behavior."
        eyebrow="Trading operations"
        title="Automation policies"
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={automationTone(currentPolicy?.automation_mode)}
          helper={policy.data?.source === "default" ? "Generated baseline" : "Saved policy"}
          label="Automation mode"
          value={currentPolicy?.automation_mode ?? "-"}
        />
        <KpiCard
          accent={decisionTone(policyDecision)}
          helper={`${summary.blocked ?? 0} blocked / ${summary.review ?? 0} review`}
          label="Policy decision"
          value={policyDecision ?? "-"}
        />
        <KpiCard
          accent="blue"
          helper="Minimum score for supervised live candidate"
          label="Confidence gate"
          value={`${formatNumber(confidencePolicy.min_confidence_score, 0)}/100`}
        />
        <KpiCard
          accent="emerald"
          helper={selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId}
          label="Allowed markets"
          value={allowedMarkets.length}
        />
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
              label="Human approval"
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

        <SectionCard title="Next trading workflow">
          <div className="space-y-3">
            <WorkflowLink
              href="/market-signals"
              label="Watch market signals"
              value="Signal to automation decision"
            />
            <WorkflowLink
              href="/execution/market-allocation"
              label="Apply market allocation"
              value="Policy filters eligible routes"
            />
            <WorkflowLink
              href="/execution/risk-approval"
              label="Review guardrails"
              value={policyDecision ?? "Policy not evaluated"}
            />
            <WorkflowLink
              href="/execution/simulation"
              label="Run paper market"
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
          title="Policy evaluation"
        >
          <DataTable
            columns={["check", "status", "message", "context"]}
            rows={formatChecks(checks)}
          />
        </SectionCard>

        <SectionCard title="Recommended actions">
          <DataTable
            columns={["priority", "action"]}
            rows={(evaluation.data?.recommended_actions ?? []).map((action, index) => ({
              action,
              priority: index + 1,
            }))}
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
            rows={formatHistory(history.data?.policies ?? [])}
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

function automationTone(value: unknown) {
  if (value === "supervised_live") {
    return "emerald";
  }

  if (value === "paper_first") {
    return "blue";
  }

  if (value === "disabled") {
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
