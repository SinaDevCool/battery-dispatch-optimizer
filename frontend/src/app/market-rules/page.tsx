"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief, type DecisionBriefTone } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import type {
  AncillaryEligibilityResponse,
  ApiEnvelope,
  AutomationControlStatusResponse,
  EligibleProductsResponse,
  MarketConnectorReadinessResponse,
  MarketAdapterRegistryResponse,
  TableRow,
} from "@/types/api";

type MarketProductsResponse = ApiEnvelope<{
  product_count?: number;
  products?: TableRow[];
}>;

const marketRuleCatalog = [
  {
    adapter_id: "epex_day_ahead",
    automation_blocker: "Live EPEX route and credential validation are required before automated submission.",
    gate_closure: "Indicative D-1 12:00 Europe/Berlin",
    market_rule: "Build hourly or 15-minute limit orders before day-ahead auction gate closure.",
    product_timing: "Day-ahead delivery schedule",
    submission_mode: "preview_only",
  },
  {
    adapter_id: "epex_intraday_auction",
    automation_blocker: "Intraday auction product mapping and gate-closure validation must be connected.",
    gate_closure: "Indicative D-1 15:00 Europe/Berlin",
    market_rule: "Submit 15-minute intraday auction orders before the auction gate.",
    product_timing: "15-minute auction products",
    submission_mode: "preview_only",
  },
  {
    adapter_id: "epex_intraday_continuous",
    automation_blocker: "Live order book, spread, partial-fill, and cancel/replace controls are required.",
    gate_closure: "Continuous trading requires live time-to-delivery/session checks",
    market_rule: "Use continuous rebalancing only with liquidity and slippage controls.",
    product_timing: "15-minute and hourly continuous products",
    submission_mode: "preview_only",
  },
  {
    adapter_id: "regelleistung_fcr",
    automation_blocker: "FCR prequalification, telemetry, symmetric capacity, and TSO settlement evidence required.",
    gate_closure: "Capacity tender timing must be connected from regelleistung.net",
    market_rule: "Reserve symmetric power and SOC headroom for minimum FCR duration.",
    product_timing: "FCR capacity blocks",
    submission_mode: "preview_only",
  },
  {
    adapter_id: "regelleistung_afrr",
    automation_blocker: "aFRR prequalification, activation telemetry, capacity reservation, and activation accounting required.",
    gate_closure: "Capacity and energy tender timing must be connected from regelleistung.net",
    market_rule: "Validate positive/negative capacity and activation-energy placeholders before automation.",
    product_timing: "aFRR capacity and activation-energy products",
    submission_mode: "preview_only",
  },
  {
    adapter_id: "regelleistung_mfrr",
    automation_blocker: "mFRR qualification, activation workflow, manual dispatch evidence, and imbalance settlement rules required.",
    gate_closure: "Capacity and energy tender timing must be connected from regelleistung.net",
    market_rule: "Validate positive/negative manual reserve and activation workflow before automation.",
    product_timing: "mFRR capacity and activation-energy products",
    submission_mode: "preview_only",
  },
];

