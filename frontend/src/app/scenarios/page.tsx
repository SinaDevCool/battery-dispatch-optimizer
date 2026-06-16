"use client";

import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useState } from "react";

import { ActionButton } from "@/components/action-button";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { EvidenceSourceSection } from "@/components/evidence-source-section";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { ProofCardGrid } from "@/components/proof-card-grid";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type { ApiEnvelope, InvestorReadinessResponse, TableRow } from "@/types/api";

type ScenarioResponse = ApiEnvelope<{
  metadata?: TableRow;
  results?: TableRow[];
  scenario_proof?: {
    kpis?: TableRow[];
    rows?: TableRow[];
  };
  scenario_file?: string;
  stress_proof?: {
    kpis?: TableRow[];
    rows?: TableRow[];
  };
  stress_file?: string;
}>;

const scenarioTabs = [
  {
    id: "asset-sizing",
    label: "Base Cases",
    helper: "Compare asset sizes and operating envelopes against the same forecast.",
  },
  {
    id: "price-stress",
    label: "Downside Cases",
    helper: "Check whether the value story survives price, dispatch, degradation, and asset-specific stress.",
  },
  {
    id: "controls",
    label: "Run Controls",
    helper: "Refresh backend scenario and stress-test evidence from the latest forecast.",
  },
] as const;

type ScenarioTabId = (typeof scenarioTabs)[number]["id"];

type ScenarioPersonaFraming = {
  bridgeTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  emptyMessage: string;
  eyebrow: string;
  nextActionClear: string;
  nextActionDownside: string;
  sizingTitle: string;
  stressTitle: string;
  title: string;
};

