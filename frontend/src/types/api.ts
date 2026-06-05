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

export type ForecastConfidenceResponse = ApiEnvelope<{
  asset_id?: string;
  automation_eligibility?: string;
  confidence_band?: string;
  confidence_score?: number;
  evidence?: TableRow[];
  reason?: string;
  risk_policy?: JsonObject & {
    price_buffer_eur_per_mwh?: number;
    volume_multiplier?: number;
  };
  run_count?: number;
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
  approval_status?: string;
  automation_eligibility?: string;
  bid_id?: string;
  bid_status?: string;
  bid_type?: string;
  confidence_reason?: string;
  delivery_end?: string;
  delivery_start?: string;
  delivery_time?: string;
  energy_mwh?: number;
  lifecycle_status?: string;
  limit_price_eur_mwh?: number;
  market?: string;
  market_product_id?: string;
  order_id?: string;
  price_limit_eur_mwh?: number;
  risk_status?: string;
  risk_adjusted_limit_price_eur_mwh?: number;
  risk_adjusted_volume_mw?: number;
  risk_adjusted_volume_mwh?: number;
  forecast_confidence_band?: string;
  forecast_confidence_score?: number;
  side?: string;
  source_action?: string;
  status?: string;
  submission_status?: string;
  volume_mw?: number;
  volume_mwh?: number;
};

export type ExecutionLifecycleStep = TableRow & {
  label?: string;
  owner?: string;
  status?: string;
  step?: string;
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
  forecast_confidence?: ForecastConfidenceResponse;
  generated_at?: string;
  bid_lifecycle?: ExecutionLifecycleStep[];
  bids?: ExecutionOrder[];
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

export type ExecutionPaperFill = TableRow & {
  bid_id?: string;
  delivery_end?: string;
  delivery_start?: string;
  delivery_time?: string;
  fill_price_eur_mwh?: number;
  filled_volume_mwh?: number;
  limit_price_eur_mwh?: number;
  market?: string;
  market_product_id?: string;
  notional_eur?: number;
  order_id?: string;
  paper_fill_id?: string;
  requested_volume_mwh?: number;
  side?: string;
  status?: string;
};

export type ExecutionPaperTrade = TableRow & {
  adapter_id?: string;
  asset_id?: string;
  audit?: TableRow[];
  bid_lifecycle?: ExecutionLifecycleStep[];
  bids?: ExecutionOrder[];
  execution_proposal_id?: number;
  fills?: ExecutionPaperFill[];
  generated_at?: string;
  lifecycle_status?: string;
  mode?: string;
  paper_trade_id?: number;
  proposal_generated_at?: string;
  status?: string;
  summary?: TableRow & {
    buy_cost_eur?: number;
    expected_pnl_eur?: number;
    filled_order_count?: number;
    order_count?: number;
    paper_pnl_eur?: number;
    paper_vs_expected_delta_eur?: number;
    sell_revenue_eur?: number;
  };
};

export type ExecutionPaperTradeResponse = ApiEnvelope<{
  asset_id?: string;
  paper_trade?: ExecutionPaperTrade | null;
}>;

export type ExecutionPaperTradeHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  paper_trades?: TableRow[];
}>;

export type SettlementSummary = JsonObject & {
  expected_pnl_eur?: number;
  paper_delta_eur?: number | null;
  paper_pnl_eur?: number | null;
  realized_delta_eur?: number | null;
  realized_pnl_eur?: number | null;
};

export type SettlementReconciliation = JsonObject & {
  asset_id?: string;
  evidence_status?: JsonObject;
  generated_at?: string;
  primary_variance_driver?: string;
  recommended_actions?: string[];
  settlement_reconciliation_id?: number;
  status?: string;
  summary?: SettlementSummary;
  variance_drivers?: TableRow[];
};

export type SettlementResponse = ApiEnvelope<{
  asset_id?: string;
  settlement?: SettlementReconciliation | null;
}>;

export type SettlementHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  settlements?: TableRow[];
}>;

export type AutomationGuardrail = TableRow & {
  context?: JsonObject;
  guardrail?: string;
  message?: string;
  status?: string;
};

