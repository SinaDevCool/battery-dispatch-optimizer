"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, CircleAlert, CircleDashed } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataTable } from "@/components/data-table";
import { DemoDataResetPanel } from "@/components/demo-data-reset-panel";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { ProofCardGrid } from "@/components/proof-card-grid";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { useAssetContext } from "@/components/asset-provider";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatDemoStatus } from "@/lib/demo-status";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { ApiEnvelope, Asset, InvestorReadinessResponse, TableRow } from "@/types/api";

type Tone = "amber" | "blue" | "emerald" | "red" | "slate";
type ReadinessStatus = "ready" | "review" | "blocked";

type AssetReadiness = {
  asset: Asset;
  assetId: string;
  assetLabel: string;
  data: InvestorReadinessResponse;
  dataMode: string;
  openGapCount: number;
  overall: ReadinessStatus;
  row: TableRow;
  score: number;
};

const checkpointColumns = ["step", "status", "evidence", "next_action"];
const flowColumns = [
  "stop",
  "page",
  "investor_question",
  "proof_to_show",
  "status",
  "demo_action",
];
const diligenceColumns = [
  "diligence_area",
  "mock_evidence",
  "investor_meaning",
  "production_upgrade",
];
const sourceColumns = ["evidence_layer", "backend_route", "page", "what_investor_sees"];
const portfolioColumns = [
  "asset",
  "asset_type",
  "data_mode",
  "asset_identity",
  "physical_operation",
  "revenue_case",
  "execution_safety",
  "investor_proof",
  "investor_story",
  "next_gap",
  "score",
];

const investorDemoTabs = [
  {
    id: "story",
    label: "Story",
    helper: "Two-minute investor walkthrough and route through the product.",
  },
  {
    id: "proof",
    label: "Proof",
    helper: "Mock evidence, production boundary, diligence story, and source map.",
  },
  {
    id: "economics",
    label: "Economics",
    helper: "Project economics snapshot and mock finance assumptions.",
  },
  {
    id: "runbook",
    label: "Runbook",
    helper: "Evidence trail and operational checklist for demo delivery.",
  },
  {
    id: "portfolio",
    label: "Portfolio",
    helper: "Readiness comparison across all investor demo assets.",
  },
] as const;

type InvestorDemoTabId = (typeof investorDemoTabs)[number]["id"];

