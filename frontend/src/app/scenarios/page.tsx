"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ActionButton } from "@/components/action-button";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ErrorState } from "@/components/error-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { ApiEnvelope, TableRow } from "@/types/api";

type ScenarioResponse = ApiEnvelope<{
  results?: TableRow[];
  scenario_file?: string;
  stress_file?: string;
}>;

const scenarioTabs = [
  {
    id: "asset-sizing",
    label: "Asset Sizing",
    helper: "Compare battery sizes against the same forecast to expose scale economics.",
  },
  {
    id: "price-stress",
    label: "Price Stress",
    helper: "Check whether expected value survives price shifts, caps, floors, and downside cases.",
  },
  {
    id: "controls",
    label: "Run Controls",
    helper: "Refresh backend scenario and stress-test evidence from the latest forecast.",
  },
] as const;

type ScenarioTabId = (typeof scenarioTabs)[number]["id"];

export default function ScenariosPage() {
  const [activeTab, setActiveTab] = useState<ScenarioTabId>("asset-sizing");

  const scenarios = useQuery({
    queryFn: () => apiGet<ScenarioResponse>("/scenarios/latest"),
    queryKey: ["scenarios-latest"],
  });

  const stress = useQuery({
    queryFn: () => apiGet<ScenarioResponse>("/stress/latest"),
    queryKey: ["stress-latest"],
  });

  const scenarioRows = scenarios.data?.results ?? [];
  const stressRows = stress.data?.results ?? [];
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
    scenarioCount: scenarioRows.length,
    scenariosStatus: scenarios.data?.status,
    stressCount: stressRows.length,
    stressStatus: stress.data?.status,
  });

  const refetchScenarios = () =>
    Promise.all([scenarios.refetch(), stress.refetch()]);

  return (
    <>
      <PageHeading
        description="Convert optimizer outputs into bankable what-if evidence: asset sizing, downside survival, upside capture, and automation guardrails before committing capital or live strategy limits."
        eyebrow="Commercial resilience"
        title="Scenario resilience lab"
      />

      {scenarios.data?.status === "not_found" && stress.data?.status === "not_found" ? (
        <div className="mb-6">
          <ErrorState message="No scenario evidence exists yet. Run scenario and price stress analysis from the controls tab after loading a forecast." />
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
        eyebrow="Automation sizing decision"
        nextAction={
          downsideAtRisk
            ? "Keep automated trading constrained until the downside stress case is explained or guarded."
            : "Use the leading sizing case as bankable evidence for automated strategy limits."
        }
        title="Scenario-to-automation basis"
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

      <SectionCard
        action={
          <StatusPill tone={downsideAtRisk || !scenarioRows.length || !stressRows.length ? "amber" : "emerald"}>
            Scenario evidence
          </StatusPill>
        }
        className="mb-6"
        title="Scenario-to-business-value bridge"
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

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={scenarioTabs}
      />

      {activeTab === "asset-sizing" ? (
        <SectionCard title="Battery sizing scenarios">
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
      ) : null}

      {activeTab === "price-stress" ? (
        <SectionCard title="Price stress tests">
          <DataTable
            columns={[
              "scenario_name",
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
      ) : null}

      {activeTab === "controls" ? (
        <div className="grid gap-5 xl:grid-cols-2">
          <SectionCard title="Run backend analysis">
            <div className="grid gap-3 md:grid-cols-2">
              <ActionButton
                endpoint="/scenarios/run-latest"
                label="Run sizing scenarios"
                refetch={refetchScenarios}
                variant="primary"
              />
              <ActionButton
                endpoint="/stress/run-latest"
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
  scenarioCount,
  scenariosStatus,
  stressCount,
  stressStatus,
}: {
  scenarioCount: number;
  scenariosStatus?: string;
  stressCount: number;
  stressStatus?: string;
}) {
  return [
    {
      backend_route: "/scenarios/latest",
      business_value: "Loads persisted asset sizing economics for investment and strategy limits.",
      capability: "Asset sizing evidence",
      status: `${scenariosStatus ?? "unknown"} / ${scenarioCount} case(s)`,
    },
    {
      backend_route: "/stress/latest",
      business_value: "Loads downside and upside price stress evidence before automation is trusted.",
      capability: "Price stress evidence",
      status: `${stressStatus ?? "unknown"} / ${stressCount} case(s)`,
    },
    {
      backend_route: "/scenarios/run-latest",
      business_value: "Refreshes sizing evidence from the latest forecast and optimizer output.",
      capability: "Sizing run control",
      status: "available",
    },
    {
      backend_route: "/stress/run-latest",
      business_value: "Refreshes downside guardrail evidence before strategy escalation.",
      capability: "Stress run control",
      status: "available",
    },
  ];
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
