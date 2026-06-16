"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { PersonaId } from "@/lib/personas";
import type { HedgeContract, HedgingRevenueResponse, TableRow } from "@/types/api";

type HedgingPersonaFraming = {
  bridgeTitle: string;
  decisionEyebrow: string;
  decisionTitle: string;
  description: string;
  eyebrow: string;
  nextAction: string;
  offerTitle: string;
  optionsTitle: string;
  title: string;
  whyThisPageMatters: string;
};

const hedgingTabs = [
  {
    id: "bankability",
    label: "Bankability",
    helper: "Protected revenue, merchant exposure, and backend assumption basis.",
  },
  {
    id: "offers",
    label: "Offers",
    helper: "Recommended owner offer and hedge structure comparison.",
  },
] as const;

type HedgingTabId = (typeof hedgingTabs)[number]["id"];

export default function HedgingPage() {
  const { selectedAssetId } = useAssetContext();
  const { personaId } = usePersona();
  const [activeTab, setActiveTab] = useState<HedgingTabId>("bankability");
  const framing = getHedgingPersonaFraming(personaId);

  const hedge = useQuery({
    queryFn: () =>
      apiGet<HedgingRevenueResponse>(
        `/assets/${selectedAssetId}/hedging/revenue`,
      ),
    queryKey: ["hedging-revenue", selectedAssetId],
  });

  const summary = hedge.data?.summary ?? {};
  const contracts = hedge.data?.contracts ?? [];
  const bestContract = hedge.data?.best_contract;
  const contractRows = contracts.map(formatContractRow);
  const contractSource = hedge.data?.contract_source ?? summary.contract_source;
  const assumptionRows = hedge.data?.assumption_basis ?? [];
  const hedgedRevenue =
    summary.hedged_revenue_eur ??
    bestContract?.expected_owner_revenue_eur_per_month;
  const merchantUpside =
    summary.merchant_upside_eur ??
    bestContract?.owner_upside_eur_per_month;
  const residualExposure =
    summary.residual_exposure_eur ??
    bestContract?.merchant_revenue_given_away_eur_per_month;
  const downsideProtection = bestContract?.downside_protection_eur_per_month;
  const recommendedContractName =
    bestContract?.name ?? bestContract?.contract_name ?? "contract pending";
  const recommendedRows = bestContract
    ? [
        {
          field: "Recommended contract",
          value: recommendedContractName,
        },
        {
          field: "Owner revenue",
          value: formatCurrency(bestContract.expected_owner_revenue_eur_per_month),
        },
        {
          field: "Downside protection",
          value: formatCurrency(bestContract.downside_protection_eur_per_month),
        },
        {
          field: "Availability requirement",
          value: `${bestContract.availability_requirement_percent ?? "-"}%`,
        },
      ]
    : [];

  return (
    <>
      <PageHeading
        description={framing.description}
        eyebrow={framing.eyebrow}
        title={framing.title}
      />

      {hedge.error ? (
        <div className="mb-6">
          <SectionCard title="Backend connection">
            <DataTable
              columns={["capability", "backend_route", "status", "business_value"]}
              rows={[
                {
                  backend_route: `/assets/${selectedAssetId}/hedging/revenue`,
                  business_value: "Loads hedge contract economics from the backend.",
                  capability: "Hedging revenue model",
                  status: "error",
                },
              ]}
            />
          </SectionCard>
        </div>
      ) : null}

      <DecisionBrief
        blockers={
          contracts.length
            ? []
            : ["No hedge contract options are available for commercial packaging."]
        }
        className="mb-6"
        decision={
          <>
            {recommendedContractName}
            <span className="text-slate-500"> / </span>
            {formatCurrency(hedgedRevenue)}
          </>
        }
        evidence={[
          `${contracts.length} hedge contract option(s) modelled.`,
          `${formatCurrency(downsideProtection)} expected downside protection from the recommended structure.`,
          `${formatCurrency(residualExposure)} merchant revenue is given away under the current best option.`,
        ]}
        eyebrow={framing.decisionEyebrow}
        nextAction={framing.nextAction}
        title={framing.decisionTitle}
        tone={contracts.length ? "emerald" : "amber"}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <KpiCard label="Contracts" value={contracts.length} />
        <KpiCard accent="emerald" label="Best owner revenue" value={formatCurrency(hedgedRevenue)} />
        <KpiCard label="Owner upside" value={formatCurrency(merchantUpside)} />
        <KpiCard accent="amber" label="Merchant revenue given away" value={formatCurrency(residualExposure)} />
      </div>

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={hedgingTabs}
      />

      {activeTab === "bankability" ? (
        <SectionCard title={framing.bridgeTitle}>
          <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <DataTable
              columns={["decision_input", "value"]}
              rows={[
                {
                  decision_input: "Merchant revenue basis",
                  value: formatCurrency(hedge.data?.merchant_revenue_eur_per_month),
                },
                {
                  decision_input: "Contract term source",
                  value:
                    contractSource === "client_contract"
                      ? "Client-specific contract"
                      : "Default assumption library",
                },
                {
                  decision_input: "Portfolio power basis",
                  value: `${hedge.data?.power_mw ?? "-"} MW`,
                },
                {
                  decision_input: "Why this page matters",
                  value: framing.whyThisPageMatters,
                },
              ]}
            />
            <DataTable
              columns={["input", "source", "value"]}
              rows={
                assumptionRows.length
                  ? assumptionRows
                  : [
                      {
                        input: "hedging revenue",
                        source: `/assets/${selectedAssetId}/hedging/revenue`,
                        value: hedge.data?.status ?? "not loaded",
                      },
                    ]
              }
            />
          </div>
        </SectionCard>
      ) : null}

      {activeTab === "offers" ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
          <SectionCard title={framing.offerTitle}>
            <DataTable columns={["field", "value"]} rows={recommendedRows} />
          </SectionCard>

          <SectionCard title={framing.optionsTitle}>
            <DataTable
              columns={[
                "name",
                "contract_type",
                "expected_owner_revenue_eur_per_month",
                "downside_protection_eur_per_month",
                "upside_share_percent",
                "availability_requirement_percent",
              ]}
              rows={contractRows.slice(0, 6)}
            />
          </SectionCard>
        </div>
      ) : null}
    </>
  );
}