export default function InvestorDemoPage() {
  const { assets, isLoadingAssets, selectedAssetId } = useAssetContext();
  const [activeTab, setActiveTab] = useState<InvestorDemoTabId>("story");
  const assetIds = assets.map((asset) => asset.asset_id).join("|");

  const readinessQuery = useQuery({
    enabled: assets.length > 0,
    queryFn: async () => {
      const rows = await Promise.all(
        assets.map(async (asset) => {
          const data = await apiGet<InvestorReadinessResponse>(
            `/assets/${asset.asset_id}/investor-readiness`,
          );

          return normalizeAssetReadiness(asset, data);
        }),
      );

      return rows;
    },
    queryKey: ["investor-demo-readiness", assetIds],
  });

  const selectedEvidenceQuery = useQuery({
    enabled: Boolean(selectedAssetId),
    queryFn: async () => {
      const [
        signal,
        revenue,
        scenarios,
        stress,
        report,
        readiness,
      ] = await Promise.all([
        apiGet<ApiEnvelope>(`/assets/${selectedAssetId}/signal/latest`),
        apiGet<ApiEnvelope>(`/assets/${selectedAssetId}/revenue-summary`),
        apiGet<ApiEnvelope>(`/assets/${selectedAssetId}/scenarios/latest`),
        apiGet<ApiEnvelope>(`/assets/${selectedAssetId}/stress/latest`),
        apiGet<ApiEnvelope>(`/assets/${selectedAssetId}/client-evidence-summary`),
        apiGet<ApiEnvelope>(`/assets/${selectedAssetId}/investor-readiness`),
      ]);

      return {
        readiness,
        report,
        revenue,
        scenarios,
        signal,
        stress,
      };
    },
    queryKey: ["investor-demo-selected-evidence", selectedAssetId],
  });

  const readinessRows = readinessQuery.data ?? [];
  const selectedReadiness =
    readinessRows.find((row) => row.assetId === selectedAssetId) ?? readinessRows[0];
  const isLoading = isLoadingAssets || readinessQuery.isLoading;
  const portfolioScore = readinessRows.length
    ? Math.round(readinessRows.reduce((total, row) => total + row.score, 0) / readinessRows.length)
    : 0;
  const readyAssets = readinessRows.filter((row) => row.overall === "ready").length;
  const reviewAssets = readinessRows.filter((row) => row.overall === "review").length;
  const blockedAssets = readinessRows.filter((row) => row.overall === "blocked").length;
  const selectedStory = selectedReadiness?.data.story;
  const financeSummary = selectedReadiness?.data.finance_summary;
  const selectedRunbookRows = selectedReadiness
    ? (selectedReadiness.data.checkpoints ?? []).map((checkpoint, index) => ({
        evidence: checkpoint.evidence,
        next_action: checkpoint.next_action,
        step: `${index + 1}. ${checkpoint.label}`,
        status: checkpoint.status,
      }))
    : [];
  const readinessChecklistRows = buildDemoReadinessChecklist({
    asset: selectedReadiness?.asset,
    evidence: selectedEvidenceQuery.data,
    readiness: selectedReadiness?.data,
  });

  return (
    <main>
      <PageHeading
        description="Start here before a demo: choose an asset, confirm the evidence is fresh, then walk through the revenue story, downside proof, report package, and execution gates."
        eyebrow="Investor walkthrough"
        title="Investor Demo"
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={overallAccent(selectedReadiness?.overall)}
          helper={selectedReadiness?.assetLabel ?? "Waiting for asset data"}
          label="Selected asset"
          value={selectedReadiness?.assetId ?? "-"}
        />
        <KpiCard
          accent={scoreAccent(selectedReadiness?.score)}
          helper="Evidence score across asset, dispatch, revenue, execution, and reporting proof."
          label="Demo readiness"
          value={isLoading ? "Loading" : `${selectedReadiness?.score ?? 0}%`}
        />
        <KpiCard
          accent="blue"
          helper={`${readyAssets} ready / ${reviewAssets} review / ${blockedAssets} blocked`}
          label="Demo portfolio"
          value={isLoading ? "Loading" : `${portfolioScore}%`}
        />
        <KpiCard
          accent={selectedReadiness?.openGapCount ? "amber" : "emerald"}
          helper={selectedReadiness?.dataMode ?? "mock"}
          label="Open investor questions"
          value={selectedReadiness?.openGapCount ?? 0}
        />
      </div>

      <div className="grid gap-6">
        {selectedReadiness && selectedStory ? (
          <SectionCard
            action={
              <StatusPill tone={overallAccent(selectedReadiness.overall)}>
                {selectedReadiness.overall === "ready"
                  ? "Ready for investor demo"
                  : selectedReadiness.overall === "blocked"
                    ? "Blocked"
                    : "Needs review"}
              </StatusPill>
            }
            title="Investor opening story"
          >
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,0.45fr)]">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                  What to say first
                </div>
                <p className="mt-3 text-base leading-7 text-slate-100">
                  {selectedStory.demo_thesis}
                </p>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <NarrativeCallout label="Investor lens" value={selectedStory.investor_lens} />
                  <NarrativeCallout label="Risk framing" value={selectedStory.risk_frame} />
                </div>
              </div>
              <div className="rounded-lg border border-sky-400/20 bg-sky-400/5 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.14em] text-sky-300">
                  Why it is investable
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">
                  {selectedStory.production_upgrade}
                </p>
              </div>
            </div>
          </SectionCard>
        ) : null}

        <WorkspaceTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={investorDemoTabs}
        />

        {activeTab === "proof" ? (
          <>
            <DemoDataResetPanel variant="compact" />

            <SectionCard
              action={<StatusPill tone={checklistTone(readinessChecklistRows)}>Demo proof</StatusPill>}
              title="Investor proof checklist"
            >
              <p className="mb-4 text-sm leading-6 text-slate-400">
                Mock-ready / production gated means the demo evidence is complete enough for the
                product story, while live exchange, telemetry, settlement, and approval integrations
                remain separated until production onboarding.
              </p>
              <ProofCardGrid
                fields={[
                  { key: "what_it_proves", label: "What it proves" },
                  { key: "proof", label: "Demo evidence" },
                  { key: "production_next_step", label: "Production next step" },
                ]}
                rows={readinessChecklistRows}
                titleKey="demo_layer"
              />
            </SectionCard>
          </>
        ) : null}

        {activeTab === "economics" ? (
          <SectionCard
            action={<StatusPill tone="blue">Mock finance case</StatusPill>}
            title="Project economics snapshot"
          >
            <div className="mb-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                accent="blue"
                helper="Mock benchmark capex including contingency."
                label="Project cost"
                value={formatCurrency(financeSummary?.total_project_cost_eur)}
              />
              <KpiCard
                accent="emerald"
                helper="Demo-day modelled revenue annualized by mock operating days."
                label="Revenue run-rate"
                value={formatCurrency(financeSummary?.annual_revenue_run_rate_eur)}
              />
              <KpiCard
                accent={Number(financeSummary?.simple_payback_years ?? 0) > 12 ? "amber" : "emerald"}
                helper="Simple payback, not bank-grade IRR."
                label="Simple payback"
                value={
                  financeSummary?.simple_payback_years
                    ? `${formatNumber(financeSummary.simple_payback_years, 1)} years`
                    : "-"
                }
              />
              <KpiCard
                accent={Number(financeSummary?.downside_net_cashflow_eur ?? 0) > 0 ? "emerald" : "amber"}
                helper="After mock downside revenue haircut."
                label="Downside cashflow"
                value={formatCurrency(financeSummary?.downside_net_cashflow_eur)}
              />
            </div>
            <ProofCardGrid
              fields={[
                { key: "value", label: "Mock value" },
                { key: "investor_meaning", label: "Investor meaning" },
                { key: "production_upgrade", label: "Production proof needed" },
              ]}
              rows={selectedReadiness?.data.project_economics ?? []}
              titleKey="metric"
            />
          </SectionCard>
        ) : null}

        {activeTab === "story" ? (
          <>
            <SectionCard
              action={
                selectedReadiness ? (
                  <StatusPill tone={overallAccent(selectedReadiness.overall)}>
                    {selectedReadiness.overall}
                  </StatusPill>
                ) : null
              }
              title="Two-minute walkthrough"
            >
              {selectedReadiness ? (
                <div className="grid gap-3 lg:grid-cols-5">
                  {(selectedReadiness.data.checkpoints ?? []).map((checkpoint, index) => (
                    <Link
                      className="group flex min-h-44 flex-col justify-between rounded-lg border border-slate-800 bg-slate-900/60 p-4 transition hover:border-sky-500/50 hover:bg-slate-900"
                      href={checkpoint.route ?? "/investor-demo"}
                      key={checkpoint.id ?? `${selectedReadiness.assetId}-${index}`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                            Step {index + 1}
                          </span>
                          <CheckpointIcon tone={checkpointTone(checkpoint.tone)} />
                        </div>
                        <h2 className="mt-3 text-sm font-semibold leading-5 text-slate-100">
                          {checkpoint.label}
                        </h2>
                        <div className="mt-3">
                          <StatusPill tone={checkpointTone(checkpoint.tone)}>
                            {formatDemoStatus(checkpoint.status)}
                          </StatusPill>
                        </div>
                        <p className="mt-3 text-sm leading-5 text-slate-400">
                          {checkpoint.evidence}
                        </p>
                      </div>
                      <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-sky-300">
                        {checkpoint.next_action}
                        <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">Loading investor demo readiness.</p>
              )}
            </SectionCard>

            <SectionCard
              action={<StatusPill tone="blue">2-minute walkthrough</StatusPill>}
              title="Demo route"
            >
              <DataTable columns={flowColumns} rows={selectedReadiness?.data.demo_flow ?? []} />
            </SectionCard>
          </>
        ) : null}

        {activeTab === "proof" ? (
          <SectionCard
            action={
              <StatusPill tone={selectedReadiness?.dataMode === "production" ? "emerald" : "blue"}>
                {selectedReadiness?.dataMode ?? "mock"}
              </StatusPill>
            }
            title="Asset-specific diligence story"
          >
            <DataTable
              columns={diligenceColumns}
              rows={selectedStory?.diligence_rows ?? []}
            />
          </SectionCard>
        ) : null}

        {activeTab === "economics" ? (
          <SectionCard
            action={<StatusPill tone="blue">Assumption trace</StatusPill>}
            title="Mock finance assumptions"
          >
            <DataTable
              columns={["assumption", "mock_value", "investor_meaning", "production_upgrade"]}
              rows={selectedReadiness?.data.finance_assumptions ?? []}
            />
          </SectionCard>
        ) : null}

        {activeTab === "runbook" ? (
          <SectionCard title="Evidence trail">
            <DataTable columns={checkpointColumns} rows={selectedRunbookRows} />
          </SectionCard>
        ) : null}

        {activeTab === "runbook" ? (
          <SectionCard
            action={<StatusPill tone="blue">Source detail</StatusPill>}
            title="Technical source map"
          >
            <DataTable columns={sourceColumns} rows={selectedReadiness?.data.source_rows ?? []} />
          </SectionCard>
        ) : null}

        {activeTab === "portfolio" ? (
          <SectionCard
            action={
              readinessQuery.isError ? (
                <StatusPill tone="red">API error</StatusPill>
              ) : (
                <StatusPill tone="blue">{readinessRows.length} asset(s)</StatusPill>
              )
            }
            title="Portfolio demo view"
          >
            <DataTable columns={portfolioColumns} rows={readinessRows.map((row) => row.row)} />
          </SectionCard>
        ) : null}
      </div>
    </main>
  );
}

function normalizeAssetReadiness(
  asset: Asset,
  data: InvestorReadinessResponse,
): AssetReadiness {
  const summary = data.summary ?? {};
  const score = numberValue(summary.readiness_score) ?? 0;
  const overall = normalizeReadinessStatus(summary.readiness_status);

  return {
    asset,
    assetId: asset.asset_id,
    assetLabel: asset.asset_name ?? asset.site_name ?? asset.asset_id,
    data,
    dataMode: String(summary.data_mode ?? asset.data_mode ?? "mock"),
    openGapCount: numberValue(summary.open_gap_count) ?? 0,
    overall,
    row: data.portfolio_row ?? {
      asset: asset.asset_name ?? asset.site_name ?? asset.asset_id,
      asset_type: [asset.asset_type, asset.asset_subtype].filter(Boolean).join(" / "),
      data_mode: asset.data_mode ?? "mock",
      score,
    },
    score,
  };
}

function buildDemoReadinessChecklist({
  asset,
  evidence,
  readiness,
}: {
  asset?: Asset;
  evidence?: {
    readiness: ApiEnvelope;
    report: ApiEnvelope;
    revenue: ApiEnvelope;
    scenarios: ApiEnvelope;
    signal: ApiEnvelope;
    stress: ApiEnvelope;
  };
  readiness?: InvestorReadinessResponse;
}): TableRow[] {
  const signalSummary = nestedObject(evidence?.signal, "data")?.summary as TableRow | undefined;
  const revenueSummary = nestedObject(evidence?.revenue, "summary");
  const reportSummary = nestedObject(evidence?.report, "summary");
  const latestReport = nestedObject(evidence?.report, "latest_report");

  return [
    {
      demo_layer: "Mock data seeded",
      proof: `${asset?.data_profile?.label ?? asset?.data_source ?? "mock profile"} / ${asset?.forecast_file ?? "asset forecast"}`,
      production_next_step: "Replace local profiles with contracted forecast, exchange, meter, settlement, and connector feeds.",
      status: asset?.data_mode === "production" ? "production" : "mock_ready",
      what_it_proves: "The selected asset has a complete demo data package.",
    },
    {
      demo_layer: "Physical dispatch generated",
      proof: `${signalSummary?.signal ?? "-"} / ${signalSummary?.throughput_mwh ?? "-"} MWh throughput`,
      production_next_step: "Add EMS telemetry, measured SOC, availability, and meter reconciliation.",
      status: evidence?.signal?.status ?? "not_loaded",
      what_it_proves: "The asset can move energy within its physical envelope.",
    },
    {
      demo_layer: "Revenue generated",
      proof: `${revenueSummary?.total_estimated_revenue_eur ?? "-"} EUR / ${revenueSummary?.eligible_product_count ?? "-"} eligible product(s)`,
      production_next_step: "Replace assumptions with executed trades, tariffs, fees, and settlement records.",
      status: evidence?.revenue?.status ?? "not_loaded",
      what_it_proves: "There is a commercial value case to discuss.",
    },
    {
      demo_layer: "Sizing scenarios generated",
      proof: `${arrayLength(evidence?.scenarios?.results)} scenario case(s)`,
      production_next_step: "Version investment cases with capex, degradation, availability, and contract assumptions.",
      status: evidence?.scenarios?.status ?? "not_loaded",
      what_it_proves: "The business case can be compared across asset sizes.",
    },
    {
      demo_layer: "Investor stress cases generated",
      proof: `${arrayLength(evidence?.stress?.results)} stress case(s)`,
      production_next_step: "Connect approved risk policies, hedge terms, and live availability tests.",
      status: evidence?.stress?.status ?? "not_loaded",
      what_it_proves: "The downside story is visible before investment review.",
    },
    {
      demo_layer: "Report generated",
      proof: String(latestReport?.report_title ?? reportSummary?.delivery_status ?? "-"),
      production_next_step: "Add signed archive, PDF export, audit package, and settlement pack.",
      status: evidence?.report?.status ?? "not_loaded",
      what_it_proves: "The story can be packaged for client or investor review.",
    },
    {
      demo_layer: "Investor readiness score available",
      proof: `${readiness?.summary?.readiness_score ?? "-"}% / ${readiness?.summary?.open_gap_count ?? "-"} open gap(s)`,
      production_next_step: "Connect real integrations and provenance before claiming production readiness.",
      status: readiness?.summary?.readiness_status ?? evidence?.readiness?.status ?? "not_loaded",
      what_it_proves: "The open diligence questions are explicit.",
    },
  ];
}

function checklistTone(rows: TableRow[]): Tone {
  if (rows.some((row) => ["error", "not_found", "not_loaded"].includes(String(row.status)))) {
    return "amber";
  }

  if (rows.some((row) => String(row.status) === "blocked")) {
    return "red";
  }

  return "emerald";
}

function nestedObject(source: ApiEnvelope | undefined, key: string) {
  const value = source?.[key];

  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as TableRow)
    : undefined;
}

function arrayLength(value: unknown) {
  return Array.isArray(value) ? value.length : 0;
}

function NarrativeCallout({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <div className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-slate-500">
        {label}
      </div>
      <p className="mt-2 text-sm leading-5 text-slate-300">{value ?? "-"}</p>
    </div>
  );
}

function CheckpointIcon({ tone }: { tone: Tone }) {
  if (tone === "emerald") {
    return <CheckCircle2 className="h-5 w-5 text-emerald-300" />;
  }

  if (tone === "red") {
    return <CircleAlert className="h-5 w-5 text-red-300" />;
  }

  return <CircleDashed className="h-5 w-5 text-amber-300" />;
}

function checkpointTone(tone: unknown): Tone {
  if (tone === "emerald" || tone === "amber" || tone === "red") {
    return tone;
  }

  return "slate";
}

function scoreAccent(score?: number): Tone {
  if (score === undefined) {
    return "slate";
  }

  if (score >= 80) {
    return "emerald";
  }

  if (score >= 50) {
    return "amber";
  }

  return "red";
}

function overallAccent(overall?: ReadinessStatus): Tone {
  if (overall === "ready") {
    return "emerald";
  }

  if (overall === "blocked") {
    return "red";
  }

  return "amber";
}

function normalizeReadinessStatus(status: unknown): ReadinessStatus {
  if (status === "ready" || status === "blocked") {
    return status;
  }

  return "review";
}

function numberValue(value: unknown) {
  const number = Number(value);

  return Number.isFinite(number) ? number : undefined;
}