export type AutomationGuardrailsResponse = ApiEnvelope<{
  asset_id?: string;
  automation_status?: string;
  evidence?: JsonObject;
  guardrails?: AutomationGuardrail[];
  policy_evaluation?: AutomationPolicyEvaluation;
  recommended_actions?: string[];
  summary?: JsonObject & {
    blocked?: number;
    passed?: number;
    review?: number;
    total?: number;
  };
}>;

export type AutomationPolicyMarketRole = TableRow & {
  adapter_id?: string;
  automation_scope?: string;
  role?: string;
};

export type AutomationPolicy = JsonObject & {
  allowed_markets?: string[];
  approval_policy?: JsonObject & {
    auto_approve_below_power_mw?: number;
    four_eyes_required_above_power_mw?: number;
    require_human_approval?: boolean;
  };
  asset_id?: string;
  automation_mode?: string;
  automation_policy_id?: number;
  confidence_policy?: JsonObject & {
    low_confidence_action?: string;
    medium_confidence_action?: string;
    min_confidence_band?: string;
    min_confidence_score?: number;
  };
  fallback_policy?: JsonObject & {
    mode?: string;
    on_adapter_unavailable?: string;
    on_missing_forecast?: string;
    on_missing_telemetry?: string;
  };
  market_roles?: AutomationPolicyMarketRole[];
  policy_version?: string;
  risk_limits?: JsonObject & {
    max_cycles_per_day?: number;
    max_daily_loss_eur?: number;
    max_open_notional_eur?: number;
    max_order_power_mw?: number;
  };
  simulation_policy?: JsonObject & {
    max_paper_vs_expected_delta_eur?: number;
    require_paper_trade?: boolean;
  };
  updated_at?: string;
};

export type AutomationPolicyCheck = TableRow & {
  check?: string;
  context?: JsonObject;
  message?: string;
  status?: string;
};

export type AutomationPolicyEvaluation = JsonObject & {
  asset_id?: string;
  checks?: AutomationPolicyCheck[];
  policy?: AutomationPolicy;
  policy_decision?: string;
  policy_source?: string;
  recommended_actions?: string[];
  summary?: JsonObject & {
    blocked?: number;
    passed?: number;
    review?: number;
    total?: number;
  };
};

export type AutomationPolicyResponse = ApiEnvelope<{
  asset_id?: string;
  policy?: AutomationPolicy;
  source?: string;
}>;

export type AutomationPolicyEvaluationResponse = ApiEnvelope<{
  asset_id?: string;
  checks?: AutomationPolicyCheck[];
  policy?: AutomationPolicy;
  policy_decision?: string;
  policy_source?: string;
  recommended_actions?: string[];
  summary?: JsonObject & {
    blocked?: number;
    passed?: number;
    review?: number;
    total?: number;
  };
}>;

export type AutomationPolicyHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  policies?: TableRow[];
}>;

export type AutomationControlStatusResponse = ApiEnvelope<{
  allowed_markets?: string[];
  asset_id?: string;
  automation_mode?: string;
  automation_mode_rank?: number;
  automation_status?: string;
  blockers?: TableRow[];
  confidence_policy?: JsonObject;
  connector_status?: string;
  evidence?: JsonObject & {
    allocation_summary?: JsonObject;
    approval_id?: number;
    automation_policy_id?: number;
    automation_policy_source?: string;
    execution_proposal_id?: number;
    guardrail_summary?: JsonObject;
    live_submission_enabled?: boolean;
    market_submission_id?: number;
    paper_trade_id?: number;
    readiness_summary?: JsonObject;
  };
  freshness_gates?: AutomationFreshnessGate[];
  generated_at?: string;
  human_gate?: JsonObject & {
    approval_id?: number;
    approval_status?: string;
    auto_approve_below_power_mw?: number;
    execution_proposal_id?: number;
    four_eyes_required_above_power_mw?: number;
    required?: boolean;
    status?: string;
  };
  live_trading_allowed?: boolean;
  mode_escalation?: AutomationModeEscalation;
  next_automation_action?: JsonObject & {
    action?: string;
    label?: string;
    message?: string;
    owner?: string;
  };
  paper_trading_allowed?: boolean;
  persistence_readiness?: PersistenceReadinessResponse;
  policy_decision?: string;
  primary_market?: MultiMarketAllocationCandidate | null;
  readiness_score?: number;
  readiness_status?: string;
  remediation_queue?: AutomationRemediationItem[];
  risk_limits?: JsonObject;
  secondary_market?: MultiMarketAllocationCandidate | null;
  supervised_trading_allowed?: boolean;
}>;