export default function ScenariosPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const framing = getScenarioPersonaFraming(personaId);
  const [activeTab, setActiveTab] = useState<ScenarioTabId>("asset-sizing");
  const visibleScenarioTabs =
    persona.layer === "client"
      ? scenarioTabs.filter((tab) => tab.id !== "controls")
      : scenarioTabs;
  const effectiveActiveTab = visibleScenarioTabs.some((tab) => tab.id === activeTab)
    ? activeTab
    : "asset-sizing";

  const scenarios = useQuery({
    queryFn: () => apiGet<ScenarioResponse>(`/assets/${selectedAssetId}/scenarios/latest`),
    queryKey: ["scenarios-latest", selectedAssetId],
  });

  const stress = useQuery({
    queryFn: () => apiGet<ScenarioResponse>(`/assets/${selectedAssetId}/stress/latest`),
    queryKey: ["stress-latest", selectedAssetId],
  });

  const investorReadiness = useQuery({
    queryFn: () =>
      apiGet<InvestorReadinessResponse>(
        `/assets/${selectedAssetId}/investor-readiness`,
      ),
    queryKey: ["scenarios-investor-readiness", selectedAssetId],
  });

  const scenarioRows = scenarios.data?.results ?? [];
  const stressRows = stress.data?.results ?? [];
  const readinessData = investorReadiness.data;
  const bestScenario = findBestRow(scenarioRows);
  const worstStress = findWorstRow(stressRows);
  const downsideAtRisk = Number(worstStress?.total_pnl_eur ?? 0) < 0;
  const automationScenarioRows = scenarioRows.slice(0, 8).map((row) => ({
    ...row,
    automation_case:
      row.scenario_name === bestScenario?.scenario_name
        ? "candidate sizing basis"
        : "comparison case",
  }));
  const automationStressRows = stressRows.slice(0, 8).map((row) => ({
    ...row,
    automation_case:
      Number(row.total_pnl_eur ?? 0) < 0
        ? "automation guardrail"
        : "resilience evidence",
  }));
  const scenarioEvidenceRows = buildScenarioEvidenceRows({
    bestScenario,
    downsideAtRisk,
    scenarioRows,
    scenariosStatus: scenarios.data?.status,
    stressRows,
    stressStatus: stress.data?.status,
    worstStress,
  });
  const backendConnectionRows = buildScenarioBackendConnectionRows({
    selectedAssetId,
    scenarioCount: scenarioRows.length,
    scenariosStatus: scenarios.data?.status,
    stressCount: stressRows.length,
    stressStatus: stress.data?.status,
  });
  const backendScenarioKpis = normalizeProofKpis(scenarios.data?.scenario_proof?.kpis);
  const backendStressKpis = normalizeProofKpis(stress.data?.stress_proof?.kpis);
  const visibleScenarioProofRows = scenarios.data?.scenario_proof?.rows ?? [];
  const visibleStressProofRows = stress.data?.stress_proof?.rows ?? [];
  const investorRiskCaseRows = buildInvestorRiskCaseRows(stressRows);
  const readinessImpactRows = buildReadinessImpactRows({
    readiness: readinessData,
    stressRows,
    worstStress,
  });

  const refetchScenarios = () =>
    Promise.all([scenarios.refetch(), stress.refetch()]);

  return (
    <>
      <PageHeading
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
      />

      {scenarios.data?.status === "not_found" && stress.data?.status === "not_found" ? (
        <div className="mb-6">
          <ErrorState message={framing.emptyMessage} />
        </div>
      ) : null}

      <DecisionBrief
        blockers={[
          scenarioRows.length ? null : "Asset sizing scenarios are missing.",
          stressRows.length ? null : "Price stress evidence is missing.",
          downsideAtRisk ? "At least one stress case produces negative PnL." : null,
        ].filter(Boolean) as string[]}
        className="mb-6"
        decision={
          <>
            {displayValue(bestScenario?.scenario_name)}
            <span className="text-slate-500"> / </span>
            {formatCurrency(bestScenario?.total_pnl_eur)}
          </>
        }
        evidence={[
          `${scenarioRows.length} sizing case(s) compare capacity and power economics.`,
          worstStress
            ? `${displayValue(worstStress.scenario_name)} is the worst stress case at ${formatCurrency(worstStress.total_pnl_eur)}.`
            : "No price stress case has been recorded.",
          `${formatNumber(bestScenario?.profit_per_mw_day, 2)} EUR/MW-day best sizing economics.`,
        ]}
        eyebrow={framing.decisionEyebrow}
        nextAction={
          downsideAtRisk
            ? framing.nextActionDownside
            : framing.nextActionClear
        }
        title={framing.decisionTitle}
        tone={downsideAtRisk || !scenarioRows.length || !stressRows.length ? "amber" : "emerald"}
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={bestScenario ? "emerald" : "slate"}
          label="Best asset case"
          value={displayValue(bestScenario?.scenario_name)}
          helper={formatCurrency(bestScenario?.total_pnl_eur)}
        />
        <KpiCard
          accent={downsideAtRisk ? "red" : "emerald"}
          label="Worst stress case"
          value={displayValue(worstStress?.scenario_name)}
          helper={formatCurrency(worstStress?.total_pnl_eur)}
        />
        <KpiCard
          accent="blue"
          label="Sizing cases"
          value={scenarioRows.length}
          helper={`${formatNumber(bestScenario?.profit_per_mw_day, 2)} EUR/MW-day best case`}
        />
        <KpiCard
          accent={stressRows.length ? "amber" : "slate"}
          label="Stress cases"
          value={stressRows.length}
          helper={downsideAtRisk ? "Downside breach visible" : "No negative stress PnL found"}
        />
      </div>

      <WorkspaceTabs
        activeTab={effectiveActiveTab}
        onTabChange={setActiveTab}
        tabs={visibleScenarioTabs}
      />

      {effectiveActiveTab === "asset-sizing" ? (
        <div className="space-y-5">
          <SectionCard
            action={
              <StatusPill tone={downsideAtRisk || !scenarioRows.length || !stressRows.length ? "amber" : "emerald"}>
                Investment evidence
              </StatusPill>
            }
            title={framing.bridgeTitle}
          >
            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(420px,1.1fr)]">
              <DataTable
                columns={["business_question", "answer", "automation_use"]}
                rows={scenarioEvidenceRows}
              />
              <DataTable
                columns={["capability", "backend_route", "status", "business_value"]}
                rows={backendConnectionRows}
              />
            </div>
          </SectionCard>
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
            <SectionCard title={framing.sizingTitle}>
              <DataTable
                columns={[
                  "scenario_name",
                  "capacity_mwh",
                  "max_charge_power_mw",
                  "max_discharge_power_mw",
                  "automation_case",
                  "signal",
                  "opportunity_level",
                  "total_pnl_eur",
                  "profit_per_mw_day",
                  "charge_hours",
                  "discharge_hours",
                ]}
                rows={automationScenarioRows}
              />
            </SectionCard>
            <EvidenceSourceSection
              asset={selectedAsset}
              metadata={scenarios.data?.metadata}
              title="Can the base case be defended?"
            />
          </div>
          <SectionCard
            action={<StatusPill tone="blue">Scenario proof</StatusPill>}
            title="Base case proof"
          >
            <div className="mb-4 grid gap-4 md:grid-cols-3">
              {backendScenarioKpis.map((kpi) => (
                <KpiCard
                  accent={kpi.accent}
                  helper={kpi.helper}
                  key={kpi.label}
                  label={kpi.label}
                  value={kpi.value}
                />
              ))}
            </div>
            <DataTable
              columns={["scenario_driver", "mock_evidence", "investor_meaning", "production_upgrade"]}
              rows={visibleScenarioProofRows}
            />
          </SectionCard>
        </div>
      ) : null}

      {effectiveActiveTab === "price-stress" ? (
        <div className="space-y-5">
          <SectionCard
            action={<StatusPill tone={downsideAtRisk ? "amber" : "emerald"}>Mock stress evidence</StatusPill>}
            title="Downside resilience"
          >
            <div className="grid gap-5">
              <ProofCardGrid
                fields={[
                  { key: "mock_stress", label: "Mock stress" },
                  { key: "readiness_impact", label: "Readiness impact" },
                  { key: "investor_decision", label: "Investor decision" },
                ]}
                rows={investorRiskCaseRows}
                titleKey="risk_case"
              />
              <DataTable
                columns={["decision_layer", "current_state", "stress_signal", "investor_meaning"]}
                rows={readinessImpactRows}
              />
            </div>
          </SectionCard>
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
            <SectionCard title={framing.stressTitle}>
              <DataTable
                columns={[
                  "scenario_name",
                  "investor_case",
                  "stress_category",
                  "automation_case",
                  "signal",
                  "opportunity_level",
                  "total_pnl_eur",
                  "profit_per_mw_day",
                  "charge_hours",
                  "discharge_hours",
                ]}
                rows={automationStressRows}
              />
            </SectionCard>
            <EvidenceSourceSection
              asset={selectedAsset}
              metadata={stress.data?.metadata}
              title="Can the downside be explained?"
            />
          </div>
          <SectionCard
            action={<StatusPill tone="blue">Stress proof</StatusPill>}
            title="Downside proof"
          >
            <div className="mb-4 grid gap-4 md:grid-cols-3">
              {backendStressKpis.map((kpi) => (
                <KpiCard
                  accent={kpi.accent}
                  helper={kpi.helper}
                  key={kpi.label}
                  label={kpi.label}
                  value={kpi.value}
                />
              ))}
            </div>
            <DataTable
              columns={["stress_driver", "mock_evidence", "investor_meaning", "production_upgrade"]}
              rows={visibleStressProofRows}
            />
          </SectionCard>
        </div>
      ) : null}

      {effectiveActiveTab === "controls" ? (
        <div className="grid gap-5 xl:grid-cols-2">
          <SectionCard title="Run backend analysis">
            <div className="grid gap-3 md:grid-cols-2">
              <ActionButton
                endpoint={`/assets/${selectedAssetId}/scenarios/run-latest`}
                label="Run sizing scenarios"
                refetch={refetchScenarios}
                variant="primary"
              />
              <ActionButton
                endpoint={`/assets/${selectedAssetId}/stress/run-latest`}
                label="Run price stress"
                refetch={refetchScenarios}
              />
            </div>
          </SectionCard>

          <SectionCard title="Evidence files">
            <DataTable
              columns={["evidence", "status", "file"]}
              rows={[
                {
                  evidence: "Asset sizing",
                  file: scenarios.data?.scenario_file,
                  status: scenarios.data?.status ?? "-",
                },
                {
                  evidence: "Price stress",
                  file: stress.data?.stress_file,
                  status: stress.data?.status ?? "-",
                },
              ]}
            />
          </SectionCard>
        </div>
      ) : null}
    </>
  );
}