export default function MarketRulesPage() {
  const { selectedAssetId } = useAssetContext();

  const adapters = useQuery({
    queryFn: () =>
      apiGet<MarketAdapterRegistryResponse>(
        "/execution/market-adapters?country=Germany",
      ),
    queryKey: ["market-rules-adapters"],
  });

  const connectorReadiness = useQuery({
    queryFn: () =>
      apiGet<MarketConnectorReadinessResponse>(
        "/execution/market-connectors/readiness?country=Germany",
      ),
    queryKey: ["market-rules-connector-readiness"],
  });

  const automationControl = useQuery({
    queryFn: () =>
      apiGet<AutomationControlStatusResponse>(
        `/assets/${selectedAssetId}/execution/automation-control/status`,
      ),
    queryKey: ["market-rules-automation-control", selectedAssetId],
  });

  const eligibleProducts = useQuery({
    queryFn: () =>
      apiGet<EligibleProductsResponse>(
        `/assets/${selectedAssetId}/eligible-products`,
      ),
    queryKey: ["market-rules-eligible-products", selectedAssetId],
  });

  const ancillary = useQuery({
    queryFn: () =>
      apiGet<AncillaryEligibilityResponse>(
        `/assets/${selectedAssetId}/ancillary/germany/eligibility`,
      ),
    queryKey: ["market-rules-ancillary", selectedAssetId],
  });

  const products = useQuery({
    queryFn: () =>
      apiGet<MarketProductsResponse>("/markets/products?country=Germany"),
    queryKey: ["market-rules-products"],
  });

  const ruleRows = useMemo(
    () =>
      buildRuleRows({
        adapters: adapters.data?.adapters ?? [],
        connectors:
          connectorReadiness.data?.connectors ??
          connectorReadiness.data?.integrations ??
          [],
      }),
    [
      adapters.data?.adapters,
      connectorReadiness.data?.connectors,
      connectorReadiness.data?.integrations,
    ],
  );
  const routeSummaryRows = useMemo(() => buildRouteSummaryRows(ruleRows), [ruleRows]);
  const routeUnlockRows = useMemo(() => buildRouteUnlockRows(ruleRows), [ruleRows]);
  const productRows = useMemo(
    () => normalizeProductRows(products.data?.products ?? []),
    [products.data?.products],
  );
  const eligibleProductRows = useMemo(
    () => normalizeEligibleProductRows(eligibleProducts.data?.products ?? []),
    [eligibleProducts.data?.products],
  );
  const previewOnlyCount = ruleRows.filter(
    (row) => row.live_submission === false,
  ).length;
  const missingCredentialCount = ruleRows.filter(
    (row) => row.credential_status === "missing",
  ).length;
  const blockedProductCount = eligibleProductRows.filter(
    (row) => row.eligibility_status === "not_eligible" || row.eligibility_status === "blocked",
  ).length;
  const decisionBrief = useMemo(
    () =>
      buildMarketRulesDecisionBrief({
        ancillary: ancillary.data,
        automationControl: automationControl.data,
        blockedProductCount,
        connectorReadiness: connectorReadiness.data,
        eligibleProductCount: eligibleProducts.data?.eligible_product_count,
        missingCredentialCount,
        previewOnlyCount,
        ruleRows,
      }),
    [
      ancillary.data,
      automationControl.data,
      blockedProductCount,
      connectorReadiness.data,
      eligibleProducts.data?.eligible_product_count,
      missingCredentialCount,
      previewOnlyCount,
      ruleRows,
    ],
  );
  const backendConnectionRows = useMemo(
    () =>
      buildMarketRulesBackendRows({
        assetId: selectedAssetId,
        ancillary: ancillary.data,
        automationControl: automationControl.data,
        connectorReadiness: connectorReadiness.data,
        eligibleProductCount: eligibleProducts.data?.eligible_product_count,
        productCount: products.data?.product_count ?? productRows.length,
        ruleCount: ruleRows.length,
      }),
    [
      ancillary.data,
      automationControl.data,
      connectorReadiness.data,
      eligibleProducts.data?.eligible_product_count,
      productRows.length,
      products.data?.product_count,
      ruleRows.length,
      selectedAssetId,
    ],
  );

  return (
    <>
      <PageHeading
        description="Decide which EPEX and regelleistung routes can receive automated orders, which routes are still preview-only, and which credentials, timing, prequalification, or connector checks block escalation."
        eyebrow="Market intelligence"
        title="Market access rules"
      />

      <div className="mb-6">
        <DecisionBrief
          action={
            <Link
              className="rounded-md border border-sky-400/35 bg-sky-400/10 px-3 py-2 text-sm font-semibold text-sky-100 transition hover:border-sky-300 hover:bg-sky-400/20"
              href={decisionBrief.actionHref}
            >
              {decisionBrief.actionLabel}
            </Link>
          }
          blockers={decisionBrief.blockers}
          decision={decisionBrief.decision}
          evidence={decisionBrief.evidence}
          eyebrow="Market eligibility gate"
          nextAction={decisionBrief.nextAction}
          tone={decisionBrief.tone}
          title="Which market route can automation trade?"
        />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent="blue"
          helper="Germany market adapters"
          label="Market routes"
          value={ruleRows.length}
        />
        <KpiCard
          accent={previewOnlyCount ? "amber" : "emerald"}
          helper="Live submission disabled until connectors are validated"
          label="Preview-only routes"
          value={previewOnlyCount}
        />
        <KpiCard
          accent={missingCredentialCount ? "amber" : "emerald"}
          helper="Credential and member/broker setup required"
          label="Missing credentials"
          value={missingCredentialCount}
        />
        <KpiCard
          accent="blue"
          helper="Registered German tradable products"
          label="Products"
          value={products.data?.product_count ?? productRows.length}
        />
      </div>

      <SectionCard
        action={<StatusPill tone={decisionBrief.tone}>{decisionBrief.actionLabel}</StatusPill>}
        title="Market access bridge"
      >
        <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(420px,1.1fr)]">
          <DataTable
            columns={["decision_input", "value"]}
            rows={[
              {
                decision_input: "Live route candidate",
                value: ruleRows.some((row) => row.live_submission === true)
                  ? `${ruleRows.filter((row) => row.live_submission === true).length} route(s)`
                  : "none yet",
              },
              {
                decision_input: "Paper or preview routes",
                value: `${previewOnlyCount} route(s) need controlled escalation`,
              },
              {
                decision_input: "Credential blockers",
                value: `${missingCredentialCount} route(s) need exchange or TSO credentials`,
              },
              {
                decision_input: "Primary unlock",
                value:
                  decisionBrief.blockers[0] ??
                  "Feed eligible routes into market allocation before proposal generation.",
              },
            ]}
          />
          <DataTable
            columns={["capability", "backend_route", "status", "business_value"]}
            rows={backendConnectionRows}
          />
        </div>
      </SectionCard>

      <SectionCard
        action={<StatusPill tone="amber">Automation gate checks</StatusPill>}
        title="Route automation gates"
      >
        <DataTable
          columns={[
            "adapter_id",
            "venue",
            "market_segment",
            "automation_mode",
            "readiness_score",
            "next_gate",
          ]}
          rows={routeSummaryRows}
        />
      </SectionCard>

      <SectionCard
        action={<StatusPill tone={missingCredentialCount || previewOnlyCount ? "amber" : "emerald"}>Unlock plan</StatusPill>}
        title="Route unlock plan"
      >
        <DataTable
          columns={[
            "adapter_id",
            "automation_lane",
            "blocks_live",
            "next_unlock",
            "business_value",
          ]}
          rows={routeUnlockRows}
        />
      </SectionCard>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard title="Product constraints">
          <DataTable
            columns={[
              "product_id",
              "product_name",
              "market",
              "minimum_power_mw",
              "requires_prequalification",
            ]}
            rows={productRows.slice(0, 8)}
          />
        </SectionCard>

        <SectionCard title="Automation readiness rules">
          <div className="space-y-3">
            <MarketRuleRow
              label="EPEX live route"
              tone={missingCredentialCount ? "amber" : "emerald"}
              value={missingCredentialCount ? "credentials required" : "ready"}
            />
            <MarketRuleRow
              label="Order timing"
              tone="amber"
              value="live exchange session checks required"
            />
            <MarketRuleRow
              label="Reserve prequalification"
              tone="amber"
              value="asset-specific TSO evidence required"
            />
            <MarketRuleRow
              label="Automation mode"
              tone={previewOnlyCount ? "amber" : "emerald"}
              value={previewOnlyCount ? "preview/paper first" : "live candidate"}
            />
          </div>
        </SectionCard>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={blockedProductCount ? "amber" : "emerald"}>{eligibleProductRows.length}</StatusPill>}
          title="Asset-specific product eligibility"
        >
          <DataTable
            columns={[
              "product_id",
              "product_name",
              "market",
              "eligibility_status",
              "automation_gate",
            ]}
            rows={eligibleProductRows.slice(0, 8)}
          />
        </SectionCard>

        <SectionCard title="EPEX vs ancillary automation contract">
          <div className="space-y-3">
            <MarketRuleRow
              label="EPEX wholesale"
              tone={epexTone(ruleRows)}
              value={epexReadinessLabel(ruleRows)}
            />
            <MarketRuleRow
              label="Ancillary services"
              tone={ancillary.data?.eligible ? "emerald" : "amber"}
              value={ancillary.data?.eligible ? "eligible" : ancillary.data?.reason ?? "prequalification required"}
            />
            <MarketRuleRow
              label="Connector readiness"
              tone={connectorReadiness.data?.connector_status === "production_ready" ? "emerald" : "amber"}
              value={connectorReadiness.data?.connector_status ?? "not evaluated"}
            />
            <MarketRuleRow
              label="Automation control"
              tone={automationControl.data?.live_trading_allowed ? "emerald" : automationControl.data?.paper_trading_allowed ? "blue" : "amber"}
              value={automationControl.data?.automation_status ?? automationControl.data?.automation_mode ?? "not evaluated"}
            />
          </div>
        </SectionCard>
      </div>
    </>
  );
}

