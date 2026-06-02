export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export type JsonObject = {
  [key: string]: JsonValue | undefined;
};

export type ApiStatus =
  | "ok"
  | "not_found"
  | "invalid"
  | "error"
  | "missing_token"
  | "fallback"
  | string;

export type ApiEnvelope<T extends JsonObject = JsonObject> = {
  message?: string;
  status: ApiStatus;
} & T;

export type TableRow = {
  [key: string]: JsonValue | undefined;
};

export type HealthResponse = ApiEnvelope<{
  service?: string;
}>;

export type Asset = TableRow & {
  asset_id: string;
  asset_name?: string;
  capacity_mwh?: number;
  country?: string;
  market?: string;
  max_charge_power_mw?: number;
  max_discharge_power_mw?: number;
  site_name?: string;
};

export type AssetListResponse = ApiEnvelope<{
  assets?: Asset[];
}>;

export type DispatchAction = "charge" | "discharge" | "idle" | string;

export type DispatchRow = TableRow & {
  action?: DispatchAction;
  battery_energy_mwh?: number;
  cost_eur?: number;
  grid_energy_mwh?: number;
  market_value_eur?: number;
  pnl_eur?: number;
  price?: number;
  soc_mwh?: number;
  timestamp: string;
  total_pnl_eur?: number;
};

export type SignalMetadata = JsonObject & {
  forecast_file?: string;
  forecast_model?: string;
  forecast_provider?: string;
  generated_at?: string;
  source?: string;
  target_date?: string;
};

export type SignalSummary = JsonObject & {
  charged_mwh?: number;
  charge_hours?: number;
  discharged_mwh?: number;
  discharge_hours?: number;
  equivalent_full_cycles?: number;
  first_charge_timestamp?: string | null;
  first_discharge_timestamp?: string | null;
  opportunity_level?: string;
  profit_per_mw_day?: number;
  signal?: string;
  throughput_mwh?: number;
  total_pnl_eur?: number;
};

export type LatestSignalResponse = ApiEnvelope<{
  data?: {
    dispatch?: DispatchRow[];
    metadata?: SignalMetadata;
    summary?: SignalSummary;
  };
  signal_file?: string;
}>;

export type ForecastStatusResponse = ApiEnvelope<{
  average_price?: number;
  duplicate_timestamps?: number;
  first_timestamp?: string;
  invalid_timestamps?: number;
  last_timestamp?: string;
  max_price?: number;
  min_price?: number;
  missing_prices?: number;
  negative_price_hours?: number;
  row_count?: number;
  valid_row_count?: number;
}>;

export type ForecastPreviewRow = TableRow & {
  forecast_model?: string;
  forecast_price?: number;
  forecast_provider?: string;
  forecast_renewables_total?: number;
  forecast_solar?: number;
  forecast_wind?: number;
  generation_forecast?: number;
  load_forecast?: number;
  timestamp: string;
};

export type ForecastPreviewResponse = ApiEnvelope<{
  columns?: string[];
  forecast_file?: string;
  preview?: ForecastPreviewRow[];
  rows?: number;
}>;

export type ForecastProfitabilityResult = TableRow & {
  charge_hours?: number;
  discharge_hours?: number;
  first_charge_timestamp?: string;
  first_discharge_timestamp?: string;
  forecast_file?: string;
  forecast_provider: string;
  opportunity_level?: string;
  profit_per_mw_day?: number;
  signal?: string;
  status?: ApiStatus;
  total_pnl_eur?: number;
};

export type ForecastProfitabilityResponse = ApiEnvelope<{
  comparison_file?: string;
  results?: ForecastProfitabilityResult[];
}>;

export type ActualPriceStatusResponse = ApiEnvelope<{
  actual_file?: JsonObject;
}>;

export type ForecastActualResponse = ApiEnvelope<{
  asset_id?: string;
  forecast_actual_id?: number;
  metrics?: JsonObject;
  result?: JsonObject;
  run?: JsonObject;
}>;

export type RevenueStackResult = TableRow & {
  availability_hours?: number;
  market?: string;
  revenue_eur?: number;
  risk_adjusted_revenue_eur?: number;
  status?: ApiStatus;
  total_revenue_eur?: number;
};

export type RevenueStackResponse = ApiEnvelope<{
  results?: RevenueStackResult[];
}>;

export type RevenueAllocationResult = TableRow & {
  allocated_capacity_mw?: number;
  expected_revenue_eur?: number;
  market?: string;
  risk_note?: string;
};

export type RevenueAllocationResponse = ApiEnvelope<{
  allocation?: JsonObject;
  results?: RevenueAllocationResult[];
}>;

export type StorageClassificationResponse = ApiEnvelope<{
  asset_id?: string;
  market_participation_mode?: string;
  storage_classification?: string;
}>;

export type EegComplianceResponse = ApiEnvelope<{
  asset_id?: string;
  compliance_notes?: string[];
  eeg_eligible?: boolean;
  green_colocation?: boolean;
  mixed_origin_risk?: string;
}>;

export type GridFeeSensitivityRow = TableRow & {
  grid_fee_eur_per_mwh?: number;
  pnl_delta_eur?: number;
  scenario_name?: string;
  total_pnl_eur?: number;
};

export type GridFeeSensitivityResponse = ApiEnvelope<{
  sensitivity?: GridFeeSensitivityRow[];
}>;

export type AncillaryEligibilityResponse = ApiEnvelope<{
  asset_id?: string;
  eligible?: boolean;
  eligible_products?: string[];
  reason?: string;
}>;

export type HedgeContract = TableRow & {
  cap_eur?: number;
  contract_name?: string;
  contract_type?: string;
  floor_eur?: number;
  hedged_revenue_eur?: number;
  revenue_share_percent?: number;
};

export type HedgingSummary = JsonObject & {
  hedged_revenue_eur?: number;
  merchant_upside_eur?: number;
  residual_exposure_eur?: number;
};

export type HedgingRevenueResponse = ApiEnvelope<{
  contracts?: HedgeContract[];
  summary?: HedgingSummary;
}>;

export type MonthlyReportResponse = ApiEnvelope<{
  report_name?: string;
}>;

export type ClientConfigResponse = ApiEnvelope<{
  config?: JsonObject;
}>;