function getScenarioPersonaFraming(personaId: PersonaId): ScenarioPersonaFraming {
  const defaults: ScenarioPersonaFraming = {
    bridgeTitle: "Investment case bridge",
    decisionEyebrow: "Scenario decision",
    decisionTitle: "Which case is strong enough to present?",
    description:
      "Compare the base case, upside, downside, and operating constraints before using this asset story in investor, owner, or strategy discussions.",
    emptyMessage:
      "No scenario evidence exists yet. Run scenario and price stress analysis from the controls tab after loading a forecast.",
    eyebrow: "Commercial resilience",
    nextActionClear:
      "Use the leading case as evidence for the investor story and strategy limits.",
    nextActionDownside:
      "Explain or mitigate the downside case before presenting this asset as resilient.",
    sizingTitle: "Base case comparison",
    stressTitle: "Downside case comparison",
    title: "Investment scenario evidence",
  };

  const frames: Partial<Record<PersonaId, ScenarioPersonaFraming>> = {
    project_developer: {
      bridgeTitle: "Development scenario bridge",
      decisionEyebrow: "Development readiness decision",
      decisionTitle: "Which asset case supports the project plan?",
      description:
        "Compare asset sizes and downside price cases so pre-COD planning can separate bankable development assumptions from unresolved market and revenue risk.",
      emptyMessage:
        "No development scenario evidence exists yet. Ask the internal team to refresh sizing and price stress analysis after the forecast is available.",
      eyebrow: "Development readiness",
      nextActionClear:
        "Use the leading sizing case in development planning, financing materials, and market eligibility follow-up.",
      nextActionDownside:
        "Explain the downside case before using this scenario set in project finance or stakeholder materials.",
      sizingTitle: "Development sizing cases",
      stressTitle: "Development downside cases",
      title: "Development scenario lab",
    },
    investor_lender: {
      bridgeTitle: "Investment resilience bridge",
      decisionEyebrow: "Bankability stress decision",
      decisionTitle: "Does the asset survive downside cases?",
      description:
        "Show whether projected economics remain financeable under sizing alternatives and price stress, with clear downside exposure before diligence review.",
      emptyMessage:
        "No bankability scenario evidence exists yet. Sizing and price stress evidence are needed before investment or lending review.",
      eyebrow: "Bankability view",
      nextActionClear:
        "Use this scenario set as resilience evidence alongside hedging, revenue assurance, and audit proof.",
      nextActionDownside:
        "Resolve or mitigate the negative stress case before presenting this asset as bankable.",
      sizingTitle: "Bankability sizing cases",
      stressTitle: "Investment downside stress",
      title: "Bankability scenario evidence",
    },
    executive: {
      bridgeTitle: "Strategic resilience bridge",
      decisionEyebrow: "Executive scenario decision",
      decisionTitle: "Is the asset strategy resilient enough to scale?",
      description:
        "Summarize the best sizing case, worst downside case, and evidence depth so management can decide whether the asset strategy is credible.",
      emptyMessage:
        "No strategic scenario evidence exists yet. The asset strategy should not be escalated until sizing and stress evidence exist.",
      eyebrow: "Executive view",
      nextActionClear:
        "Use the leading scenario as management evidence for asset strategy and commercial planning.",
      nextActionDownside:
        "Keep the strategy constrained until the downside case has a mitigation or executive decision.",
      sizingTitle: "Strategic sizing cases",
      stressTitle: "Strategic downside cases",
      title: "Executive scenario evidence",
    },
    forecast_quant: {
      bridgeTitle: "Model stress-test bridge",
      decisionEyebrow: "Model robustness decision",
      decisionTitle: "Do forecast and optimizer assumptions survive stress?",
      description:
        "Use sizing and price stress runs to test model sensitivity, downside guardrails, and whether one forecast has become an untested trading policy.",
      emptyMessage:
        "No model stress evidence exists yet. Run scenario and price stress analysis after loading the latest forecast.",
      eyebrow: "Model quality OS",
      nextActionClear:
        "Use this stress set to validate forecast assumptions and optimizer guardrails.",
      nextActionDownside:
        "Investigate the negative stress case before the model output influences automation limits.",
      sizingTitle: "Model sizing sensitivity",
      stressTitle: "Forecast price stress",
      title: "Model scenario lab",
    },
    revenue_analyst: {
      bridgeTitle: "Commercial scenario bridge",
      decisionEyebrow: "Revenue scenario decision",
      decisionTitle: "Which scenario changes the commercial case?",
      description:
        "Compare sizing, stress, upside, and downside cases so revenue assumptions, hedging choices, and allocation limits stay commercially defensible.",
      emptyMessage:
        "No commercial scenario evidence exists yet. Refresh sizing and stress evidence before updating revenue or hedge assumptions.",
      eyebrow: "Commercial analytics OS",
      nextActionClear:
        "Feed the leading scenario into revenue assurance, hedging, and owner or investor evidence.",
      nextActionDownside:
        "Quantify the downside breach and update revenue, hedge, or allocation assumptions before delivery.",
      sizingTitle: "Commercial sizing cases",
      stressTitle: "Commercial price stress",
      title: "Commercial scenario lab",
    },
  };

  return frames[personaId] ?? defaults;
}