export type PersistenceReadinessCheck = TableRow & {
  check?: string;
  evidence?: JsonObject;
  label?: string;
  message?: string;
  status?: string;
};

export type PersistenceReadinessResponse = ApiEnvelope<{
  automation_blocking_level?: string | null;
  checks?: PersistenceReadinessCheck[];
  database_file?: string;
  generated_at?: string;
  persistence_status?: string;
  recommended_actions?: string[];
  summary?: JsonObject & {
    blocked?: number;
    missing_tables?: string[];
    passed?: number;
    review?: number;
    total?: number;
  };
}>;

export type AutomationModeRequirement = TableRow & {
  check?: string;
  context?: JsonObject;
  label?: string;
  message?: string;
  status?: string;
};

export type AutomationModeLadderStep = TableRow & {
  description?: string;
  label?: string;
  mode?: string;
  status?: string;
};

export type AutomationModeEscalation = JsonObject & {
  can_escalate?: boolean;
  current_mode?: string;
  current_mode_rank?: number;
  escalation_blockers?: AutomationModeRequirement[];
  ladder?: AutomationModeLadderStep[];
  next_eligible_mode?: string | null;
  required_evidence?: AutomationModeRequirement[];
  target_mode?: string | null;
};

export type AutomationFreshnessGate = TableRow & {
  age_minutes?: number | null;
  blocks_mode?: string;
  freshness_status?: "fresh" | "missing" | "stale" | string;
  gate_id?: string;
  label?: string;
  last_seen_at?: string | null;
  max_age_minutes?: number;
  required_action?: string;
};

export type AutomationRemediationItem = TableRow & {
  auto_resolvable?: boolean;
  blocker_id?: string;
  category?: string;
  evidence_link?: string;
  message?: string;
  required_action?: string;
  resolution_endpoint?: string | null;
  severity?: string;
  source?: string;
};

export type StrategyIntentConfidence = JsonObject & {
  automation_eligible?: boolean;
  band?: string;
  score?: number;
};

export type StrategyIntentMarket = TableRow & {
  adapter_id?: string;
  allocated_power_mw?: number;
  expected_revenue_eur?: number;
  market_name?: string;
  market_segment?: string;
  rank?: number;
  role?: string;
  status?: string;
};

export type StrategyIntentAction = JsonObject & {
  action?: string;
  label?: string;
  message?: string;
  owner?: string;
};

export type StrategyIntentResponse = ApiEnvelope<{
  asset_id?: string;
  blocking_evidence?: TableRow[];
  confidence?: StrategyIntentConfidence;
  dispatch_bias?: string;
  evidence?: JsonObject;
  generated_at?: string;
  market_intent?: JsonObject & {
    primary_adapter_id?: string;
    primary_market?: string;
    secondary_adapter_id?: string;
    secondary_market?: string;
    stacking_intent?: string;
  };
  recommended_next_action?: StrategyIntentAction;
  strategy_mode?: string;
  target_markets?: StrategyIntentMarket[];
  why?: string[];
}>;

export type AutomationEvent = TableRow & {
  action?: string;
  asset_id?: string;
  automation_event_id?: number;
  automation_mode_after?: string;
  automation_mode_before?: string;
  created_at?: string;
  error_type?: string | null;
  event_type?: string;
  status?: string;
  strategy_mode_after?: string;
  strategy_mode_before?: string;
};

export type AutomationEventHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  events?: AutomationEvent[];
}>;

export type AutomationEventResponse = ApiEnvelope<{
  asset_id?: string;
  event?: JsonObject | null;
}>;

export type ExecutionReadinessCheck = TableRow & {
  check?: string;
  evidence?: JsonObject;
  label?: string;
  message?: string;
  status?: string;
};

export type MarketAdapterStatus = TableRow & {
  adapter_id?: string;
  adapter_name?: string;
  bidding_zone?: string;
  connection_status?: string;
  country?: string;
  credential_status?: string;
  environment?: string;
  live_submission?: boolean;
  market_segment?: string;
  next_connection_action?: string;
  product_family?: string;
  supported_granularity?: string[];
  supported_products?: string[];
  venue?: string;
};

