"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { DataTable } from "@/components/data-table";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";
import type {
  ApiEnvelope,
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
  const adapters = useQuery({
    queryFn: () =>
      apiGet<MarketAdapterRegistryResponse>(
        "/execution/market-adapters?country=Germany",
      ),
    queryKey: ["market-rules-adapters"],
  });

  const products = useQuery({
    queryFn: () =>
      apiGet<MarketProductsResponse>("/markets/products?country=Germany"),
    queryKey: ["market-rules-products"],
  });

  const ruleRows = useMemo(
    () => buildRuleRows(adapters.data?.adapters ?? []),
    [adapters.data?.adapters],
  );
  const productRows = useMemo(
    () => normalizeProductRows(products.data?.products ?? []),
    [products.data?.products],
  );
  const previewOnlyCount = ruleRows.filter(
    (row) => row.live_submission === false,
  ).length;
  const missingCredentialCount = ruleRows.filter(
    (row) => row.credential_status === "missing",
  ).length;

  return (
    <>
      <PageHeading
        description="Inspect gate closures, product timing, submission constraints, and automation blockers for German EPEX and regelleistung markets."
        eyebrow="Market intelligence"
        title="Market rules"
      />

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
        action={<StatusPill tone="amber">Automation gate checks</StatusPill>}
        title="Market gate and automation rules"
      >
        <DataTable
          columns={[
            "adapter_id",
            "venue",
            "market_segment",
            "gate_closure",
            "product_timing",
            "supported_granularity",
            "submission_mode",
            "credential_status",
            "automation_blocker",
          ]}
          rows={ruleRows}
        />
      </SectionCard>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard title="Product constraints">
          <DataTable
            columns={[
              "product_id",
              "product_name",
              "market",
              "settlement_interval_minutes",
              "minimum_power_mw",
              "minimum_duration_hours",
              "requires_prequalification",
            ]}
            rows={productRows}
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
    </>
  );
}

function buildRuleRows(adapters: NonNullable<MarketAdapterRegistryResponse["adapters"]>) {
  return adapters
    .filter((adapter) => adapter.environment !== "paper" && adapter.environment !== "demo")
    .map((adapter) => {
      const rule = marketRuleCatalog.find(
        (item) => item.adapter_id === adapter.adapter_id,
      );

      return {
        ...adapter,
        automation_blocker: rule?.automation_blocker ?? adapter.next_connection_action,
        gate_closure: rule?.gate_closure ?? "Connector-specific gate timing required",
        market_rule: rule?.market_rule ?? adapter.next_connection_action,
        product_timing: rule?.product_timing ?? "-",
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