function buildScenarioEvidenceRows({
  bestScenario,
  downsideAtRisk,
  scenarioRows,
  scenariosStatus,
  stressRows,
  stressStatus,
  worstStress,
}: {
  bestScenario?: TableRow;
  downsideAtRisk: boolean;
  scenarioRows: TableRow[];
  scenariosStatus?: string;
  stressRows: TableRow[];
  stressStatus?: string;
  worstStress?: TableRow;
}) {
  return [
    {
      answer: bestScenario
        ? `${displayValue(bestScenario.scenario_name)} at ${formatCurrency(bestScenario.total_pnl_eur)}`
        : "No sizing case available",
      automation_use: "Sets candidate capacity, power, and cycle limits before live strategy scaling.",
      business_question: "What asset size creates the best economics?",
    },
    {
      answer: worstStress
        ? `${displayValue(worstStress.scenario_name)} at ${formatCurrency(worstStress.total_pnl_eur)}`
        : "No stress case available",
      automation_use: downsideAtRisk
        ? "Create a guardrail before allowing automated escalation."
        : "Supports resilient operation under current stress assumptions.",
      business_question: "Does the strategy survive downside prices?",
    },
    {
      answer: `${scenarioRows.length} sizing case(s), ${stressRows.length} stress case(s)`,
      automation_use: "Prevents one forecast run from becoming an untested trading policy.",
      business_question: "Is there enough scenario evidence?",
    },
    {
      answer: `${scenariosStatus ?? "unknown"} / ${stressStatus ?? "unknown"}`,
      automation_use: "Shows whether the evidence is fresh enough to support client or owner decisions.",
      business_question: "Is the backend evidence available?",
    },
  ];
}

