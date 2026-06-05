import { DataTable } from "@/components/data-table";
import { ExecutionMetric } from "@/components/execution/execution-metric";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatNumber } from "@/lib/format";
import type {
  AssetMarketAdapterStatusResponse,
  AssetTelemetryResponse,
  EpexDayAheadPreviewResponse,
  EpexIntradayAuctionPreviewResponse,
  EpexIntradayContinuousPreviewResponse,
  RegelleistungAfrrPreviewResponse,
  RegelleistungFcrPreviewResponse,
  RegelleistungMfrrPreviewResponse,
} from "@/types/api";

export function AssetTelemetryPanel({
  telemetryData,
}: {
  telemetryData: AssetTelemetryResponse["telemetry"];
}) {
  return (
    <SectionCard
      action={
        <StatusPill tone={telemetryData ? "emerald" : "slate"}>
          {telemetryData?.availability_status ?? "missing"}
        </StatusPill>
      }
      title="Asset telemetry"
    >
      <div className="grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="SOC"
          value={`${formatNumber(telemetryData?.soc_percent, 1)}%`}
        />
        <ExecutionMetric
          label="Discharge MW"
          value={formatNumber(telemetryData?.available_discharge_power_mw, 2)}
        />
        <ExecutionMetric
          label="Schedule deviation"
          value={`${formatNumber(telemetryData?.schedule_deviation_mwh, 3)} MWh`}
        />
      </div>
      <div className="mt-4">
        <DataTable
          columns={[
            "provider",
            "captured_at",
            "ems_status",
            "inverter_status",
            "grid_import_limit_mw",
            "grid_export_limit_mw",
            "maintenance_active",
            "curtailment_active",
          ]}
          rows={telemetryData ? [telemetryData] : []}
        />
      </div>
    </SectionCard>
  );
}

export function MarketAdapterPanel({
  status,
}: {
  status?: AssetMarketAdapterStatusResponse;
}) {
  const adapters = status?.adapters ?? [];

  return (
    <SectionCard
      action={
        <StatusPill tone={status?.live_submission_enabled ? "emerald" : "blue"}>
          {status?.market_adapter_status ?? "not evaluated"}
        </StatusPill>
      }
      title="Germany market adapters"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Connected"
          value={formatNumber(status?.connected_adapter_count, 0)}
        />
        <ExecutionMetric
          label="Planned"
          value={formatNumber(status?.planned_adapter_count, 0)}
        />
        <ExecutionMetric
          label="Bidding zone"
          value={status?.bidding_zone ?? "DE_LU"}
        />
      </div>
      <DataTable
        columns={[
          "adapter_id",
          "venue",
          "market_segment",
          "environment",
          "connection_status",
          "credential_status",
          "live_submission",
          "next_connection_action",
        ]}
        rows={adapters.slice(0, 8)}
      />
    </SectionCard>
  );
}

export function EpexDayAheadPreviewPanel({
  preview,
}: {
  preview?: EpexDayAheadPreviewResponse["preview"];
}) {
  const summary = preview?.summary ?? {};

  return (
    <SectionCard
      action={
        <StatusPill tone={preview?.status === "ready_for_broker_submission" ? "emerald" : "amber"}>
          {preview?.status ?? "not built"}
        </StatusPill>
      }
      title="EPEX Day-Ahead order preview"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Orders"
          value={formatNumber(summary.order_count, 0)}
        />
        <ExecutionMetric
          label="Buy MW"
          value={formatNumber(summary.total_buy_mw, 2)}
        />
        <ExecutionMetric
          label="Sell MW"
          value={formatNumber(summary.total_sell_mw, 2)}
        />
      </div>
      <DataTable
        columns={[
          "exchange_order_id",
          "source_bid_id",
          "product",
          "side",
          "quantity_mw",
          "limit_price_eur_mwh",
          "delivery_start",
          "time_in_force",
          "live_submission",
        ]}
        rows={(preview?.orders ?? []).slice(0, 10)}
      />
      <div className="mt-4">
        <DataTable
          columns={["check", "status", "message"]}
          rows={(preview?.validation?.checks ?? []).slice(0, 6)}
        />
      </div>
    </SectionCard>
  );
}

export function EpexIntradayAuctionPreviewPanel({
  preview,
}: {
  preview?: EpexIntradayAuctionPreviewResponse["preview"];
}) {
  const summary = preview?.summary ?? {};

  return (
    <SectionCard
      action={
        <StatusPill tone={preview?.status === "ready_for_broker_submission" ? "emerald" : "amber"}>
          {preview?.status ?? "not built"}
        </StatusPill>
      }
      title="EPEX Intraday Auction preview"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Orders"
          value={formatNumber(summary.order_count, 0)}
        />
        <ExecutionMetric
          label="Buy MW"
          value={formatNumber(summary.total_buy_mw, 2)}
        />
        <ExecutionMetric
          label="Sell MW"
          value={formatNumber(summary.total_sell_mw, 2)}
        />
      </div>
      <DataTable
        columns={[
          "exchange_order_id",
          "source_bid_id",
          "product",
          "side",
          "quantity_mw",
          "limit_price_eur_mwh",
          "delivery_start",
          "time_in_force",
          "live_submission",
        ]}
        rows={(preview?.orders ?? []).slice(0, 10)}
      />
      <div className="mt-4">
        <DataTable
          columns={["check", "status", "message"]}
          rows={(preview?.validation?.checks ?? []).slice(0, 6)}
        />
      </div>
    </SectionCard>
  );
}

