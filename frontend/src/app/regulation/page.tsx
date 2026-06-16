"use client";

import { useQuery } from "@tanstack/react-query";

import {
  AssetDataProfileSection,
  buildAssetDataProfileEvidence,
} from "@/components/asset-data-profile-section";
import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { WorkspaceTabs } from "@/components/workspace-tabs";
import { apiGet } from "@/lib/api";
import { useState } from "react";
import type { PersonaId } from "@/lib/personas";
import type {
  AncillaryEligibilityResponse,
  EegComplianceResponse,
  GridFeeSensitivityResponse,
  JsonObject,
  RegulatorySummaryResponse,
  StorageClassificationResponse,
  TableRow,
} from "@/types/api";

const regulationTabs = [
  {
    id: "eligibility",
    label: "Eligibility",
    helper: "Regulatory decision inputs, automation gate, and client approval meaning.",
  },
  {
    id: "market-rules",
    label: "Market Rules",
    helper: "Storage classification, EEG checks, grid-fee sensitivity, and ancillary eligibility details.",
  },
  {
    id: "proof",
    label: "Evidence",
    helper: "Selected asset profile and mock-vs-production regulatory proof.",
  },
] as const;

type RegulationTabId = (typeof regulationTabs)[number]["id"];

export default function RegulationPage() {
  const { selectedAsset, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const isClientPersona = persona.layer === "client";
  const [activeTab, setActiveTab] = useState<RegulationTabId>("eligibility");
  const assetDataProfileEvidence = buildAssetDataProfileEvidence(selectedAsset);

  const regulatorySummary = useQuery({
    queryFn: () =>
      apiGet<RegulatorySummaryResponse>(
        `/assets/${selectedAssetId}/regulatory-summary`,
      ),
    queryKey: ["regulatory-summary", selectedAssetId],
  });

  const classification = useQuery({
    enabled: !isClientPersona,
    queryFn: () =>
      apiGet<StorageClassificationResponse>(
        `/assets/${selectedAssetId}/storage-classification`,
      ),
    queryKey: ["reg-storage-classification", selectedAssetId],
  });

  const eeg = useQuery({
    enabled: !isClientPersona,
    queryFn: () =>
      apiGet<EegComplianceResponse>(
        `/assets/${selectedAssetId}/eeg-compliance/latest`,
      ),
    queryKey: ["reg-eeg", selectedAssetId],
  });

  const gridFees = useQuery({
    enabled: !isClientPersona,
    queryFn: () =>
      apiGet<GridFeeSensitivityResponse>(
        `/assets/${selectedAssetId}/grid-fees/germany/sensitivity`,
      ),
    queryKey: ["reg-grid-fees", selectedAssetId],
  });

  const ancillary = useQuery({
    enabled: !isClientPersona,
    queryFn: () =>
      apiGet<AncillaryEligibilityResponse>(
        `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
      ),
    queryKey: ["reg-ancillary", selectedAssetId],
  });

  const classificationData =
    classification.data ?? regulatorySummary.data?.storage_classification;
  const eegData = eeg.data ?? regulatorySummary.data?.eeg_compliance;
  const ancillaryData =
    ancillary.data ?? regulatorySummary.data?.ancillary_eligibility;
  const backendRegulatoryKpis = normalizeProofKpis(
    regulatorySummary.data?.regulatory_proof?.kpis,
  );
  const visibleRegulatoryRows = regulatorySummary.data?.regulatory_proof?.rows ?? [];
  const gridFeeRows = gridFees.data?.sensitivity?.length
    ? gridFees.data.sensitivity
    : gridFees.data?.scenarios ?? [];
  const ancillaryRows = ancillaryData?.products ?? [];
  const formattedAncillaryRows = formatAncillaryRows(ancillaryRows);
  const blockedAncillaryRows = formattedAncillaryRows.filter(
    (row) =>
      row.eligibility_status === "not_eligible" ||
      row.blocking_reasons !== "-",
  );
  const reviewAncillaryRows = formattedAncillaryRows.filter(
    (row) => row.review_warnings !== "-",
  );
  const automationBlockers = uniqueStrings([
    ...(regulatorySummary.data?.blockers ?? []),
    eegData && !eegData.eeg_eligible && !(regulatorySummary.data?.blockers ?? []).length
      ? "EEG compliance is not eligible for automatic trading."
      : null,
    eegData?.mixed_origin_risk && !(regulatorySummary.data?.blockers ?? []).length
      ? "Mixed-origin or renewable-support risk needs compliance review."
      : null,
    !isClientPersona && blockedAncillaryRows.length
      ? `${blockedAncillaryRows.length} ancillary product(s) are blocked.`
      : null,
    !isClientPersona && reviewAncillaryRows.length
      ? `${reviewAncillaryRows.length} ancillary product(s) require review.`
      : null,
  ].filter(Boolean) as string[]);
  const framing = getRegulatoryPersonaFraming(personaId);
  const approvalStatus = automationBlockers.length
    ? "needs review"
    : "approval-ready";
  const primaryBlocker =
    automationBlockers[0] ?? "No regulatory blocker shown for the current evidence.";
  const ancillaryEligibleCount =
    regulatorySummary.data?.summary?.ancillary_eligible_count ??
    ancillaryData?.eligible_product_count ??
    ancillaryData?.eligible_products?.length ??
    (isClientPersona ? "not loaded" : 0);
  const ancillaryEligibilityStatus = ancillaryData
    ? `${ancillaryEligibleCount} eligible`
    : isClientPersona
      ? "internal detail"
      : "0 eligible";
  const ancillaryClientNextAction = ancillaryData
    ? Number(ancillaryEligibleCount)
      ? "Use eligible options in the market-readiness story."
      : "Do not promise ancillary revenue until eligibility is clear."
    : "Open internal compliance detail before making ancillary-market claims.";

  return (
    <>
      <PageHeading
        description={framing.pageDescription}
        eyebrow={framing.pageEyebrow}
        title={framing.pageTitle}
      />

      <DecisionBrief
        blockers={automationBlockers}
        className="mb-6"
        decision={
          <>
            {isClientPersona
              ? approvalStatus
              : automationBlockers.length
                ? "Review before auto-trade"
                : "Auto-trade eligible"}
            <span className="text-slate-500"> / </span>
            Germany
          </>
        }
        evidence={[
          `${framing.storageEvidenceLabel}: ${String(classificationData?.storage_classification ?? classificationData?.storage_mode ?? "-")}.`,
          `${framing.eegEvidenceLabel}: ${String(eegData?.status ?? "-")}.`,
          `${String(ancillaryEligibleCount)} ${framing.ancillaryEvidenceLabel}.`,
          `Asset type: ${String(selectedAsset?.asset_type ?? "-").replaceAll("_", " ")} / ${String(selectedAsset?.asset_subtype ?? "-").replaceAll("_", " ")}.`,
          ...assetDataProfileEvidence,
        ]}
        eyebrow={framing.decisionEyebrow}
        nextAction={
          automationBlockers.length
            ? framing.blockedNextAction
            : framing.clearNextAction
        }
        title={framing.decisionTitle}
        tone={automationBlockers.length ? "amber" : "emerald"}
      />

      {isClientPersona ? (
        <div className="mb-5 grid gap-4 md:grid-cols-3">
          <KpiCard
            accent={automationBlockers.length ? "amber" : "emerald"}
            helper={primaryBlocker}
            label="Approval readiness"
            value={approvalStatus}
          />
          <KpiCard
            accent={eegData?.eeg_eligible ? "emerald" : "amber"}
            helper="EEG and renewable-origin evidence."
            label="Compliance status"
            value={String(eegData?.status ?? "-")}
          />
          <KpiCard
            accent={ancillaryData ? (Number(ancillaryEligibleCount) ? "emerald" : "amber") : "blue"}
            helper={
              ancillaryData
                ? "Eligible market options for the asset."
                : "Detailed market eligibility loads in internal compliance views."
            }
            label="Market eligibility"
            value={String(ancillaryEligibleCount)}
          />
        </div>
      ) : (
        <div className="mb-5 grid gap-4 md:grid-cols-4">
          <KpiCard
            label="Storage mode"
            value={String(
              classificationData?.storage_classification ??
                classificationData?.storage_mode ??
                "-",
            )}
          />
          <KpiCard accent="amber" label="EEG status" value={String(eegData?.status ?? "-")} />
          <KpiCard
            label="Ancillary eligible"
            value={String(ancillaryEligibleCount || "-")}
            helper="Product count"
          />
          <KpiCard accent="blue" label="Country" value="Germany" />
        </div>
      )}

      <WorkspaceTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={regulationTabs}
      />

      {activeTab === "eligibility" ? (
        <div className="space-y-5">
          <SectionCard title={framing.bridgeTitle}>
            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <DataTable
                columns={["decision_input", "value"]}
                rows={[
                  {
                    decision_input: "Country rulebook",
                    value: "Germany",
                  },
                  {
                    decision_input: "Automation gate",
                    value: automationBlockers.length
                      ? isClientPersona
                        ? "needs review before approval"
                        : "blocked for live automation"
                      : isClientPersona
                        ? "ready for approval narrative"
                        : "eligible for automated route selection",
                  },
                  {
                    decision_input: isClientPersona ? "Open approval blockers" : "Regulatory blockers",
                    value: automationBlockers.length,
                  },
                  {
                    decision_input: "Why this page matters",
                    value: framing.whyItMatters,
                  },
                ]}
              />
              {isClientPersona ? (
                <DataTable
                  columns={["approval_area", "status", "client_meaning", "next_action"]}
                  rows={[
                    {
                      approval_area: "Asset classification",
                      client_meaning: "Defines how the asset may participate in German markets.",
                      next_action: "Use this classification in the client approval narrative.",
                      status:
                        classificationData?.storage_classification ??
                        classificationData?.storage_mode ??
                        "not loaded",
                    },
                    {
                      approval_area: "EEG and origin risk",
                      client_meaning: "Shows whether renewable-support or mixed-origin risk needs review.",
                      next_action: eegData?.eeg_eligible
                        ? "Include as supporting compliance evidence."
                        : "Resolve EEG finding before presenting as approval-ready.",
                      status: eegData?.status ?? "not loaded",
                    },
                    {
                      approval_area: "Market eligibility",
                      client_meaning: "Shows which market options can be discussed with the client.",
                      next_action: ancillaryClientNextAction,
                      status: ancillaryEligibilityStatus,
                    },
                  ]}
                />
              ) : (
                <DataTable
                  columns={["capability", "backend_route", "status", "business_value"]}
                  rows={[
                    {
                      backend_route: `/assets/${selectedAssetId}/storage-classification`,
                      business_value: "Classifies the asset before market-route selection.",
                      capability: "Storage classification",
                      status:
                        classificationData?.storage_classification ??
                        classificationData?.storage_mode ??
                        "not loaded",
                    },
                    {
                      backend_route: `/assets/${selectedAssetId}/eeg-compliance/latest`,
                      business_value:
                        "Blocks renewable-support or mixed-origin logic before automated bids.",
                      capability: "EEG compliance",
                      status: eegData?.status ?? "not loaded",
                    },
                    {
                      backend_route: `/assets/${selectedAssetId}/grid-fees/germany/sensitivity`,
                      business_value: "Tests tariff economics before dispatch approval.",
                      capability: "Grid fee sensitivity",
                      status: `${gridFeeRows.length} scenario(s)`,
                    },
                    {
                      backend_route: `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
                      business_value:
                        "Allows reserve-market bidding only for cleared products.",
                      capability: "Ancillary eligibility",
                      status: `${ancillaryEligibleCount} eligible`,
                    },
                  ]}
                />
              )}
            </div>
          </SectionCard>

          <SectionCard title="Automation gate summary">
            <DataTable
              columns={["gate", "status", "automation_use"]}
              rows={[
                {
                  automation_use: "Select tradable market routes",
                  gate: "Storage classification",
                  status:
                    classificationData?.storage_classification ??
                    classificationData?.storage_mode ??
                    "-",
                },
                {
                  automation_use: "Block unsupported renewable-support logic",
                  gate: "EEG compliance",
                  status: eegData?.eeg_eligible ? "eligible" : eegData?.status ?? "-",
                },
                {
                  automation_use: "Allow ancillary-market bidding only for cleared products",
                  gate: "Ancillary eligibility",
                  status: ancillaryEligibilityStatus,
                },
                {
                  automation_use: "Apply tariff economics before dispatch approval",
                  gate: "Grid fee sensitivity",
                  status: isClientPersona ? "internal detail" : `${gridFeeRows.length} scenario(s)`,
                },
              ]}
            />
          </SectionCard>
        </div>
      ) : null}

      {activeTab === "market-rules" ? (
        <div className="grid gap-5 xl:grid-cols-2">
          <SectionCard title="Storage classification detail">
            <DataTable
              columns={["field", "value"]}
              rows={storageRows(classificationData)}
            />
          </SectionCard>

          <SectionCard title="EEG and green colocation checks">
            <DataTable
              columns={["field", "value"]}
              rows={eegRows(eegData)}
            />
          </SectionCard>

          {!isClientPersona ? (
            <>
              <SectionCard title="Grid fee sensitivity">
                <DataTable
                  columns={[
                    "grid_fee_scenario",
                    "import_grid_fee_eur_per_mwh",
                    "capacity_charge_eur_per_mw_year",
                    "annualized_grid_fee_cost_eur",
                    "description",
                  ]}
                  rows={gridFeeRows.slice(0, 6)}
                />
              </SectionCard>

              <SectionCard title="Ancillary eligibility">
                <DataTable
                  columns={[
                    "product_id",
                    "eligibility_status",
                    "automation_gate",
                    "market_requirement",
                    "next_action",
                  ]}
                  rows={formatAncillaryGateRows(formattedAncillaryRows).slice(0, 6)}
                />
              </SectionCard>
            </>
          ) : null}
        </div>
      ) : null}

      {activeTab === "proof" ? (
        <div className="space-y-5">
          <AssetDataProfileSection
            asset={selectedAsset}
            title="Selected regulatory asset profile"
          />

          <SectionCard
            action={<StatusPill tone="blue">{selectedAsset?.data_mode ?? "mock"} regulatory proof</StatusPill>}
            title="Asset regulatory proof"
          >
            <div className="mb-4 grid gap-4 md:grid-cols-3">
              {backendRegulatoryKpis.map((kpi) => (
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
              columns={["regulatory_driver", "mock_evidence", "investor_meaning", "production_upgrade"]}
              rows={visibleRegulatoryRows}
            />
          </SectionCard>
        </div>
      ) : null}
    </>
  );
}

function storageRows(value?: StorageClassificationResponse): TableRow[] {
  if (!value) {
    return [];
  }

  return objectToRows({
    status: value.status,
    storage_mode: value.storage_mode,
    storage_classification: value.storage_classification,
    market_participation_mode: value.market_participation_mode,
    charges_from_grid: value.charges_from_grid,
    charges_from_renewables: value.charges_from_renewables,
    exports_stored_renewable_power: value.exports_stored_renewable_power,
    uses_eeg_support: value.uses_eeg_support,
    eeg_support_risk: value.eeg_support_risk,
    metering_concept: value.metering_concept,
    warnings: formatList(value.warnings),
  });
}

function eegRows(value?: EegComplianceResponse): TableRow[] {
  if (!value) {
    return [];
  }

  return objectToRows({
    status: value.status,
    eeg_eligible: value.eeg_eligible,
    green_colocation: value.green_colocation,
    mixed_origin_risk: value.mixed_origin_risk,
    eeg_support_risk: value.eeg_support_risk,
    compliance_notes: formatList(value.compliance_notes),
    findings: formatList(value.findings),
    recommended_actions: formatList(value.recommended_actions),
  });
}

function objectToRows(value: JsonObject): TableRow[] {
  return Object.entries(value)
    .filter(([, rowValue]) => rowValue !== undefined)
    .map(([field, rowValue]) => ({
      field,
      value: rowValue,
    }));
}

type RegulatoryProofKpi = {
  accent: "amber" | "blue" | "emerald" | "red" | "slate";
  helper: string;
  label: string;
  value: React.ReactNode;
};

function normalizeProofKpis(rows?: TableRow[]): RegulatoryProofKpi[] {
  return (rows ?? []).map((row) => ({
    accent: normalizeAccent(row.accent),
    helper: String(row.helper ?? ""),
    label: String(row.label ?? "Evidence"),
    value: normalizeKpiValue(row.value),
  }));
}

function normalizeAccent(value: unknown): RegulatoryProofKpi["accent"] {
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

function formatAncillaryRows(rows: TableRow[]): TableRow[] {
  return rows.map((row) => ({
    ...row,
    blocking_reasons: formatList(row.blocking_reasons),
    review_warnings: formatList(row.review_warnings),
  }));
}

function formatAncillaryGateRows(rows: TableRow[]): TableRow[] {
  return rows.map((row) => {
    const blocked = row.eligibility_status === "not_eligible" || row.blocking_reasons !== "-";
    const review = row.review_warnings !== "-";

    return {
      automation_gate: blocked ? "blocked" : review ? "review" : "eligible",
      eligibility_status: row.eligibility_status ?? "-",
      market_requirement:
        row.name ??
        `${row.minimum_duration_minutes ?? "-"} min / ${row.response_time_seconds ?? "-"} sec`,
      next_action: blocked
        ? row.blocking_reasons
        : review
          ? row.review_warnings
          : "Can be considered for automated route selection.",
      product_id: row.product_id ?? "-",
    };
  });
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}

function getRegulatoryPersonaFraming(personaId: PersonaId) {
  const defaultFraming = {
    ancillaryEvidenceLabel: "ancillary product(s) eligible",
    blockedNextAction: "Clear the regulatory blockers before allowing unattended bid submission.",
    bridgeTitle: "Regulatory-to-automation bridge",
    clearNextAction: "Use this regulatory clearance as a pre-trade automation gate for German market routes.",
    decisionEyebrow: "Regulatory automation gate",
    decisionTitle: "German eligibility decision",
    eegEvidenceLabel: "EEG status",
    pageDescription:
      "Prove whether the selected German asset can be used for automated trading by checking storage classification, EEG origin risk, grid-fee exposure, and ancillary-service eligibility.",
    pageEyebrow: "Germany regulatory layer",
    pageTitle: "Regulatory compliance",
    storageEvidenceLabel: "Storage classification",
    whyItMatters:
      "It prevents the platform from submitting bids where EEG, storage classification, grid-fee, or ancillary eligibility evidence is incomplete.",
  };

  const personaFraming: Partial<Record<PersonaId, typeof defaultFraming>> = {
    project_developer: {
      ancillaryEvidenceLabel: "reserve-market option(s) available for development planning",
      blockedNextAction: "Resolve pre-COD regulatory blockers before using this asset in the investment case.",
      bridgeTitle: "Development-readiness bridge",
      clearNextAction: "Use this clearance as development evidence for market access, financing, and COD planning.",
      decisionEyebrow: "Development eligibility gate",
      decisionTitle: "Pre-COD regulatory readiness",
      eegEvidenceLabel: "Development EEG risk",
      pageDescription:
        "Check whether the German asset has the regulatory, market, and grid-fee assumptions needed before COD, financing, or market-access planning.",
      pageEyebrow: "Development compliance",
      pageTitle: "Development regulatory readiness",
      storageEvidenceLabel: "Development storage classification",
      whyItMatters:
        "It prevents the project from carrying unsupported market-access, EEG, or grid-fee assumptions into financing and COD planning.",
    },
    investor_lender: {
      ancillaryEvidenceLabel: "bankability-relevant ancillary option(s) eligible",
      blockedNextAction: "Resolve legal and eligibility gaps before presenting this asset as bankable.",
      bridgeTitle: "Bankability risk bridge",
      clearNextAction: "Use this clearance as regulatory evidence in the investment or lending packet.",
      decisionEyebrow: "Bankability gate",
      decisionTitle: "Regulatory bankability decision",
      eegEvidenceLabel: "Legal-risk status",
      pageDescription:
        "Translate storage classification, EEG exposure, grid fees, and market eligibility into bankability and legal-risk evidence for investors or lenders.",
      pageEyebrow: "Investment compliance",
      pageTitle: "Regulatory bankability",
      storageEvidenceLabel: "Bankability classification",
      whyItMatters:
        "It shows whether revenue assumptions are legally and commercially supportable before diligence or lending review.",
    },
    risk_compliance: {
      ancillaryEvidenceLabel: "ancillary control(s) eligible",
      blockedNextAction: "Clear governance blockers before approving automation or client reporting.",
      bridgeTitle: "Operating compliance bridge",
      clearNextAction: "Use this clearance as the compliance gate before automation mode escalation.",
      decisionEyebrow: "Operating compliance gate",
      decisionTitle: "Can this asset operate compliantly?",
      eegEvidenceLabel: "Compliance status",
      pageDescription:
        "Review whether storage classification, EEG origin risk, grid-fee exposure, and ancillary eligibility support compliant operation and automation approval.",
      pageEyebrow: "Operating compliance",
      pageTitle: "Compliance gate",
      storageEvidenceLabel: "Operating classification",
      whyItMatters:
        "It keeps automation, reporting, and market participation inside approved regulatory and operating assumptions.",
    },
    executive: {
      ancillaryEvidenceLabel: "market expansion option(s) available",
      blockedNextAction: "Treat regulatory readiness as a management blocker before promising automated trading.",
      bridgeTitle: "Management readiness bridge",
      clearNextAction: "Use this clearance as management evidence that the German asset can progress.",
      decisionEyebrow: "Executive readiness gate",
      decisionTitle: "Is regulatory readiness blocking value?",
      eegEvidenceLabel: "Readiness status",
      pageDescription:
        "Summarize whether German regulatory assumptions, tariff exposure, and market eligibility create a major blocker for management decisions.",
      pageEyebrow: "Executive compliance view",
      pageTitle: "Regulatory readiness",
      storageEvidenceLabel: "Readiness classification",
      whyItMatters:
        "It gives management a high-level blocked-or-clear view of legal and market eligibility risks.",
    },
    asset_owner: {
      ancillaryEvidenceLabel: "owner revenue option(s) eligible",
      blockedNextAction: "Resolve regulatory blockers before presenting the asset as owner-ready for automated trading.",
      bridgeTitle: "Owner readiness bridge",
      clearNextAction: "Use this clearance to support owner reporting and market-route confidence.",
      decisionEyebrow: "Owner readiness gate",
      decisionTitle: "Can the owner rely on this asset's market eligibility?",
      eegEvidenceLabel: "Owner compliance status",
      pageDescription:
        "Explain whether German regulatory evidence supports owner value, market participation, and safe automation claims.",
      pageEyebrow: "Owner compliance view",
      pageTitle: "Owner regulatory readiness",
      storageEvidenceLabel: "Owner asset classification",
      whyItMatters:
        "It prevents owner-facing revenue claims from relying on incomplete EEG, grid-fee, or eligibility evidence.",
    },
    client_success: {
      ancillaryEvidenceLabel: "client-explainable market option(s) eligible",
      blockedNextAction: "Explain the open regulatory blocker before sharing automation or revenue claims with the client.",
      bridgeTitle: "Client explanation bridge",
      clearNextAction: "Use this clearance in the client report and next-action narrative.",
      decisionEyebrow: "Client readiness gate",
      decisionTitle: "Can this regulatory story be explained to the client?",
      eegEvidenceLabel: "Client-facing compliance status",
      pageDescription:
        "Turn German regulatory checks into a clear client explanation of what is ready, what is blocked, and what must happen next.",
      pageEyebrow: "Client compliance explanation",
      pageTitle: "Client regulatory evidence",
      storageEvidenceLabel: "Client-facing classification",
      whyItMatters:
        "It gives client success a defensible explanation of regulatory readiness, blockers, and next actions.",
    },
  };

  return personaFraming[personaId] ?? defaultFraming;
}

function formatList(value: unknown) {
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
