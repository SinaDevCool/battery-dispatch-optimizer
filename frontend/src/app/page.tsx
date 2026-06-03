"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DispatchChart } from "@/components/charts/dispatch-chart";
import { CommandCenterHeader } from "@/components/cockpit/command-center-header";
import { DecisionSummary } from "@/components/cockpit/decision-summary";
import { RevenueStackOverview } from "@/components/cockpit/revenue-stack-overview";
import { RiskCompliancePanel } from "@/components/cockpit/risk-compliance-panel";
import { StrategyRecommendation } from "@/components/cockpit/strategy-recommendation";
import { TradingReadinessPanel } from "@/components/cockpit/trading-readiness-panel";
import { DataCompletenessPanel } from "@/components/data-completeness-panel";
import { DataTable } from "@/components/data-table";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  AncillaryEligibilityResponse,
  AssetCockpitResponse,
  BusinessDecisionResponse,
  DataCompletenessResponse,
  DatabaseStatusResponse,
  EegComplianceResponse,
  HealthResponse,
  HedgingRevenueResponse,
  LatestSignalResponse,
  RevenueStackResponse,
  StorageClassificationResponse,
  WorkflowRunResponse,
} from "@/types/api";

export default function OverviewPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();

  const health = useQuery({
    queryFn: () => apiGet<HealthResponse>("/health"),
    queryKey: ["health"],
  });

  const databaseStatus = useQuery({
    queryFn: () => apiGet<DatabaseStatusResponse>("/database/status"),
    queryKey: ["database-status"],
  });

  const cockpit = useQuery({
    queryFn: () =>
      apiGet<AssetCockpitResponse>(`/assets/${selectedAssetId}/cockpit`),
    queryKey: ["asset-cockpit", selectedAssetId],
  });

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["asset-signal-latest", selectedAssetId],
  });

  const revenue = useQuery({
    queryFn: () =>
      apiGet<RevenueStackResponse>(
        `/assets/${selectedAssetId}/revenue-stack/latest`,
      ),
    queryKey: ["revenue-stack-latest", selectedAssetId],
  });

  const hedging = useQuery({
    queryFn: () =>
      apiGet<HedgingRevenueResponse>(
        `/assets/${selectedAssetId}/hedging/revenue`,
      ),
    queryKey: ["overview-hedging", selectedAssetId],
  });

  const eeg = useQuery({
    queryFn: () =>
      apiGet<EegComplianceResponse>(
        `/assets/${selectedAssetId}/eeg-compliance/latest`,
      ),
    queryKey: ["overview-eeg-compliance", selectedAssetId],
  });

  const classification = useQuery({
    queryFn: () =>
      apiGet<StorageClassificationResponse>(
        `/assets/${selectedAssetId}/storage-classification`,
      ),
    queryKey: ["overview-storage-classification", selectedAssetId],
  });

  const ancillary = useQuery({
    queryFn: () =>
      apiGet<AncillaryEligibilityResponse>(
        `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
      ),
    queryKey: ["overview-ancillary", selectedAssetId],
  });

  const businessDecision = useQuery({
    queryFn: () =>
      apiGet<BusinessDecisionResponse>(
        `/assets/${selectedAssetId}/business-decision/latest`,
      ),
    queryKey: ["overview-business-decision", selectedAssetId],
  });

  const workflowRun = useQuery({
    queryFn: () =>
      apiGet<WorkflowRunResponse>(
        `/assets/${selectedAssetId}/workflow-runs/latest`,
      ),
    queryKey: ["overview-workflow-run", selectedAssetId],
  });

  const completeness = useQuery({
    queryFn: () =>
      apiGet<DataCompletenessResponse>(
        `/assets/${selectedAssetId}/data-completeness`,
      ),
    queryKey: ["overview-data-completeness", selectedAssetId],
  });

  const cockpitData = cockpit.data?.cockpit;
  const signalPayload = cockpitData?.latest_signal ?? signal.data;
  const revenuePayload = cockpitData?.revenue_stack ?? revenue.data;
  const businessDecisionPayload =
    cockpitData?.business_decision ?? businessDecision.data;
  const workflowRunPayload = cockpitData?.workflow_run
    ? { status: "ok", workflow_run: cockpitData.workflow_run }
    : workflowRun.data;
  const completenessPayload = cockpitData?.data_completeness ?? completeness.data;
  const enterpriseMaturity = cockpitData?.enterprise_maturity;
  const metadata = cockpitData?.signal_metadata ?? signalPayload?.data?.metadata ?? {};
  const summary = cockpitData?.signal_summary ?? signalPayload?.data?.summary ?? {};
  const dispatch = cockpitData?.dispatch ?? signalPayload?.data?.dispatch ?? [];
  const revenueRows = cockpitData?.revenue_products?.length
    ? cockpitData.revenue_products
    : revenuePayload?.results?.length
      ? revenuePayload.results
      : revenuePayload?.products ?? [];
  const hedgeSummary = hedging.data?.summary ?? {};
  const activeDispatchRows = dispatch.filter((row) => row.action !== "idle");
  const totalRevenue =
    cockpitData?.business_kpis?.modelled_revenue_eur ??
    revenueRows.reduce(
      (sum, row) =>
        sum +
        Number(
          row.estimated_revenue_eur ??
            row.revenue_eur ??
            row.total_revenue_eur ??
            0,
        ),
      0,
    );
  const isBackendDown = Boolean(health.error);

  const refetchCockpit = () =>
    Promise.all([
      health.refetch(),
      databaseStatus.refetch(),
      cockpit.refetch(),
      signal.refetch(),
      revenue.refetch(),
      hedging.refetch(),
      eeg.refetch(),
      classification.refetch(),
      ancillary.refetch(),
      businessDecision.refetch(),
      workflowRun.refetch(),
      completeness.refetch(),
    ]);

  return (
    <>
      <CommandCenterHeader
        asset={selectedAsset}
        assetId={selectedAssetId}
        healthStatus={health.data?.status}
        metadata={metadata}
        onRun={refetchCockpit}
        summary={summary}
      />

      {isBackendDown ? (
        <div className="mb-6">
          <ErrorState message="The FastAPI backend is not reachable. Start it with: python -m uvicorn src.api.main:app --reload --port 8000" />
        </div>
      ) : null}

      <div className="mb-6 flex flex-wrap gap-3">
        <ActionButton
          endpoint={`/demo/portfolio/run?asset_id=${selectedAssetId}`}
          label="Populate full demo evidence"
          refetch={refetchCockpit}
          variant="primary"
        />
        <ActionButton
          endpoint={`/assets/${selectedAssetId}/workflow-runs/run`}
          label="Run audited workflow"
          refetch={refetchCockpit}
          variant="secondary"
        />
      </div>

      <div className="mb-6 grid gap-4 xl:grid-cols-3">
        <EngineCard
          href="/forecasts"
          label="AI Forecast Engine"
          status={displayValue(
            metadata.forecast_model ?? metadata.forecast_provider,
            "Forecast source pending",
          )}
          title="Forecast trading desk"
          value={displayValue(
            metadata.forecast_provider ?? metadata.source,
            "No active forecast",
          )}
          bullets={[
            "Day-ahead forecast comparison",
            "Forecast quality and provider ranking",
            "Actual-vs-forecast PnL evidence",
          ]}
        />
        <EngineCard
          href="/revenue"
          label="Multi-Market Optimization"
          status={`${activeDispatchRows.length} active dispatch interval(s)`}
          title="Revenue and constraint optimizer"
          value={formatCurrency(totalRevenue)}
          bullets={[
            "Day-ahead dispatch economics",
            "Grid fee, degradation, and regulation checks",
            "Merchant, ancillary, and hedged revenue view",
          ]}
        />
        <EngineCard
          href="/execution"
          label="Automated Execution Engine"
          status={displayValue(
            businessDecisionPayload?.decision?.recommendation_status ??
              workflowRunPayload?.workflow_run?.status,
            "Execution evidence pending",
          )}
          title="Guardrailed trading control"
          value={displayValue(
            businessDecisionPayload?.decision?.readiness ??
              businessDecisionPayload?.decision?.recommendation,
            "Advisory mode",
          )}
          bullets={[
            "Draft orders and human approval",
            "Paper trading before live submission",
            "Risk gates before automated trading",
          ]}
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={summary.signal === "ACTION" ? "emerald" : "slate"}
          label="Latest signal"
          value={String(summary.signal ?? "-")}
          helper={String(summary.opportunity_level ?? "No opportunity level")}
        />
        <KpiCard
          accent="emerald"
          label="Expected PnL"
          value={formatCurrency(summary.total_pnl_eur)}
          helper={`${formatNumber(summary.profit_per_mw_day, 2)} EUR/MW-day`}
        />
        <KpiCard
          accent="blue"
          label="Revenue stack"
          value={formatCurrency(totalRevenue)}
          helper={`${revenueRows.length} market product(s) assessed`}
        />
        <KpiCard
          accent={eeg.data?.eeg_eligible ? "emerald" : "amber"}
          label="Regulatory readiness"
          value={eeg.data?.eeg_eligible ? "Eligible" : eeg.data?.status ?? "-"}
          helper={classification.data?.storage_classification ?? "Storage class pending"}
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent="blue"
          label="Database signal runs"
          value={databaseStatus.data?.table_counts?.signal_runs ?? 0}
          helper="Persisted optimization evidence"
        />
        <KpiCard
          accent="blue"
          label="Database revenue runs"
          value={databaseStatus.data?.table_counts?.revenue_stack_runs ?? 0}
          helper="Persisted revenue stack evidence"
        />
        <KpiCard
          accent="blue"
          label="Business decisions"
          value={databaseStatus.data?.table_counts?.business_decisions ?? 0}
          helper="Backend recommendation records"
        />
        <KpiCard
          accent="blue"
          label="Workflow runs"
          value={databaseStatus.data?.table_counts?.workflow_runs ?? 0}
          helper="Linked audit records"
        />
      </div>

      {enterpriseMaturity ? (
        <div className="mb-6">
          <SectionCard
            action={
              <StatusPill tone={maturityTone(enterpriseMaturity.score)}>
                {enterpriseMaturity.display_level ?? "Maturity pending"}
              </StatusPill>
            }
            title="Enterprise maturity and competitive edge"
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                accent={maturityTone(enterpriseMaturity.score)}
                helper="Enterprise-grade operating readiness"
                label="Maturity score"
                value={`${formatNumber(enterpriseMaturity.score, 1)}/100`}
              />
              <KpiCard
                accent="emerald"
                helper="Linked backend proof points"
                label="Bankability evidence"
                value={enterpriseMaturity.bankability_evidence_count ?? 0}
              />
              <KpiCard
                accent={enterpriseMaturity.automation_readiness === "blocked" ? "amber" : "blue"}
                helper="Market API, telemetry, approval, and guardrails"
                label="Automation readiness"
                value={enterpriseMaturity.automation_readiness ?? "-"}
              />
              <KpiCard
                accent="emerald"
                helper="Evidence-led differentiation score"
                label="Competitive differentiation"
                value={`${formatNumber(enterpriseMaturity.differentiation_score, 1)}/100`}
              />
            </div>

            <div className="mt-4 grid gap-4 xl:grid-cols-3">
              <EvidenceList
                items={enterpriseMaturity.strengths}
                title="What is already defensible"
                tone="emerald"
              />
              <EvidenceList
                items={enterpriseMaturity.gaps}
                title="What still blocks premium positioning"
                tone="amber"
              />
              <EvidenceList
                items={enterpriseMaturity.next_moat_actions}
                title="Next moat-building actions"
                tone="blue"
              />
            </div>

            {enterpriseMaturity.competitor_positioning ? (
              <div className="mt-4 rounded-lg border border-sky-500/25 bg-sky-500/10 px-4 py-3 text-sm text-sky-100">
                {enterpriseMaturity.competitor_positioning}
              </div>
            ) : null}
          </SectionCard>
        </div>
      ) : null}

      <div className="mb-6">
        <SectionCard
          action={
            <StatusPill tone={workflowRunPayload?.workflow_run ? "emerald" : "amber"}>
              {workflowRunPayload?.workflow_run ? "Audit linked" : "Audit pending"}
            </StatusPill>
          }
          title="Decision audit trail"
        >
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              accent="blue"
              label="Workflow run"
              value={workflowRunPayload?.workflow_run?.workflow_run_id ?? "-"}
              helper={workflowRunPayload?.workflow_run?.status ?? "No audit run yet"}
            />
            <KpiCard
              accent="blue"
              label="Forecast snapshot"
              value={workflowRunPayload?.workflow_run?.forecast_snapshot_id ?? "-"}
              helper={workflowRunPayload?.workflow_run?.forecast_provider ?? "-"}
            />
            <KpiCard
              accent="emerald"
              label="Linked signal"
              value={workflowRunPayload?.workflow_run?.signal_id ?? "-"}
              helper={workflowRunPayload?.workflow_run?.target_date ?? "-"}
            />
            <KpiCard
              accent="emerald"
              label="Linked decision"
              value={workflowRunPayload?.workflow_run?.decision_id ?? "-"}
              helper={
                workflowRunPayload?.workflow_run?.recommendation_status ??
                "Decision pending"
              }
            />
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <KpiCard
              accent="blue"
              label="Revenue stack run"
              value={workflowRunPayload?.workflow_run?.revenue_stack_id ?? "-"}
              helper="Commercial stack evidence"
            />
            <KpiCard
              accent="emerald"
              label="Audited PnL"
              value={formatCurrency(workflowRunPayload?.workflow_run?.expected_pnl_eur)}
              helper="Stored business decision result"
            />
            <KpiCard
              accent="blue"
              label="Optimizer"
              value={workflowRunPayload?.workflow_run?.optimizer_engine ?? "-"}
              helper={workflowRunPayload?.workflow_run?.completed_at ?? "-"}
            />
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(420px,0.85fr)]">
        <div className="space-y-5">
          <StrategyRecommendation
            ancillary={ancillary.data}
            businessDecision={businessDecisionPayload?.decision}
            eeg={eeg.data}
            hedgingSummary={hedgeSummary}
            metadata={metadata}
            revenueRows={revenueRows}
            summary={summary}
          />

          <DecisionSummary metadata={metadata} summary={summary} />

          <SectionCard
            action={
              <StatusPill tone={activeDispatchRows.length ? "emerald" : "slate"}>
                {activeDispatchRows.length} active intervals
              </StatusPill>
            }
            title="Optimization timeline"
          >
            {dispatch.length ? (
              <DispatchChart rows={dispatch} />
            ) : (
              <ErrorState message="No dispatch schedule is available yet. Run optimization to generate a signal." />
            )}
          </SectionCard>

          <DataCompletenessPanel
            data={completenessPayload}
            title="Decision evidence completeness"
          />
        </div>

        <div className="space-y-5">
          <RiskCompliancePanel
            ancillary={ancillary.data}
            classification={classification.data}
            eeg={eeg.data}
            signal={signalPayload}
          />
          <TradingReadinessPanel />
        </div>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(420px,0.9fr)_minmax(0,1.1fr)]">
        <RevenueStackOverview
          hedgingSummary={hedgeSummary}
          rows={revenueRows}
        />

        <SectionCard
          action={<StatusPill tone="blue">Audit preview</StatusPill>}
          title="Dispatch actions"
        >
          <DataTable
            columns={[
              "timestamp",
              "price",
              "action",
              "soc_mwh",
              "pnl_eur",
              "total_pnl_eur",
            ]}
            rows={(activeDispatchRows.length ? activeDispatchRows : dispatch).slice(
              0,
              12,
            )}
          />
        </SectionCard>
      </div>
    </>
  );
}

function EngineCard({
  bullets,
  href,
  label,
  status,
  title,
  value,
}: {
  bullets: string[];
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
      <div className="mb-4 rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2">
        <div className="text-xs text-slate-500">Current state</div>
        <div className="mt-1 text-base font-semibold text-slate-100">{value}</div>
        <div className="mt-1 text-xs text-slate-400">{status}</div>
      </div>
      <ul className="space-y-2 text-sm text-slate-300">
        {bullets.map((bullet) => (
          <li className="flex gap-2" key={bullet}>
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-300" />
            <span>{bullet}</span>
          </li>
        ))}
      </ul>
    </Link>
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

function displayValue(value: unknown, fallback: string) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  return fallback;
}

function EvidenceList({
  items,
  title,
  tone,
}: {
  items?: string[];
  title: string;
  tone: "amber" | "blue" | "emerald";
}) {
  const borderByTone = {
    amber: "border-amber-500/30 bg-amber-500/5",
    blue: "border-sky-500/30 bg-sky-500/5",
    emerald: "border-emerald-500/30 bg-emerald-500/5",
  };

  return (
    <div className={`rounded-lg border p-4 ${borderByTone[tone]}`}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
        <StatusPill tone={tone}>{items?.length ?? 0}</StatusPill>
      </div>
      {items?.length ? (
        <ul className="space-y-2 text-sm leading-6 text-slate-300">
          {items.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-300" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-400">No evidence recorded yet.</p>
      )}
    </div>
  );
}
