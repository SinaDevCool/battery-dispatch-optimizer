"use client";

import { Activity, Bot, Clock, Globe2, ShieldCheck } from "lucide-react";

import { ActionButton } from "@/components/action-button";
import { AssetSelector } from "@/components/asset-selector";
import { StatusPill } from "@/components/status-pill";
import { formatDateTime } from "@/lib/format";
import type { Asset, SignalMetadata, SignalSummary } from "@/types/api";

export function CommandCenterHeader({
  asset,
  assetId,
  healthStatus,
  metadata,
  onRun,
  summary,
}: {
  asset?: Asset;
  assetId: string;
  healthStatus?: string;
  metadata: SignalMetadata;
  onRun: () => Promise<unknown>;
  summary: SignalSummary;
}) {
  const market = asset?.market ?? "DE-LU day-ahead";
  const country = asset?.country ?? "Germany";
  const signal = String(summary.signal ?? "No signal");

  return (
    <section className="mb-6 overflow-hidden rounded-lg border border-slate-800 bg-slate-950 shadow-sm shadow-black/20">
      <div className="border-b border-slate-800 bg-slate-900/55 px-5 py-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusPill tone="blue">Value cockpit</StatusPill>
              <StatusPill tone={healthStatus === "ok" ? "emerald" : "amber"}>
                API {healthStatus ?? "checking"}
              </StatusPill>
              <StatusPill tone="slate">Fail-closed automation</StatusPill>
            </div>
            <h1 className="mt-4 text-2xl font-semibold tracking-tight text-white md:text-3xl">
              Battery value control room
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              One place to see owner value, trade confidence, evidence quality,
              and the blockers that prevent safe automated execution.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <AssetSelector />
            <ActionButton
              endpoint="/workflow/run-daily"
              label="Run optimization"
              refetch={onRun}
              variant="primary"
            />
          </div>
        </div>
      </div>

      <div className="grid gap-px bg-slate-800 md:grid-cols-2 xl:grid-cols-5">
        <HeaderCell
          icon={<Activity className="h-4 w-4" />}
          label="Asset"
          value={asset?.asset_name ?? asset?.site_name ?? assetId}
        />
        <HeaderCell
          icon={<Globe2 className="h-4 w-4" />}
          label="Market"
          value={`${country} / ${market}`}
        />
        <HeaderCell
          icon={<Bot className="h-4 w-4" />}
          label="Trading mode"
          value="Advisory simulation"
        />
        <HeaderCell
          icon={<Clock className="h-4 w-4" />}
          label="Last optimization"
          value={formatDateTime(metadata.generated_at)}
        />
        <HeaderCell
          icon={<ShieldCheck className="h-4 w-4" />}
          label="Signal state"
          value={signal}
        />
      </div>

    </section>
  );
}

function HeaderCell({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="bg-slate-950 px-5 py-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
        <span className="text-sky-300">{icon}</span>
        {label}
      </div>
      <div className="mt-2 truncate text-sm font-semibold text-slate-100">
        {value}
      </div>
    </div>
  );
}
