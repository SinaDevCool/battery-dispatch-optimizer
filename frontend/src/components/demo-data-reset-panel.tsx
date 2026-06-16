"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  DatabaseZap,
  FileText,
  Loader2,
  RefreshCw,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { InvestorDemoSeedResponse } from "@/types/api";

type SeedScope = "selected" | "all";

const statusTone = {
  error: "red",
  ok: "emerald",
  partial: "amber",
} as const;

export function DemoDataResetPanel({
  className,
  variant = "full",
}: {
  className?: string;
  variant?: "compact" | "full";
}) {
  const queryClient = useQueryClient();
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const [lastScope, setLastScope] = useState<SeedScope | null>(null);

  const selectedAssetLabel =
    selectedAsset?.asset_name ??
    selectedAsset?.site_name ??
    selectedAsset?.asset_id ??
    selectedAssetId;
  const isProductionAsset = selectedAsset?.data_mode === "production";

  const seedMutation = useMutation({
    mutationFn: (scope: SeedScope) => {
      const endpoint =
        scope === "selected"
          ? `/demo/investor-seed?asset_id=${encodeURIComponent(selectedAssetId)}`
          : "/demo/investor-seed";

      return apiPost<InvestorDemoSeedResponse>(endpoint);
    },
    onMutate: (scope) => {
      setLastScope(scope);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  const response = seedMutation.data;
  const responseTone = getResponseTone(response);
  const seededAssets = useMemo(
    () =>
      (response?.assets ?? [])
        .map((asset) => asset.asset_id)
        .filter(Boolean)
        .join(", "),
    [response],
  );

  return (
    <SectionCard
      action={<StatusPill tone="blue">Mock data only</StatusPill>}
      className={className}
      title={variant === "compact" ? "Demo ready control" : "Investor demo data reset"}
    >
      {variant === "compact" ? (
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-md border border-sky-400/30 bg-sky-400/10 p-2 text-sky-200">
              <DatabaseZap className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-slate-100">
                Refresh the selected investor demo
              </div>
              <p className="mt-1 text-sm leading-6 text-slate-400">
                Rebuilds mock forecasts, revenue, execution, settlement, and
                reports for the selected asset before a live walkthrough.
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <DemoSeedMetric label="Asset" value={String(selectedAssetLabel)} />
            <DemoSeedMetric
              label="Mode"
              value={selectedAsset?.data_mode ?? "mock"}
            />
            <DemoSeedMetric
              label="Last reset"
              value={response?.generated_at ?? "Not run here"}
            />
          </div>

          {isProductionAsset ? (
            <div className="rounded-md border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs leading-5 text-amber-100">
              Selected asset is marked as production. Switch to a mock asset
              before resetting selected demo data.
            </div>
          ) : null}

          {response ? (
            <>
              <SeedResponseMessage
                response={response}
                responseTone={responseTone}
                seededAssets={seededAssets}
              />
              <DemoJourneyActions />
            </>
          ) : null}

          {seedMutation.error ? (
            <SeedErrorMessage error={seedMutation.error} />
          ) : null}

          <div className="grid gap-2 sm:grid-cols-2">
            <SeedButton
              disabled={seedMutation.isPending || isProductionAsset}
              isPending={seedMutation.isPending && lastScope === "selected"}
              label="Reset selected"
              onClick={() => seedMutation.mutate("selected")}
              variant="primary"
            />
            <SeedButton
              disabled={seedMutation.isPending}
              isPending={seedMutation.isPending && lastScope === "all"}
              label="Reset all mock"
              onClick={() => seedMutation.mutate("all")}
            />
          </div>
        </div>
      ) : (
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-md border border-sky-400/30 bg-sky-400/10 p-2 text-sky-200">
              <DatabaseZap className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-slate-100">
                Reset generated mock evidence for investor demos
              </div>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-400">
                Rebuilds forecasts, signals, revenue, execution, settlement,
                telemetry, and reports from local mock sources without touching
                production connectors.
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <DemoSeedMetric label="Selected asset" value={String(selectedAssetLabel)} />
            <DemoSeedMetric
              label="Data mode"
              value={selectedAsset?.data_mode ?? "mock"}
            />
            <DemoSeedMetric
              label="Last run"
              value={response?.generated_at ?? "Not run in this session"}
            />
          </div>

          {isProductionAsset ? (
            <div className="rounded-md border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs leading-5 text-amber-100">
              Selected asset is marked as production. Use all mock assets or
              switch to a mock asset before running a selected-asset demo reset.
            </div>
          ) : null}

          {response ? (
            <>
              <SeedResponseMessage
                response={response}
                responseTone={responseTone}
                seededAssets={seededAssets}
              />
              <DemoJourneyActions />
            </>
          ) : null}

          {seedMutation.error ? (
            <SeedErrorMessage error={seedMutation.error} />
          ) : null}
        </div>

        <div className="flex flex-col gap-2 sm:flex-row lg:w-56 lg:flex-col">
          <SeedButton
            disabled={seedMutation.isPending || isProductionAsset}
            isPending={seedMutation.isPending && lastScope === "selected"}
            label="Reset selected asset"
            onClick={() => seedMutation.mutate("selected")}
            variant="primary"
          />
          <SeedButton
            disabled={seedMutation.isPending}
            isPending={seedMutation.isPending && lastScope === "all"}
            label="Reset all mock assets"
            onClick={() => seedMutation.mutate("all")}
          />
        </div>
      </div>
      )}
    </SectionCard>
  );
}

function DemoSeedMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-h-20 rounded-lg border border-slate-800 bg-slate-900/55 p-3">
      <div className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 break-words text-sm font-semibold text-slate-100">
        {value}
      </div>
    </div>
  );
}

function SeedButton({
  disabled,
  isPending,
  label,
  onClick,
  variant = "secondary",
}: {
  disabled?: boolean;
  isPending?: boolean;
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary";
}) {
  return (
    <button
      className={cn(
        "inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border px-3 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary"
          ? "border-emerald-400/35 bg-emerald-400/15 text-emerald-100 hover:bg-emerald-400/25"
          : "border-sky-400/30 bg-sky-400/10 text-sky-100 hover:bg-sky-400/20",
      )}
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {isPending ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : variant === "primary" ? (
        <CheckCircle2 className="h-3.5 w-3.5" />
      ) : (
        <RefreshCw className="h-3.5 w-3.5" />
      )}
      {isPending ? "Resetting..." : label}
    </button>
  );
}

function SeedResponseMessage({
  response,
  responseTone,
  seededAssets,
}: {
  response: InvestorDemoSeedResponse;
  responseTone: "amber" | "emerald" | "red";
  seededAssets: string;
}) {
  return (
    <div
      className={cn(
        "rounded-md border px-3 py-2 text-xs leading-5",
        responseTone === "emerald" &&
          "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
        responseTone === "amber" &&
          "border-amber-400/30 bg-amber-400/10 text-amber-100",
        responseTone === "red" &&
          "border-red-400/30 bg-red-400/10 text-red-100",
      )}
    >
      {response.message ?? `Seed finished with status ${response.status}.`}
      {seededAssets ? ` Assets: ${seededAssets}.` : ""}
    </div>
  );
}

function SeedErrorMessage({ error }: { error: unknown }) {
  return (
    <div className="rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs leading-5 text-red-100">
      {error instanceof Error ? error.message : "Could not reset demo data."}
    </div>
  );
}

function DemoJourneyActions() {
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      <DemoJourneyLink
        href="/revenue"
        icon={<WalletCards className="h-3.5 w-3.5" />}
        label="Revenue"
      />
      <DemoJourneyLink
        href="/execution"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        label="Execution"
      />
      <DemoJourneyLink
        href="/reports"
        icon={<FileText className="h-3.5 w-3.5" />}
        label="Reports"
      />
    </div>
  );
}

function DemoJourneyLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <Link
      className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-700 bg-slate-900/80 px-3 text-xs font-semibold text-slate-100 transition hover:border-sky-400/40 hover:bg-sky-400/10 hover:text-sky-100"
      href={href}
    >
      {icon}
      {label}
      <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
    </Link>
  );
}

function getResponseTone(response?: InvestorDemoSeedResponse) {
  if (!response) {
    return "emerald";
  }

  return statusTone[response.status as keyof typeof statusTone] ?? "amber";
}