function buildScenarioBackendConnectionRows({
  selectedAssetId,
  scenarioCount,
  scenariosStatus,
  stressCount,
  stressStatus,
}: {
  selectedAssetId: string;
  scenarioCount: number;
  scenariosStatus?: string;
  stressCount: number;
  stressStatus?: string;
}) {
  return [
    {
      backend_route: `/assets/${selectedAssetId}/scenarios/latest`,
      business_value: "Loads persisted asset sizing economics for investment and strategy limits.",
      capability: "Asset sizing evidence",
      status: `${scenariosStatus ?? "unknown"} / ${scenarioCount} case(s)`,
    },
    {
      backend_route: `/assets/${selectedAssetId}/stress/latest`,
      business_value: "Loads downside and upside price stress evidence before automation is trusted.",
      capability: "Price stress evidence",
      status: `${stressStatus ?? "unknown"} / ${stressCount} case(s)`,
    },
    {
      backend_route: `/assets/${selectedAssetId}/scenarios/run-latest`,
      business_value: "Refreshes sizing evidence from the latest forecast and optimizer output.",
      capability: "Sizing run control",
      status: "available",
    },
    {
      backend_route: `/assets/${selectedAssetId}/stress/run-latest`,
      business_value: "Refreshes downside guardrail evidence before strategy escalation.",
      capability: "Stress run control",
      status: "available",
    },
  ];
}