function buildRuleRows({
  adapters,
  connectors,
}: {
  adapters: NonNullable<MarketAdapterRegistryResponse["adapters"]>;
  connectors: NonNullable<MarketConnectorReadinessResponse["connectors"]>;
}) {
  const connectorById = new Map(
    connectors.map((connector) => [connector.adapter_id, connector]),
  );

  return adapters
    .filter((adapter) => adapter.environment !== "paper" && adapter.environment !== "demo")
    .map((adapter) => {
      const rule = marketRuleCatalog.find(
        (item) => item.adapter_id === adapter.adapter_id,
      );
      const connector = connectorById.get(adapter.adapter_id);
      const missingCredentials =
        connector?.missing_credentials?.length
          ? `Missing ${connector.missing_credentials.join(", ")}`
          : null;
      const missingControls =
        connector?.missing_controls?.length
          ? `Missing ${connector.missing_controls.join(", ")}`
          : null;

      return {
        ...adapter,
        automation_blocker:
          missingCredentials ??
          missingControls ??
          connector?.next_integration_action ??
          rule?.automation_blocker ??
          adapter.next_connection_action,
        automation_scope: connector?.automation_blocking_level ?? "preview_only",
        gate_closure: rule?.gate_closure ?? "Connector-specific gate timing required",
        market_rule: rule?.market_rule ?? adapter.next_connection_action,
        next_integration_action: connector?.next_integration_action,
        paper_supported: connector?.paper_supported,
        product_timing: rule?.product_timing ?? "-",
        readiness_score: connector?.readiness_score ?? "-",
        submission_mode: adapter.live_submission ? "live_enabled" : rule?.submission_mode ?? "preview_only",
        supported_granularity: (adapter.supported_granularity ?? []).join(", "),
      };
    });
}

