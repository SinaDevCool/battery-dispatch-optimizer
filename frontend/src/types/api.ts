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
  average_actual_price?: number;
  columns?: string[];
  first_timestamp?: string;
  invalid_timestamps?: number;
  last_timestamp?: string;
  max_actual_price?: number;
  min_actual_price?: number;
  missing_prices?: number;
  rows?: number;
  valid_rows?: number;
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
  blocking_reasons?: JsonValue[];
  eligibility_status?: string;
  estimated_revenue_eur?: number | null;
  missing_inputs?: string[];
  market?: string;
  product_id?: string;
  revenue_eur?: number;
  review_warnings?: JsonValue[];
  risk_adjusted_revenue_eur?: number;
  source?: string;
  status?: ApiStatus;
  total_revenue_eur?: number;
};

export type RevenueStackResponse = ApiEnvelope<{
  estimated_product_count?: number;
  product_count?: number;
  products?: RevenueStackResult[];
  results?: RevenueStackResult[];
  total_estimated_revenue_eur?: number;
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
  charges_from_grid?: boolean;
  charges_from_renewables?: boolean;
  eeg_support_risk?: string;
  exports_stored_renewable_power?: boolean;
  is_colocated?: boolean;
  market_participation_mode?: string;
  metering_concept?: string | null;
  storage_classification?: string;
  storage_mode?: string;
  uses_eeg_support?: boolean;
  warnings?: JsonValue[];
}>;

export type EegComplianceResponse = ApiEnvelope<{
  asset_id?: string;
  compliance_notes?: string[];
  eeg_eligible?: boolean;
  eeg_support_risk?: string;
  findings?: JsonValue[];
  green_colocation?: boolean;
  mixed_origin_risk?: string;
  recommended_actions?: string[];
}>;

export type GridFeeSensitivityRow = TableRow & {
  grid_fee_eur_per_mwh?: number;
  pnl_delta_eur?: number;
  scenario_name?: string;
  total_pnl_eur?: number;
};

export type GridFeeSensitivityResponse = ApiEnvelope<{
  export_mwh?: number;
  import_mwh?: number;
  scenarios?: GridFeeSensitivityRow[];
  sensitivity?: GridFeeSensitivityRow[];
}>;

export type AncillaryEligibilityResponse = ApiEnvelope<{
  asset_id?: string;
  eligible?: boolean;
  eligible_product_count?: number;
  eligible_products?: string[];
  products?: TableRow[];
  reason?: string;
}>;

export type HedgeContract = TableRow & {
  cap_eur?: number;
  contract_name?: string;
  contract_type?: string;
  downside_protection_eur_per_month?: number;
  expected_owner_revenue_eur_per_month?: number;
  floor_eur?: number;
  floor_revenue_eur_per_month?: number;
  floor_revenue_eur_per_mw_month?: number;
  name?: string;
  owner_upside_eur_per_month?: number;
  hedged_revenue_eur?: number;
  merchant_revenue_given_away_eur_per_month?: number;
  revenue_share_percent?: number;
  upside_share_percent?: number;
};

export type HedgingSummary = JsonObject & {
  hedged_revenue_eur?: number;
  merchant_upside_eur?: number;
  residual_exposure_eur?: number;
};

export type HedgingRevenueResponse = ApiEnvelope<{
  best_contract?: HedgeContract | null;
  contracts?: HedgeContract[];
  merchant_revenue_eur_per_month?: number;
  power_mw?: number;
  summary?: HedgingSummary;
}>;

export type BusinessDecision = JsonObject & {
  asset_id?: string;
  blockers?: string[];
  decision_basis?: JsonObject;
  description?: string;
  eeg_eligible?: boolean;
  eligible_product_count?: number;
  expected_pnl_eur?: number;
  forecast_model?: string;
  forecast_provider?: string;
  generated_at?: string;
  hedged_revenue_eur?: number;
  merchant_upside_eur?: number;
  profit_per_mw_day?: number;
  readiness?: string;
  recommendation_status?: string;
  recommendation_title?: string;
  recommended_actions?: string[];
  residual_exposure_eur?: number;
  revenue_stack_available?: boolean;
  signal_available?: boolean;
};

export type BusinessDecisionResponse = ApiEnvelope<{
  asset_id?: string;
  decision?: BusinessDecision;
}>;

export type BusinessDecisionHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  decisions?: BusinessDecision[];
}>;

export type DatabaseStatusResponse = ApiEnvelope<{
  database_file?: string;
  table_counts?: {
    assets?: number;
    business_decisions?: number;
    forecast_actual_runs?: number;
    forecast_snapshots?: number;
    revenue_product_results?: number;
    revenue_stack_runs?: number;
    signal_runs?: number;
    workflow_runs?: number;
  };
}>;

export type DataCompletenessCheck = TableRow & {
  check_id?: string;
  evidence?: JsonObject;
  label?: string;
  message?: string;
  recommended_action?: string;
  record_id?: number | string | null;
  status?: "complete" | "missing" | string;
};

export type DataCompletenessResponse = ApiEnvelope<{
  asset_id?: string;
  check_count?: number;
  checks?: DataCompletenessCheck[];
  complete_count?: number;
  missing_count?: number;
  next_actions?: string[];
  readiness?: string;
  score?: number;
}>;