function buildInvestorRiskCaseRows(stressRows: TableRow[]): TableRow[] {
  const prioritized = [
    "Base case",
    "Low-price downside",
    "High-volatility upside",
    "Dispatch underperformance",
    "Battery degradation / availability reduction",
  ];
  const selectedRows = [
    ...prioritized
      .map((scenarioName) =>
        stressRows.find((row) => row.scenario_name === scenarioName),
      )
      .filter(Boolean),
    ...stressRows.filter((row) => row.stress_category === "asset_specific_downside"),
  ] as TableRow[];
  const uniqueRows = selectedRows.filter(
    (row, index, rows) =>
      rows.findIndex((candidate) => candidate.scenario_name === row.scenario_name) === index,
  );

  if (!uniqueRows.length) {
    return [
      {
        investor_decision: "Run selected-asset stress tests to populate investor cases.",
        mock_stress: "No stress evidence loaded",
        readiness_impact: "Scenario readiness cannot be proven yet.",
        risk_case: "Missing downside appendix",
      },
    ];
  }

  return uniqueRows.map((row) => {
    const pnl = Number(row.total_pnl_eur ?? 0);
    const isNegative = pnl < 0;
    const category = String(row.stress_category ?? "stress_case");

    return {
      investor_decision: isNegative
        ? "Needs review before presenting as resilient downside."
        : category === "market_upside"
          ? "Shows upside sensitivity without changing the production-data boundary."
          : "Works in mock evidence; keep the case in the diligence appendix.",
      mock_stress: `${displayValue(row.scenario_name)} / ${formatCurrency(row.total_pnl_eur)}`,
      readiness_impact: isNegative
        ? "Reduces revenue confidence and should create an open diligence item."
        : "Supports revenue confidence for the selected asset under this mock case.",
      risk_case: displayValue(row.investor_case ?? row.scenario_name),
    };
  });
}

function buildReadinessImpactRows({
  readiness,
  stressRows,
  worstStress,
}: {
  readiness?: InvestorReadinessResponse;
  stressRows: TableRow[];
  worstStress?: TableRow;
}): TableRow[] {
  const negativeCases = stressRows.filter((row) => Number(row.total_pnl_eur ?? 0) < 0);
  const stressStatus = negativeCases.length ? "review" : stressRows.length ? "works" : "missing";

  return [
    {
      current_state: `${readiness?.summary?.readiness_score ?? "-"}% / ${displayValue(readiness?.summary?.readiness_status)}`,
      decision_layer: "Readiness score",
      investor_meaning: "The scenario result is tied to backend readiness rather than a standalone UI claim.",
      stress_signal: stressStatus,
    },
    {
      current_state: `${negativeCases.length} negative stress case(s)`,
      decision_layer: "Revenue confidence",
      investor_meaning:
        negativeCases.length > 0
          ? "Downside survives only with review notes in the report appendix."
          : "Mock stress cases do not currently break the revenue story.",
      stress_signal: worstStress
        ? `${displayValue(worstStress.scenario_name)} at ${formatCurrency(worstStress.total_pnl_eur)}`
        : "No stress evidence loaded",
    },
    {
      current_state: `${readiness?.summary?.open_gap_count ?? "-"} open readiness gap(s)`,
      decision_layer: "Open gaps",
      investor_meaning:
        readiness?.summary?.recommended_next_action ?? "Run investor readiness to show next diligence action.",
      stress_signal: readiness?.summary?.readiness_status ?? "not_loaded",
    },
  ];
}

type ScenarioProofKpi = {
  accent: "amber" | "blue" | "emerald" | "red" | "slate";
  helper: string;
  label: string;
  value: ReactNode;
};

function normalizeProofKpis(rows?: TableRow[]): ScenarioProofKpi[] {
  return (rows ?? []).map((row) => ({
    accent: normalizeAccent(row.accent),
    helper: String(row.helper ?? ""),
    label: String(row.label ?? "Evidence"),
    value: normalizeKpiValue(row.value),
  }));
}

function normalizeAccent(value: unknown): ScenarioProofKpi["accent"] {
  if (
    value === "amber" ||
    value === "blue" ||
    value === "emerald" ||
    value === "red" ||
    value === "slate"
  ) {
    return value;
  }

  return "slate";
}

function normalizeKpiValue(value: TableRow[string]): React.ReactNode {
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  if (value === null || value === undefined) {
    return "-";
  }

  return JSON.stringify(value);
}

function findBestRow(rows: TableRow[]) {
  return [...rows].sort(
    (left, right) =>
      Number(right.total_pnl_eur ?? 0) - Number(left.total_pnl_eur ?? 0),
  )[0];
}

function findWorstRow(rows: TableRow[]) {
  return [...rows].sort(
    (left, right) =>
      Number(left.total_pnl_eur ?? 0) - Number(right.total_pnl_eur ?? 0),
  )[0];
}

function displayValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  return "-";
}