function normalizeProductRows(rows: TableRow[]) {
  return rows.map((row) => ({
    ...row,
    product_name: row.product_name ?? row.name ?? "-",
    requires_prequalification: row.requires_prequalification ?? false,
  }));
}

function normalizeEligibleProductRows(
  rows: NonNullable<EligibleProductsResponse["products"]>,
) {
  return rows.map((row) => {
    const product = row.product ?? {};

    return {
      automation_gate:
        row.eligibility_status === "eligible"
          ? "eligible for allocation"
          : row.eligibility_status === "review_required"
            ? "review before automation"
            : formatList(row.blocking_reasons),
      blocking_reasons: formatList(row.blocking_reasons),
      eligibility_status: row.eligibility_status ?? "-",
      market: product.market ?? row.market ?? "-",
      product_id: product.product_id ?? row.product_id ?? "-",
      product_name: product.product_name ?? row.product_name ?? "-",
      review_warnings: formatList(row.review_warnings),
    };
  });
}

function buildRouteSummaryRows(rows: ReturnType<typeof buildRuleRows>) {
  return rows.map((row) => ({
    adapter_id: row.adapter_id,
    automation_mode: row.live_submission ? "live enabled" : row.submission_mode,
    market_segment: row.market_segment,
    next_gate: row.automation_blocker,
    readiness_score: row.readiness_score,
    venue: row.venue,
  }));
}

