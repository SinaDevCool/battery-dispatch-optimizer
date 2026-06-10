"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { DecisionBrief } from "@/components/decision-brief";
import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import {
  RevenueAllocationPanel,
  RevenueConstraintsPanel,
  RevenueEconomicsPanel,
  RevenueRunControlsPanel,
  RevenueStackPanel,
} from "@/components/revenue/revenue-workbench-panels";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type {
  AncillaryEligibilityResponse,
  BusinessDecisionResponse,
  EegComplianceResponse,
  HedgingRevenueResponse,
  LatestSignalResponse,
  RevenueAllocationResponse,
  RevenueStackResult,
  RevenueStackResponse,
  TableRow,
} from "@/types/api";

const revenueTabs = [
  {
    id: "stack",
    label: "Market Stack",
    helper: "Tradable products, revenue ranking, eligibility, and product-level blockers.",
  },
  {
    id: "allocation",
    label: "Capacity Allocation",
    helper: "How battery capacity should be assigned across revenue pools.",
  },
  {
    id: "constraints",
    label: "Constraints",
    helper: "Missing inputs, blocked products, EEG status, ancillary readiness, and review warnings.",
  },
  {
    id: "economics",
    label: "Economics",
    helper: "Owner/investor view of merchant value, hedge protection, and recommendation basis.",
  },
  {
    id: "controls",
    label: "Run Controls",
    helper: "Refresh the revenue stack and allocation decision.",
  },
] as const;

type RevenueTabId = (typeof revenueTabs)[number]["id"];

type RevenuePersonaFraming = {
  bridgeTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  eyebrow: string;
  nextActionClear: string;
  nextActionBlocked: string;
  readyLabel: string;
  title: string;
};

