import Link from "next/link";

import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatNumber } from "@/lib/format";
import type { AssetCockpitResponse } from "@/types/api";

export function EngineCard({
  href,
  label,
  status,
  title,
  value,
}: {
  href: string;
  label: string;
  status: string;
  title: string;
  value: string;
}) {
  return (
    <Link
      className="group rounded-lg border border-sky-500/20 bg-slate-950/60 p-5 transition hover:border-sky-400/50 hover:bg-sky-950/20"
      href={href}
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-300">
            {label}
          </div>
          <h2 className="mt-2 text-lg font-semibold text-white">{title}</h2>
        </div>
        <StatusPill tone="blue">Open</StatusPill>
      </div>
      <div className="rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2">
        <div className="text-xs text-slate-500">Current state</div>
        <div className="mt-1 text-base font-semibold text-slate-100">{value}</div>
        <div className="mt-1 text-xs text-slate-400">{status}</div>
      </div>
    </Link>
  );
}

export function EnterpriseMaturityPanel({
  enterpriseMaturity,
}: {
  enterpriseMaturity: NonNullable<AssetCockpitResponse["cockpit"]>["enterprise_maturity"];
}) {
  return (
    <SectionCard
      action={
        <StatusPill tone={maturityTone(enterpriseMaturity?.score)}>
          {enterpriseMaturity?.display_level ?? "Maturity pending"}
        </StatusPill>
      }
      title="Enterprise maturity and competitive edge"
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={maturityTone(enterpriseMaturity?.score)}
          helper="Enterprise operating readiness"
          label="Maturity score"
          value={`${formatNumber(enterpriseMaturity?.score, 1)}/100`}
        />
        <KpiCard
          accent="emerald"
          helper="Linked backend proof points"
          label="Bankability evidence"
          value={enterpriseMaturity?.bankability_evidence_count ?? 0}
        />
        <KpiCard
          accent={enterpriseMaturity?.automation_readiness === "blocked" ? "amber" : "blue"}
          helper="Connectivity, telemetry, approval, and guardrails"
          label="Automation readiness"
          value={enterpriseMaturity?.automation_readiness ?? "-"}
        />
        <KpiCard
          accent="emerald"
          helper="Evidence-led differentiation"
          label="Competitive score"
          value={`${formatNumber(enterpriseMaturity?.differentiation_score, 1)}/100`}
        />
      </div>
    </SectionCard>
  );
}

export function StatusRow({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "amber" | "blue" | "emerald" | "red" | "slate";
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3">
      <span className="text-sm text-slate-300">{label}</span>
      <StatusPill tone={tone}>{value}</StatusPill>
    </div>
  );
}

export function EvidenceList({
  items,
  tone,
}: {
  items?: string[];
  tone: "amber" | "blue" | "emerald";
}) {
  return items?.length ? (
    <ul className="space-y-2 text-sm leading-6 text-slate-300">
      {items.map((item) => (
        <li key={item} className="flex gap-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-300" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  ) : (
    <StatusPill tone={tone}>No actions</StatusPill>
  );
}

function maturityTone(score?: number) {
  if ((score ?? 0) >= 80) {
    return "emerald";
  }

  if ((score ?? 0) >= 55) {
    return "blue";
  }

  return "amber";
}