export type MarketAdapterRegistryResponse = ApiEnvelope<{
  adapters?: MarketAdapterStatus[];
  country?: string;
}>;

export type MarketConnectorReadiness = MarketAdapterStatus & {
  automation_blocking_level?: string;
  credential_keys?: string[];
  family?: string;
  integration_type?: string;
  missing_controls?: string[];
  missing_credentials?: string[];
  next_integration_action?: string;
  paper_supported?: boolean;
  preview_available?: boolean;
  priority?: number;
  production_readiness_tier?: string;
  readiness_score?: number;
};

export type MarketConnectorReadinessResponse = ApiEnvelope<{
  connector_status?: string;
  connectors?: MarketConnectorReadiness[];
  country?: string;
  generated_at?: string;
  integrations?: MarketConnectorReadiness[];
  recommended_actions?: string[];
  summary?: JsonObject & {
    ancillary_count?: number;
    average_readiness_score?: number;
    connector_count?: number;
    credentials_required_count?: number;
    data_feed_count?: number;
    epex_count?: number;
    live_auto_blocking_count?: number;
    live_submission_count?: number;
    preview_ready_count?: number;
    production_ready_count?: number;
    supervised_auto_blocking_count?: number;
  };
}>;

export type AssetMarketAdapterStatusResponse = ApiEnvelope<{
  adapters?: MarketAdapterStatus[];
  asset_id?: string;
  bidding_zone?: string;
  connected_adapter_count?: number;
  country?: string;
  live_submission_enabled?: boolean;
  market_adapter_status?: string;
  next_connection_action?: string;
  planned_adapter_count?: number;
  primary_adapter?: MarketAdapterStatus | null;
}>;

export type EpexDayAheadPreview = JsonObject & {
  adapter_id?: string;
  adapter_name?: string;
  audit?: TableRow[];
  bidding_zone?: string;
  environment?: string;
  gate_closure?: string;
  generated_at?: string;
  live_submission?: boolean;
  market_segment?: string;
  orders?: TableRow[];
  status?: string;
  summary?: JsonObject;
  validation?: JsonObject & {
    checks?: TableRow[];
    status?: string;
  };
  venue?: string;
};

export type EpexDayAheadPreviewResponse = ApiEnvelope<{
  asset_id?: string;
  preview?: EpexDayAheadPreview | null;
}>;

export type EpexIntradayAuctionPreviewResponse = ApiEnvelope<{
  asset_id?: string;
  preview?: EpexDayAheadPreview | null;
}>;

export type EpexIntradayContinuousPreviewResponse = ApiEnvelope<{
  asset_id?: string;
  preview?: EpexDayAheadPreview | null;
}>;

export type RegelleistungFcrPreview = JsonObject & {
  adapter_id?: string;
  adapter_name?: string;
  audit?: TableRow[];
  bids?: TableRow[];
  bidding_zone?: string;
  capability?: JsonObject;
  environment?: string;
  generated_at?: string;
  live_submission?: boolean;
  market_segment?: string;
  product?: string;
  status?: string;
  summary?: JsonObject;
  validation?: JsonObject & {
    checks?: TableRow[];
    status?: string;
  };
  venue?: string;
};

export type RegelleistungFcrPreviewResponse = ApiEnvelope<{
  asset_id?: string;
  preview?: RegelleistungFcrPreview | null;
}>;

export type RegelleistungAfrrPreviewResponse = ApiEnvelope<{
  asset_id?: string;
  preview?: RegelleistungFcrPreview | null;
}>;

export type RegelleistungMfrrPreviewResponse = ApiEnvelope<{
  asset_id?: string;
  preview?: RegelleistungFcrPreview | null;
}>;

export type MultiMarketAllocationCandidate = TableRow & {
  adapter_connection_status?: string;
  adapter_credential_status?: string;
  adapter_id?: string;
  allocated_energy_mwh?: number;
  allocated_power_mw?: number;
  allocation_score?: number;
  automation_blocking_level?: string;
  blocking_reasons?: string[];
  commercial_product_id?: string;
  connector_family?: string;
  connector_readiness_score?: number;
  connector_readiness_tier?: string;
  data_dependencies?: string[];
  expected_revenue_eur?: number;
  execution_role?: string;
  live_submission?: boolean;
  market_name?: string;
  market_segment?: string;
  missing_connector_controls?: string[];
  missing_credentials?: string[];
  operator_next_action?: string;
  preview_status?: string;
  preview_validation_status?: string;
  recommendation_status?: string;
  risk_score?: number;
  venue?: string;
};