function buildRouteUnlockRows(rows: ReturnType<typeof buildRuleRows>) {
  return rows.map((row) => {
    const isEpex = String(row.adapter_id).startsWith("epex_");
    const hasCredentialGap = row.credential_status === "missing";
    const hasControlGap = row.automation_scope === "blocked";

    return {
      adapter_id: row.adapter_id,
      automation_lane: row.live_submission
        ? "live enabled"
        : row.paper_supported
          ? "paper-ready, live gated"
          : row.submission_mode,
      blocks_live: hasCredentialGap || hasControlGap ? row.automation_blocker : row.gate_closure,
      business_value: isEpex
        ? "wholesale spot bid submission and intraday repricing"
        : "reserve capacity access, activation readiness, and TSO settlement evidence",
      next_unlock:
        row.next_integration_action ??
        row.next_connection_action ??
        row.automation_blocker ??
        "Validate connector, credential, timing, and order controls.",
    };
  });
}

function buildMarketRulesBackendRows({
  assetId,
  ancillary,
  automationControl,
  connectorReadiness,
  eligibleProductCount,
  productCount,
  ruleCount,
}: {
  assetId: string;
  ancillary?: AncillaryEligibilityResponse;
  automationControl?: AutomationControlStatusResponse;
  connectorReadiness?: MarketConnectorReadinessResponse;
  eligibleProductCount?: number;
  productCount: number;
  ruleCount: number;
}) {
  return [
    {
      backend_route: "/execution/market-adapters?country=Germany",
      business_value: "Maps the actual EPEX and regelleistung execution routes.",
      capability: "Market route registry",
      status: `${ruleCount} route(s)`,
    },
    {
      backend_route: "/execution/market-connectors/readiness?country=Germany",
      business_value: "Shows whether routes are preview, paper, supervised, or live-ready.",
      capability: "Connector readiness",
      status: connectorReadiness?.connector_status ?? "not evaluated",
    },
    {
      backend_route: `/assets/${assetId}/eligible-products`,
      business_value: "Prevents allocation into products the asset cannot trade.",
      capability: "Asset product eligibility",
      status: `${eligibleProductCount ?? 0} eligible`,
    },
    {
      backend_route: `/assets/${assetId}/ancillary/germany/eligibility`,
      business_value: "Separates EPEX merchant trading from reserve-market prequalification.",
      capability: "Ancillary eligibility",
      status: ancillary?.eligible ? "eligible" : ancillary?.reason ?? "not confirmed",
    },
    {
      backend_route: `/assets/${assetId}/execution/automation-control/status`,
      business_value: "Stops live trading until approval, guardrails, telemetry, and settlement checks pass.",
      capability: "Automation control",
      status:
        automationControl?.automation_status ??
        automationControl?.automation_mode ??
        "not evaluated",
    },
    {
      backend_route: "/markets/products?country=Germany",
      business_value: "Defines the product universe used by revenue stack and market allocation.",
      capability: "Product catalog",
      status: `${productCount} product(s)`,
    },
  ];
}

