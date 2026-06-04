"use client";

import { Cable, CirclePause, LockKeyhole, ShieldCheck, UserCheck } from "lucide-react";

import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type { ExecutionReadinessResponse } from "@/types/api";

export function TradingReadinessPanel({
  readiness,
}: {
  readiness?: ExecutionReadinessResponse;
}) {
  const checks = readiness?.checks ?? [];
  const summary = readiness?.summary ?? {};

  return (
    <SectionCard
      action={
        <StatusPill tone={readinessTone(readiness?.readiness_status)}>
          {readiness?.readiness_status ?? "not evaluated"}
        </StatusPill>
      }
      title="Trading readiness"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <ReadinessMetric label="Score" value={`${readiness?.readiness_score ?? 0}/100`} />
        <ReadinessMetric label="Passed" value={summary.passed ?? 0} />
        <ReadinessMetric label="Review" value={summary.review ?? 0} />
        <ReadinessMetric label="Blocked" value={summary.blocked ?? 0} />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {checks.length ? (
          checks.map((check) => (
            <ReadinessItem
              icon={iconForCheck(check.check)}
              key={check.check}
              label={check.label ?? check.check ?? "Readiness check"}
              tone={checkTone(check.status)}
              value={check.status ?? "-"}
            />
          ))
        ) : (
          <ReadinessItem
            icon={<CirclePause className="h-4 w-4" />}
            label="Execution readiness"
            tone="amber"
            value="Not evaluated"
          />
        )}
      </div>

      <div className="mt-4 rounded-lg border border-sky-400/20 bg-sky-400/10 p-4 text-sm leading-6 text-sky-100">
        {readiness?.recommended_actions?.[0] ??
          "Evaluate readiness before moving from advisory mode into supervised execution."}
      </div>
    </SectionCard>
  );
}

function ReadinessMetric({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function ReadinessItem({
  icon,
  label,
  tone,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  tone: "amber" | "blue" | "emerald" | "red" | "slate";
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        <span className="text-slate-400">{icon}</span>
        {label}
      </div>
      <div className="mt-3">
        <StatusPill tone={tone}>{value}</StatusPill>
      </div>
    </div>
  );
}

function iconForCheck(check?: string) {
  if (check === "market_adapter") {
    return <Cable className="h-4 w-4" />;
  }

  if (check === "operator_approval") {
    return <UserCheck className="h-4 w-4" />;
  }

  if (check === "automation_guardrails") {
    return <LockKeyhole className="h-4 w-4" />;
  }

  return <ShieldCheck className="h-4 w-4" />;
}

function checkTone(status?: string) {
  if (status === "passed") {
    return "emerald";
  }

  if (status === "review") {
    return "blue";
  }

  if (status === "blocked") {
    return "red";
  }

  return "slate";
}

function readinessTone(status?: string) {
  if (status === "supervised_ready") {
    return "emerald";
  }

  if (status === "operator_review_required") {
    return "blue";
  }

  if (status === "blocked") {
    return "red";
  }

  return "slate";
}