function getHedgingPersonaFraming(personaId: PersonaId): HedgingPersonaFraming {
  const defaults: HedgingPersonaFraming = {
    bridgeTitle: "Hedge-to-bankability bridge",
    decisionEyebrow: "Bankability decision",
    decisionTitle: "Hedge-to-owner offer",
    description:
      "Convert volatile merchant battery revenue into bankable revenue profiles using floors, collars, revenue shares, and availability contracts.",
    eyebrow: "Revenue certainty",
    nextAction:
      "Use the recommended hedge as the owner-facing commercial offer, then keep merchant automation limits aligned with the availability and upside-sharing terms.",
    offerTitle: "Recommended owner offer",
    optionsTitle: "Hedge contract options",
    title: "Hedging",
    whyThisPageMatters:
      "It converts volatile merchant optimization value into an owner-facing revenue certainty offer.",
  };

  const frames: Partial<Record<PersonaId, HedgingPersonaFraming>> = {
    asset_owner: {
      bridgeTitle: "Owner downside-protection bridge",
      decisionEyebrow: "Owner protection decision",
      decisionTitle: "Which hedge gives the owner reliable revenue?",
      description:
        "Show how much owner revenue can be protected, how much upside remains, and what merchant value is exchanged for downside certainty.",
      eyebrow: "Client evidence portal",
      nextAction:
        "Use the recommended hedge to explain protected revenue, retained upside, and automation constraints to the asset owner.",
      offerTitle: "Recommended owner revenue protection",
      optionsTitle: "Owner hedge options",
      title: "Owner hedging assurance",
      whyThisPageMatters:
        "It turns volatile merchant revenue into an owner-ready protection story with explicit upside trade-offs.",
    },
    investor_lender: {
      bridgeTitle: "Hedge-to-bankability bridge",
      decisionEyebrow: "Financeability decision",
      decisionTitle: "Does the hedge make revenue bankable?",
      description:
        "Compare floor, collar, revenue-share, and availability structures to judge whether revenue certainty is strong enough for investment or lending review.",
      eyebrow: "Bankability view",
      nextAction:
        "Use the recommended hedge as bankability evidence, then verify settlement and audit proof before diligence delivery.",
      offerTitle: "Recommended bankability structure",
      optionsTitle: "Financeable hedge options",
      title: "Bankability hedging",
      whyThisPageMatters:
        "It separates merchant upside from protected cash flow so investors and lenders can judge downside risk.",
    },
    project_developer: {
      bridgeTitle: "Development financeability bridge",
      decisionEyebrow: "Development hedge decision",
      decisionTitle: "Which hedge supports the project case?",
      description:
        "Translate merchant revenue uncertainty into financeable pre-COD assumptions, downside protection, and availability obligations for the development plan.",
      eyebrow: "Development readiness",
      nextAction:
        "Use the hedge case in scenario planning and confirm market eligibility before relying on it for project finance materials.",
      offerTitle: "Recommended development hedge",
      optionsTitle: "Development hedge structures",
      title: "Development hedging case",
      whyThisPageMatters:
        "It shows whether the project can convert forecast merchant value into financeable revenue assumptions.",
    },
    client_success: {
      bridgeTitle: "Client hedge explanation bridge",
      decisionEyebrow: "Client explanation decision",
      decisionTitle: "Can we explain the hedge trade-off to the client?",
      description:
        "Turn hedge economics into a client conversation: protected revenue, retained upside, revenue given away, and the operating obligations behind the offer.",
      eyebrow: "Client delivery",
      nextAction:
        "Explain the recommended hedge in the client report together with revenue, settlement, and open evidence gaps.",
      offerTitle: "Client-ready hedge explanation",
      optionsTitle: "Client hedge comparison",
      title: "Hedge explanation",
      whyThisPageMatters:
        "It gives client success a plain-language trade-off between certainty, upside, and operating obligations.",
    },
    revenue_analyst: {
      bridgeTitle: "Hedge economics bridge",
      decisionEyebrow: "Commercial structure decision",
      decisionTitle: "Which hedge structure improves the revenue case?",
      description:
        "Compare hedge structures against merchant upside, downside protection, availability obligations, and revenue given away so the commercial model stays honest.",
      eyebrow: "Commercial analytics OS",
      nextAction:
        "Feed the preferred hedge structure into revenue assurance, scenario analysis, and owner or investor evidence.",
      offerTitle: "Recommended commercial structure",
      optionsTitle: "Hedge structure comparison",
      title: "Hedge economics",
      whyThisPageMatters:
        "It quantifies the trade between protected revenue and merchant value given away by each hedge structure.",
    },
  };

  return frames[personaId] ?? defaults;
}

function formatContractRow(contract: HedgeContract): TableRow {
  return {
    ...contract,
    name: contract.name ?? contract.contract_name ?? "-",
  };
}