export default function RevenuePage() {
  const { selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const framing = getRevenuePersonaFraming(personaId);
  const [activeTab, setActiveTab] = useState<RevenueTabId>("stack");
  const visibleRevenueTabs = useMemo(
    () =>
      persona.layer === "client"
        ? revenueTabs.filter((tab) => tab.id !== "controls")
        : revenueTabs,
    [persona.layer],
  );
  const effectiveActiveTab = visibleRevenueTabs.some((tab) => tab.id === activeTab)
    ? activeTab
    : "economics";

  const stack = useQuery({
    queryFn: () =>
      apiGet<RevenueStackResponse>(
        `/assets/${selectedAssetId}/revenue-stack/latest`,
      ),
    queryKey: ["revenue-stack", selectedAssetId],
  });

  const allocation = useQuery({
    queryFn: () =>
      apiGet<RevenueAllocationResponse>(
        `/assets/${selectedAssetId}/revenue-stack/allocation/latest`,
      ),
    queryKey: ["revenue-allocation", selectedAssetId],
  });

  const signal = useQuery({
    queryFn: () =>
      apiGet<LatestSignalResponse>(`/assets/${selectedAssetId}/signal/latest`),
    queryKey: ["revenue-signal-latest", selectedAssetId],
  });

  const hedging = useQuery({
    queryFn: () =>
      apiGet<HedgingRevenueResponse>(
        `/assets/${selectedAssetId}/hedging/revenue`,
      ),
    queryKey: ["revenue-hedging", selectedAssetId],
  });

  const eeg = useQuery({
    queryFn: () =>
      apiGet<EegComplianceResponse>(
        `/assets/${selectedAssetId}/eeg-compliance/latest`,
      ),
    queryKey: ["revenue-eeg", selectedAssetId],
  });

  const ancillary = useQuery({
    queryFn: () =>
      apiGet<AncillaryEligibilityResponse>(
        `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
      ),
    queryKey: ["revenue-ancillary", selectedAssetId],
  });

  const businessDecision = useQuery({
    queryFn: () =>
      apiGet<BusinessDecisionResponse>(
        `/assets/${selectedAssetId}/business-decision/latest`,
      ),
    queryKey: ["revenue-business-decision", selectedAssetId],
  });

  const rows = normalizeRevenueRows(stack.data);
  const allocationRows = allocation.data?.results ?? [];
  const eligibleRows = rows.filter((row) => row.eligibility_status === "eligible");
  const blockedRows = rows.filter(
    (row) =>
      row.eligibility_status === "not_eligible" ||
      row.status === "blocked" ||
      row.blocking_reasons !== "-",
  );
  const warningRows = rows.filter((row) => row.review_warnings !== "-");
  const metadata = signal.data?.data?.metadata ?? {};
  const summary = signal.data?.data?.summary ?? {};
  const hedgeSummary = hedging.data?.summary ?? {};
  const totalRevenue =
    stack.data?.total_estimated_revenue_eur ??
    rows.reduce(
      (sum, row) => sum + Number(row.estimated_revenue_eur ?? 0),
      0,
    );
  const bestProduct = rows
    .filter((row) => row.eligibility_status === "eligible")
    .toSorted(
      (left, right) =>
        Number(right.estimated_revenue_eur ?? 0) -
        Number(left.estimated_revenue_eur ?? 0),
    )[0];
  const executableRevenue = eligibleRows
    .filter((row) => row.status === "ok" || row.automation_fit === "ready for market allocation")
    .reduce((sum, row) => sum + Number(row.estimated_revenue_eur ?? 0), 0);
  const blockedRevenue = rows
    .filter((row) => row.automation_fit !== "ready for market allocation")
    .reduce((sum, row) => sum + Number(row.estimated_revenue_eur ?? 0), 0);
  const commercialBlockers = [
    blockedRows.length ? `${blockedRows.length} product(s) are blocked or not eligible.` : null,
    warningRows.length ? `${warningRows.length} product(s) require commercial review.` : null,
    allocationRows.length ? null : "Capacity allocation evidence is not available yet.",
  ].filter(Boolean) as string[];
  const revenueUnlockRows = buildRevenueUnlockRows(rows);

  return (
    <>
      <PageHeading
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
      />

      <DecisionBrief
        blockers={commercialBlockers}
        className="mb-6"
        decision={
          <>
            {formatCurrency(totalRevenue)}
            <span className="text-slate-500"> / </span>
            {bestProduct?.product_id ?? "product pending"}
          </>
        }
        evidence={[
          `${eligibleRows.length}/${stack.data?.product_count ?? rows.length} market product(s) eligible.`,
          bestProduct
            ? `${bestProduct.product_id} is currently the strongest eligible revenue product.`
            : "No eligible product has been ranked yet.",
          businessDecision.data?.decision?.recommendation_status
            ? `Decision status: ${businessDecision.data.decision.recommendation_status}.`
            : "Business decision evidence is pending.",
        ]}
        eyebrow={framing.decisionEyebrow}
        nextAction={
          commercialBlockers.length
            ? framing.nextActionBlocked
            : framing.nextActionClear
        }
        title={framing.decisionTitle}
        tone={commercialBlockers.length ? "amber" : "emerald"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard accent="emerald" label="Modelled revenue" value={formatCurrency(totalRevenue)} />
        <KpiCard label="Eligible products" value={`${eligibleRows.length}/${stack.data?.product_count ?? rows.length}`} />
        <KpiCard label="Allocation status" value={allocation.data?.status ?? "-"} />
        <KpiCard accent="blue" label="Asset" value={selectedAssetId} />
      </div>

      <SectionCard
        action={
          <StatusPill tone={commercialBlockers.length ? "amber" : "emerald"}>
            {commercialBlockers.length ? "Revenue not fully bankable" : framing.readyLabel}
          </StatusPill>
        }
        className="mb-5"
        title={framing.bridgeTitle}
      >
        <div className="mb-4 grid gap-4 md:grid-cols-3">
          <KpiCard
            accent="emerald"
            label="Automatable now"
            value={formatCurrency(executableRevenue)}
            helper="Eligible products with clear automation fit."
          />
          <KpiCard
            accent={blockedRevenue > 0 ? "amber" : "emerald"}
            label="Blocked or review upside"
            value={formatCurrency(blockedRevenue)}
            helper={`${blockedRows.length + warningRows.length} product(s) need evidence or review.`}
          />
          <KpiCard
            accent={allocationRows.length ? "emerald" : "amber"}
            label="Allocation proof"
            value={allocationRows.length ? "available" : "missing"}
            helper="Needed before promising capacity across products."
          />
        </div>
        <DataTable
          columns={["product_id", "commercial_value", "automation_fit", "unlock_action"]}
          rows={revenueUnlockRows}
        />
      </SectionCard>

      <WorkspaceTabs
        activeTab={effectiveActiveTab}
        onTabChange={setActiveTab}
        tabs={visibleRevenueTabs}
      />

      {effectiveActiveTab === "stack" ? (
        <RevenueStackPanel
          ancillary={ancillary.data}
          blockedRows={blockedRows}
          eligibleRows={eligibleRows}
          rows={rows}
          warningRows={warningRows}
        />
      ) : null}

      {effectiveActiveTab === "allocation" ? (
        <RevenueAllocationPanel
          allocationRows={allocationRows}
          metadata={metadata}
          signalSummary={summary}
        />
      ) : null}

      {effectiveActiveTab === "constraints" ? (
        <RevenueConstraintsPanel
          ancillary={ancillary.data}
          blockedRows={blockedRows}
          eeg={eeg.data}
          warningRows={warningRows}
        />
      ) : null}

      {effectiveActiveTab === "economics" ? (
        <RevenueEconomicsPanel
          allocationRows={allocationRows}
          ancillary={ancillary.data}
          businessDecision={businessDecision.data?.decision}
          eeg={eeg.data}
          hedgeSummary={hedgeSummary}
          metadata={metadata}
          revenueRows={rows}
          signalSummary={summary}
          totalRevenue={totalRevenue}
        />
      ) : null}

      {effectiveActiveTab === "controls" ? (
        <RevenueRunControlsPanel
          refetchAllocation={() => allocation.refetch()}
          refetchStack={() => stack.refetch()}
          selectedAssetId={selectedAssetId}
        />
      ) : null}
    </>
  );
}

function getRevenuePersonaFraming(personaId: PersonaId): RevenuePersonaFraming {
  const defaults: RevenuePersonaFraming = {
    bridgeTitle: "Bankable revenue bridge",
    decisionEyebrow: "Commercial decision",
    decisionTitle: "Revenue-to-market decision",
    description:
      "Decide which revenue streams are tradable, how capacity should be allocated, what constraints block value, and how the economics look to owners and investors.",
    eyebrow: "Commercial optimizer",
    nextActionBlocked:
      "Resolve product eligibility, allocation, or review blockers before promising automated revenue capture.",
    nextActionClear:
      "Use this revenue stack to guide market allocation and trading strategy intent.",
    readyLabel: "Bankable stack",
    title: "Revenue stack",
  };

  const frames: Partial<Record<PersonaId, RevenuePersonaFraming>> = {
    asset_owner: {
      bridgeTitle: "Owner revenue assurance bridge",
      decisionEyebrow: "Owner value decision",
      decisionTitle: "How much revenue can the owner rely on?",
      description:
        "Show the owner which revenue streams are usable now, what value is blocked, and what evidence is needed before expected revenue can be treated as reliable.",
      eyebrow: "Client evidence portal",
      nextActionBlocked:
        "Clear product, allocation, or review blockers before presenting the value as owner-ready.",
      nextActionClear:
        "Use this revenue view as the owner-facing basis for performance and trading intent.",
      readyLabel: "Owner-ready",
      title: "Owner revenue assurance",
    },
    investor_lender: {
      bridgeTitle: "Bankable revenue bridge",
      decisionEyebrow: "Investment revenue decision",
      decisionTitle: "Is this revenue stack bankable enough for diligence?",
      description:
        "Separate defensible revenue from upside that still depends on eligibility, allocation evidence, hedge protection, or commercial review.",
      eyebrow: "Bankability view",
      nextActionBlocked:
        "Close eligibility, allocation, and review gaps before using this revenue case in investment or lending review.",
      nextActionClear:
        "Use this revenue stack as bankability evidence alongside hedging, settlement, and audit proof.",
      readyLabel: "Bankable stack",
      title: "Bankable revenue assurance",
    },
    executive: {
      bridgeTitle: "Portfolio value bridge",
      decisionEyebrow: "Executive revenue decision",
      decisionTitle: "Is revenue growth credible and action-ready?",
      description:
        "Summarize modelled revenue, blocked value, allocation proof, and commercial blockers so management can judge whether the asset is creating credible value.",
      eyebrow: "Executive view",
      nextActionBlocked:
        "Resolve the top commercial blocker before escalating this value story to management or the board.",
      nextActionClear:
        "Use this revenue stack to support portfolio performance and strategic trading decisions.",
      readyLabel: "Management-ready",
      title: "Executive revenue assurance",
    },
    client_success: {
      bridgeTitle: "Client revenue explanation bridge",
      decisionEyebrow: "Client revenue explanation",
      decisionTitle: "Can we explain the revenue story to the client?",
      description:
        "Translate revenue stack, blocked upside, allocation proof, and commercial review gaps into a clear client conversation and next-action story.",
      eyebrow: "Client delivery",
      nextActionBlocked:
        "Explain the open revenue blockers and next actions before sending the client report.",
      nextActionClear:
        "Use this revenue story in the client report and settlement follow-up.",
      readyLabel: "Client-explainable",
      title: "Client revenue explanation",
    },
    project_developer: {
      bridgeTitle: "Development revenue bridge",
      decisionEyebrow: "Development revenue decision",
      decisionTitle: "Which revenue assumptions can support the project case?",
      description:
        "Use revenue stack evidence to separate bankable pre-COD assumptions from market access, eligibility, and allocation gaps that still affect the development case.",
      eyebrow: "Development readiness",
      nextActionBlocked:
        "Resolve market eligibility and allocation evidence before relying on the revenue case in development planning.",
      nextActionClear:
        "Use this revenue stack as commercial input for scenario planning and stakeholder materials.",
      readyLabel: "Development-ready",
      title: "Development revenue case",
    },
    revenue_analyst: {
      bridgeTitle: "Commercial analytics bridge",
      decisionEyebrow: "Revenue analytics decision",
      decisionTitle: "Where is tradable value available or blocked?",
      description:
        "Quantify revenue by product, allocation route, automation fit, hedge context, and blocker so the commercial model can feed trading and client evidence.",
      eyebrow: "Commercial analytics OS",
      nextActionBlocked:
        "Quantify blocked value and update product eligibility or allocation assumptions before forwarding the stack.",
      nextActionClear:
        "Feed eligible revenue streams into allocation, reporting, and owner/investor evidence.",
      readyLabel: "Analysis-ready",
      title: "Revenue analytics workbench",
    },
    forecast_quant: {
      bridgeTitle: "Forecast-to-revenue bridge",
      decisionEyebrow: "Model-to-revenue decision",
      decisionTitle: "Does the model output create credible revenue?",
      description:
        "Connect forecast and signal assumptions to revenue outcomes, blocked products, allocation proof, and economics so model quality is tied to commercial value.",
      eyebrow: "Model quality OS",
      nextActionBlocked:
        "Resolve forecast, eligibility, or allocation evidence gaps before treating the revenue output as model-backed.",
      nextActionClear:
        "Use this revenue stack to validate forecast and optimizer assumptions against commercial value.",
      readyLabel: "Model-backed",
      title: "Model-backed revenue evidence",
    },
  };

  return frames[personaId] ?? defaults;
}

function normalizeRevenueRows(data?: RevenueStackResponse): TableRow[] {
  const sourceRows = data?.results?.length ? data.results : data?.products ?? [];

  return sourceRows.map((row: RevenueStackResult) => ({
    ...row,
    automation_fit: classifyRevenueAutomationFit(row),
    blocking_reasons: formatIssueList(row.blocking_reasons),
    estimated_revenue_eur: row.estimated_revenue_eur ?? row.revenue_eur ?? row.total_revenue_eur ?? 0,
    missing_inputs: row.missing_inputs?.join(", ") || "-",
    product_id: row.product_id ?? row.market ?? "-",
    review_warnings: formatIssueList(row.review_warnings),
  }));
}

function formatIssueList(value: unknown) {
  if (!Array.isArray(value) || value.length === 0) {
    return "-";
  }

  return value
    .map((item) => {
      if (typeof item === "string") {
        return item;
      }

      if (item && typeof item === "object" && "message" in item) {
        return String((item as { message?: unknown }).message);
      }

      return JSON.stringify(item);
    })
    .join("; ");
}

function classifyRevenueAutomationFit(row: RevenueStackResult) {
  if (row.eligibility_status === "eligible" && row.status === "ok") {
    return "ready for market allocation";
  }

  if (row.eligibility_status === "not_eligible" || row.blocking_reasons?.length) {
    return "blocked from automation";
  }

  if (row.eligibility_status === "review_required" || row.review_warnings?.length) {
    return "needs commercial review";
  }

  return "advisory only";
}

function buildRevenueUnlockRows(rows: TableRow[]) {
  return rows
    .toSorted(
      (left, right) =>
        Number(right.estimated_revenue_eur ?? 0) -
        Number(left.estimated_revenue_eur ?? 0),
    )
    .slice(0, 6)
    .map((row) => ({
      automation_fit: row.automation_fit,
      commercial_value: formatCurrency(Number(row.estimated_revenue_eur ?? 0)),
      product_id: row.product_id,
      unlock_action: buildUnlockAction(row),
    }));
}

function buildUnlockAction(row: TableRow) {
  if (row.automation_fit === "ready for market allocation") {
    return "Route into capacity allocation and bid proposal.";
  }

  if (row.blocking_reasons && row.blocking_reasons !== "-") {
    return String(row.blocking_reasons);
  }

  if (row.review_warnings && row.review_warnings !== "-") {
    return String(row.review_warnings);
  }

  if (row.missing_inputs && row.missing_inputs !== "-") {
    return `Provide missing inputs: ${row.missing_inputs}`;
  }

  return "Run allocation and commercial review before automation.";
}