export type MultiMarketAllocationResponse = ApiEnvelope<{
  allocation?: MultiMarketAllocationCandidate[];
  allocation_status?: string;
  asset_id?: string;
  evidence?: JsonObject;
  excluded_markets?: MultiMarketAllocationCandidate[];
  generated_at?: string;
  primary_market?: MultiMarketAllocationCandidate | null;
  recommended_actions?: string[];
  secondary_market?: MultiMarketAllocationCandidate | null;
  summary?: JsonObject & {
    approval_status?: string;
    candidate_market_count?: number;
    eligible_market_count?: number;
    excluded_market_count?: number;
    forecast_confidence_band?: string;
    forecast_confidence_score?: number;
    readiness_score?: number;
    readiness_status?: string;
    total_allocated_power_mw?: number;
    total_expected_revenue_eur?: number;
  };
}>;

export type TradingOrchestratorStage = JsonObject & {
  action?: string;
  message?: string;
  owner?: string;
  status?: string;
};

export type TradingOrchestratorNextAction = JsonObject & {
  action?: string;
  label?: string;
  message?: string;
  owner?: string;
  target_adapter_id?: string;
  target_market?: string;
};

export type TradingOrchestratorResponse = ApiEnvelope<{
  asset_id?: string;
  audit?: TableRow[];
  blockers?: TableRow[];
  evidence?: JsonObject;
  executed_actions?: TableRow[];
  generated_at?: string;
  next_action?: TradingOrchestratorNextAction;
  orchestrator_status?: string;
  stage?: TradingOrchestratorStage;
  workflow?: TableRow[];
}>;

export type ExecutionReadinessResponse = ApiEnvelope<{
  asset_id?: string;
  automation_status?: string;
  checks?: ExecutionReadinessCheck[];
  evidence?: JsonObject;
  market_adapters?: MarketAdapterStatus[];
  market_adapter_status?: string;
  readiness_score?: number;
  readiness_status?: string;
  recommended_actions?: string[];
  summary?: JsonObject & {
    blocked?: number;
    passed?: number;
    review?: number;
    total?: number;
  };
}>;

export type MarketSubmission = JsonObject & {
  adapter_id?: string;
  asset_id?: string;
  bids?: TableRow[];
  execution_proposal_id?: number;
  lifecycle?: TableRow[];
  live_submission?: boolean;
  market_submission_id?: number;
  status?: string;
  submitted_at?: string;
  summary?: JsonObject & {
    accepted_bid_count?: number;
    awarded_bid_count?: number;
    notional_eur?: number;
    rejected_bid_count?: number;
    submitted_bid_count?: number;
  };
};

export type MarketSubmissionResponse = ApiEnvelope<{
  asset_id?: string;
  submission?: MarketSubmission | null;
}>;

export type MarketSubmissionHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  submissions?: TableRow[];
}>;

export type ExecutionApproval = JsonObject & {
  approval_id?: number;
  asset_id?: string;
  decided_at?: string | null;
  decided_by?: string | null;
  execution_proposal_id?: number;
  reason?: string;
  requested_at?: string;
  requested_by?: string;
  status?: string;
};

export type ExecutionApprovalResponse = ApiEnvelope<{
  approval?: ExecutionApproval | null;
  asset_id?: string;
}>;

export type ExecutionApprovalHistoryResponse = ApiEnvelope<{
  approvals?: TableRow[];
  asset_id?: string;
}>;

export type AssetTelemetry = JsonObject & {
  asset_id?: string;
  availability_status?: string;
  available_charge_power_mw?: number;
  available_discharge_power_mw?: number;
  captured_at?: string;
  curtailment_active?: boolean;
  ems_status?: string;
  grid_export_limit_mw?: number;
  grid_import_limit_mw?: number;
  inverter_status?: string;
  maintenance_active?: boolean;
  provider?: string;
  schedule_deviation_mwh?: number;
  soc_mwh?: number;
  soc_percent?: number;
  status?: string;
  telemetry_id?: number;
};

export type AssetTelemetryResponse = ApiEnvelope<{
  asset_id?: string;
  telemetry?: AssetTelemetry | null;
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