export function EpexIntradayContinuousPreviewPanel({
  preview,
}: {
  preview?: EpexIntradayContinuousPreviewResponse["preview"];
}) {
  const summary = preview?.summary ?? {};

  return (
    <SectionCard
      action={
        <StatusPill tone={preview?.status === "ready_for_trader_review" ? "emerald" : "amber"}>
          {preview?.status ?? "not built"}
        </StatusPill>
      }
      title="EPEX Intraday Continuous preview"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Orders"
          value={formatNumber(summary.order_count, 0)}
        />
        <ExecutionMetric
          label="Aggressive"
          value={formatNumber(summary.aggressive_order_count, 0)}
        />
        <ExecutionMetric
          label="Do not cross"
          value={formatNumber(summary.do_not_cross_order_count, 0)}
        />
      </div>
      <DataTable
        columns={[
          "exchange_order_id",
          "source_bid_id",
          "product",
          "side",
          "execution_style",
          "quantity_mw",
          "limit_price_eur_mwh",
          "reference_price_eur_mwh",
          "bid_ask_spread_eur_mwh",
          "max_slippage_eur_mwh",
          "partial_fill_policy",
          "cancel_replace_policy",
          "live_submission",
        ]}
        rows={(preview?.orders ?? []).slice(0, 10)}
      />
      <div className="mt-4">
        <DataTable
          columns={["check", "status", "message"]}
          rows={(preview?.validation?.checks ?? []).slice(0, 6)}
        />
      </div>
    </SectionCard>
  );
}

export function RegelleistungFcrPreviewPanel({
  preview,
}: {
  preview?: RegelleistungFcrPreviewResponse["preview"];
}) {
  const summary = preview?.summary ?? {};
  const capability = preview?.capability ?? {};

  return (
    <SectionCard
      action={
        <StatusPill tone={preview?.status === "ready_for_prequalification_review" ? "emerald" : "amber"}>
          {preview?.status ?? "not built"}
        </StatusPill>
      }
      title="Regelleistung FCR preview"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Symmetric MW"
          value={formatNumber(capability.available_symmetric_power_mw, 2)}
        />
        <ExecutionMetric
          label="Bid MW"
          value={formatNumber(summary.capacity_bid_mw, 2)}
        />
        <ExecutionMetric
          label="Min MW"
          value={formatNumber(summary.minimum_power_mw, 2)}
        />
      </div>
      <DataTable
        columns={[
          "reserve_bid_id",
          "product",
          "direction",
          "capacity_mw",
          "minimum_duration_hours",
          "availability_status",
          "telemetry_provider",
          "live_submission",
        ]}
        rows={(preview?.bids ?? []).slice(0, 10)}
      />
      <div className="mt-4">
        <DataTable
          columns={["check", "status", "message", "context"]}
          rows={(preview?.validation?.checks ?? []).slice(0, 6)}
        />
      </div>
    </SectionCard>
  );
}

export function RegelleistungAfrrPreviewPanel({
  preview,
}: {
  preview?: RegelleistungAfrrPreviewResponse["preview"];
}) {
  const summary = preview?.summary ?? {};
  const capability = preview?.capability ?? {};

  return (
    <SectionCard
      action={
        <StatusPill tone={preview?.status === "ready_for_prequalification_review" ? "emerald" : "amber"}>
          {preview?.status ?? "not built"}
        </StatusPill>
      }
      title="Regelleistung aFRR preview"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Positive MW"
          value={formatNumber(capability.positive_capacity_mw, 2)}
        />
        <ExecutionMetric
          label="Negative MW"
          value={formatNumber(capability.negative_capacity_mw, 2)}
        />
        <ExecutionMetric
          label="Residual energy MW"
          value={formatNumber(summary.energy_arbitrage_capacity_after_reserve_mw, 2)}
        />
      </div>
      <DataTable
        columns={[
          "reserve_bid_id",
          "product",
          "direction",
          "capacity_mw",
          "linked_capacity_mw",
          "activation_policy",
          "availability_status",
          "telemetry_provider",
          "live_submission",
          "status",
        ]}
        rows={(preview?.bids ?? []).slice(0, 10)}
      />
      <div className="mt-4">
        <DataTable
          columns={["check", "status", "message", "context"]}
          rows={(preview?.validation?.checks ?? []).slice(0, 6)}
        />
      </div>
    </SectionCard>
  );
}

export function RegelleistungMfrrPreviewPanel({
  preview,
}: {
  preview?: RegelleistungMfrrPreviewResponse["preview"];
}) {
  const summary = preview?.summary ?? {};
  const capability = preview?.capability ?? {};

  return (
    <SectionCard
      action={
        <StatusPill tone={preview?.status === "ready_for_prequalification_review" ? "emerald" : "amber"}>
          {preview?.status ?? "not built"}
        </StatusPill>
      }
      title="Regelleistung mFRR preview"
    >
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <ExecutionMetric
          label="Positive MW"
          value={formatNumber(capability.positive_capacity_mw, 2)}
        />
        <ExecutionMetric
          label="Negative MW"
          value={formatNumber(capability.negative_capacity_mw, 2)}
        />
        <ExecutionMetric
          label="Residual energy MW"
          value={formatNumber(summary.energy_arbitrage_capacity_after_reserve_mw, 2)}
        />
      </div>
      <DataTable
        columns={[
          "reserve_bid_id",
          "product",
          "direction",
          "capacity_mw",
          "linked_capacity_mw",
          "activation_mode",
          "activation_policy",
          "availability_status",
          "telemetry_provider",
          "live_submission",
          "status",
        ]}
        rows={(preview?.bids ?? []).slice(0, 10)}
      />
      <div className="mt-4">
        <DataTable
          columns={["check", "status", "message", "context"]}
          rows={(preview?.validation?.checks ?? []).slice(0, 6)}
        />
      </div>
    </SectionCard>
  );
}