function buildMarketRulesDecisionBrief({
  ancillary,
  automationControl,
  blockedProductCount,
  connectorReadiness,
  eligibleProductCount,
  missingCredentialCount,
  previewOnlyCount,
  ruleRows,
}: {
  ancillary?: AncillaryEligibilityResponse;
  automationControl?: AutomationControlStatusResponse;
  blockedProductCount: number;
  connectorReadiness?: MarketConnectorReadinessResponse;
  eligibleProductCount?: number;
  missingCredentialCount: number;
  previewOnlyCount: number;
  ruleRows: ReturnType<typeof buildRuleRows>;
}) {
  const blockers: string[] = [];
  const summary = connectorReadiness?.summary ?? {};
  const liveBlockingCount = Number(summary.live_auto_blocking_count ?? 0);

  if (missingCredentialCount > 0) {
    blockers.push(`${missingCredentialCount} market route(s) still need exchange credentials.`);
  }

  if (previewOnlyCount > 0) {
    blockers.push(`${previewOnlyCount} route(s) remain preview-only before live submission.`);
  }

  if (!ancillary?.eligible) {
    blockers.push(ancillary?.reason ?? "Ancillary prequalification is not confirmed.");
  }

  if (blockedProductCount > 0) {
    blockers.push(`${blockedProductCount} asset product(s) are blocked or not eligible.`);
  }

  for (const blocker of automationControl?.blockers ?? []) {
    blockers.push(
      String(
        blocker.message ??
          blocker.required_action ??
          blocker.label ??
          "Automation control blocker",
      ),
    );
  }

  const hasLiveRoute = ruleRows.some((row) => row.live_submission === true);
  const tone: DecisionBriefTone = automationControl?.live_trading_allowed
    ? "emerald"
    : automationControl?.supervised_trading_allowed || automationControl?.paper_trading_allowed
      ? "blue"
      : blockers.length
        ? "amber"
        : "slate";

  return {
    actionHref: blockers.length ? "/execution/market-connectors" : "/execution/market-allocation",
    actionLabel: blockers.length ? "Open market access" : "Allocate markets",
    blockers: blockers.slice(0, 4),
    decision: automationControl?.live_trading_allowed
      ? "At least one market route is eligible for live automated trading."
      : automationControl?.supervised_trading_allowed
        ? "Markets can support supervised automation, but live auto remains gated."
        : automationControl?.paper_trading_allowed
          ? "Keep market execution in paper mode until connector and eligibility gates clear."
          : "Market rules currently block automated trading escalation.",
    evidence: [
      `${ruleRows.length} German market route(s) mapped across EPEX and regelleistung`,
      `${eligibleProductCount ?? 0} asset product(s) commercially eligible or reviewable`,
      `${Number(summary.epex_count ?? 0)} EPEX route(s), ${Number(summary.ancillary_count ?? 0)} ancillary route(s) tracked`,
      hasLiveRoute
        ? "At least one connector advertises live submission"
        : `${liveBlockingCount || previewOnlyCount} route(s) still block live automation`,
    ],
    nextAction:
      automationControl?.next_automation_action?.message ??
      connectorReadiness?.recommended_actions?.[0] ??
      blockers[0] ??
      "Feed eligible routes into market allocation before bid proposal generation.",
    tone,
  };
}

function epexTone(rows: ReturnType<typeof buildRuleRows>): DecisionBriefTone {
  const epexRows = rows.filter((row) => String(row.adapter_id).startsWith("epex_"));

  if (epexRows.some((row) => row.live_submission === true)) {
    return "emerald";
  }

  if (epexRows.length) {
    return "amber";
  }

  return "red";
}

function epexReadinessLabel(rows: ReturnType<typeof buildRuleRows>) {
  const epexRows = rows.filter((row) => String(row.adapter_id).startsWith("epex_"));
  const liveCount = epexRows.filter((row) => row.live_submission === true).length;

  if (liveCount) {
    return `${liveCount} live route(s)`;
  }

  return epexRows.length ? "preview/live credentials required" : "not mapped";
}

function formatList(value: unknown) {
  return Array.isArray(value) ? value.join(" | ") || "-" : String(value ?? "-");
}

function MarketRuleRow({
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