export type AssetCockpitBusinessKpis = JsonObject & {
  data_completeness_score?: number;
  data_readiness?: string;
  decision_expected_pnl_eur?: number;
  decision_status?: string;
  expected_pnl_eur?: number;
  modelled_revenue_eur?: number;
  opportunity_level?: string;
  profit_per_mw_day?: number;
  revenue_product_count?: number;
  signal?: string;
};

export type EnterpriseMaturity = JsonObject & {
  automation_readiness?: string;
  bankability_evidence_count?: number;
  competitor_positioning?: string;
  differentiation_score?: number;
  display_level?: string;
  gaps?: string[];
  level?: string;
  next_moat_actions?: string[];
  score?: number;
  strengths?: string[];
};

export type AssetCockpitPayload = JsonObject & {
  asset_id?: string;
  business_decision?: BusinessDecisionResponse;
  business_kpis?: AssetCockpitBusinessKpis;
  data_completeness?: DataCompletenessResponse;
  dispatch?: DispatchRow[];
  enterprise_maturity?: EnterpriseMaturity;
  execution_proposal?: ExecutionProposal | null;
  latest_signal?: LatestSignalResponse;
  recommended_next_actions?: string[];
  revenue_allocation?: RevenueAllocationResponse;
  revenue_products?: RevenueStackResult[];
  revenue_stack?: RevenueStackResponse;
  signal_metadata?: SignalMetadata;
  signal_summary?: SignalSummary;
  workflow_run?: WorkflowRun | null;
};

export type AssetCockpitResponse = ApiEnvelope<{
  asset_id?: string;
  cockpit?: AssetCockpitPayload;
}>;

export type WorkflowRun = JsonObject & {
  asset_id?: string;
  completed_at?: string;
  decision_id?: number;
  expected_pnl_eur?: number;
  forecast_model?: string;
  forecast_provider?: string;
  forecast_snapshot_id?: number;
  optimizer_engine?: string;
  recommendation_status?: string;
  revenue_stack_id?: number;
  signal_id?: number;
  started_at?: string;
  status?: ApiStatus;
  target_date?: string;
  workflow_run_id?: number;
};

export type WorkflowRunResponse = ApiEnvelope<{
  asset_id?: string;
  workflow_run?: WorkflowRun | null;
}>;

export type WorkflowRunHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  workflow_runs?: WorkflowRun[];
}>;

export type ExecutionOrder = TableRow & {
  delivery_time?: string;
  market?: string;
  order_id?: string;
  price_limit_eur_mwh?: number;
  side?: string;
  source_action?: string;
  status?: string;
  volume_mwh?: number;
};

export type ExecutionRiskCheck = TableRow & {
  check?: string;
  context?: JsonObject;
  message?: string;
  status?: string;
};

export type ExecutionProposal = JsonObject & {
  approval_status?: string;
  asset_id?: string;
  audit?: TableRow[];
  automation_blockers?: string[];
  blockers?: string[];
  execution_mode?: string;
  execution_proposal_id?: number;
  forecast_model?: string;
  forecast_provider?: string;
  generated_at?: string;
  market?: string;
  market_submission_enabled?: boolean;
  orders?: ExecutionOrder[];
  risk_checks?: ExecutionRiskCheck[];
  signal_id?: number;
  status?: string;
  summary?: JsonObject & {
    expected_pnl_eur?: number;
    max_daily_loss_eur?: number;
    order_count?: number;
    profit_per_mw_day?: number;
    total_buy_mwh?: number;
    total_sell_mwh?: number;
  };
  target_date?: string;
  workflow_run_id?: number;
};

export type ExecutionProposalResponse = ApiEnvelope<{
  asset_id?: string;
  proposal?: ExecutionProposal | null;
}>;

export type ExecutionProposalHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  proposals?: TableRow[];
}>;

export type ForecastPerformanceRun = TableRow & {
  asset_id?: string;
  bias_eur_per_mwh?: number;
  forecast_actual_id?: number;
  forecast_model?: string;
  forecast_provider?: string;
  generated_at?: string;
  mae_eur_per_mwh?: number;
  predicted_pnl_eur?: number;
  realized_pnl_eur?: number;
  revenue_delta_eur?: number;
  rmse_eur_per_mwh?: number;
  row_count?: number;
  target_date?: string;
};

export type ForecastPerformanceHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  run_count?: number;
  runs?: ForecastPerformanceRun[];
}>;

export type EligibleProductResult = TableRow & {
  asset_capability?: JsonObject;
  blocking_reasons?: JsonValue[];
  eligibility_status?: string;
  eligible?: boolean;
  product?: JsonObject & {
    market?: string;
    product_id?: string;
    product_name?: string;
  };
  review_warnings?: JsonValue[];
};

export type EligibleProductsResponse = ApiEnvelope<{
  asset_id?: string;
  eligible_product_count?: number;
  product_count?: number;
  products?: EligibleProductResult[];
}>;

export type MonthlyReportResponse = ApiEnvelope<{
  report_file?: string;
  report_name?: string;
}>;

export type MonthlyReportListResponse = ApiEnvelope<{
  report_count?: number;
  reports?: TableRow[];
}>;

export type ClientConfigResponse = ApiEnvelope<{
  config?: JsonObject;
}>;
