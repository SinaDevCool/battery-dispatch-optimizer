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
  assumption_basis?: TableRow[];
  best_contract?: HedgeContract | null;
  contract_source?: string;
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
  adapter_id?: string;
  activation_mode?: string;
  activation_policy?: string;
  approval_status?: string;
  automation_lane?: string;
  automation_eligibility?: string;
  bid_granularity?: string;
  bid_id?: string;
  bid_status?: string;
  bid_type?: string;
  capacity_mw?: number;
  confidence_reason?: string;
  delivery_end?: string;
  delivery_start?: string;
  delivery_time?: string;
  energy_mwh?: number;
  gate_closure_label?: string;
  lifecycle_status?: string;
  limit_price_eur_mwh?: number;
  market?: string;
  market_lifecycle_status?: string;
  market_product?: string;
  market_product_id?: string;
  market_segment?: string;
  next_gate_closure_at?: string;
  order_id?: string;
  order_style?: string;
  package_order_type?: string;
  package_schema_version?: string;
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

export type ExecutionBidPackage = JsonObject & {
  adapter_id?: string;
  bid_package_id?: string;
  generated_at?: string;
  market?: string;
  market_segment?: string;
  order_style?: string;
  orders?: ExecutionOrder[];
  package_status?: string;
  submission_mode?: string;
  summary?: JsonObject & {
    buy_order_count?: number;
    order_count?: number;
    reserve_order_count?: number;
    sell_order_count?: number;
    total_buy_mwh?: number;
    total_reserve_mw?: number;
    total_sell_mwh?: number;
    validation_status?: string;
  };
  validation?: JsonObject & {
    checks?: TableRow[];
    status?: string;
  };
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
  bid_package?: ExecutionBidPackage;
  bid_package_status?: string;
  bids?: ExecutionOrder[];
  market?: string;
  market_allocation_status?: string;
  market_lifecycle?: JsonObject;
  market_submission_enabled?: boolean;
  orders?: ExecutionOrder[];
  risk_checks?: ExecutionRiskCheck[];
  signal_id?: number;
  status?: string;
  summary?: JsonObject & {
    expected_pnl_eur?: number;
    max_daily_loss_eur?: number;
    market_gate_closure?: string;
    order_style?: string;
    order_count?: number;
    package_status?: string;
    package_validation_status?: string;
    profit_per_mw_day?: number;
    reserve_order_count?: number;
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
  capacity_mw?: number;
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

export type ExecutionPaperAward = TableRow & {
  award_id?: string;
  bid_id?: string;
  capacity_mw?: number;
  clearing_price_eur_mwh?: number;
  direction?: string;
  execution_style?: string;
  fill_ratio?: number;
  product?: string;
  status?: string;
};

export type ExecutionPaperTrade = TableRow & {
  adapter_id?: string;
  asset_id?: string;
  audit?: TableRow[];
  awards?: ExecutionPaperAward[];
  bid_lifecycle?: ExecutionLifecycleStep[];
  bids?: ExecutionOrder[];
  execution_proposal_id?: number;
  fills?: ExecutionPaperFill[];
  generated_at?: string;
  lifecycle_status?: string;
  market_execution_model?: string;
  mode?: string;
  paper_trade_id?: number;
  proposal_generated_at?: string;
  status?: string;
  settlement_basis?: string;
  summary?: TableRow & {
    accepted_order_count?: number;
    awarded_capacity_mw?: number;
    buy_cost_eur?: number;
    expected_pnl_eur?: number;
    filled_order_count?: number;
    order_count?: number;
    paper_pnl_eur?: number;
    paper_vs_expected_delta_eur?: number;
    rejected_order_count?: number;
    reserve_revenue_eur?: number;
    sell_revenue_eur?: number;
    total_filled_mwh?: number;
  };
  validation?: JsonObject & {
    checks?: TableRow[];
    status?: string;
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
  awarded_capacity_mw?: number | null;
  expected_pnl_eur?: number;
  paper_delta_eur?: number | null;
  paper_pnl_eur?: number | null;
  realized_delta_eur?: number | null;
  realized_pnl_eur?: number | null;
  reserve_revenue_eur?: number | null;
  total_filled_mwh?: number | null;
};

export type SettlementReconciliation = JsonObject & {
  asset_id?: string;
  evidence_status?: JsonObject;
  generated_at?: string;
  links?: JsonObject;
  market_execution_model?: string;
  primary_variance_driver?: string;
  recommended_actions?: string[];
  settlement_basis?: string;
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

export type LiveTradingRouteReadiness = TableRow & {
  adapter_id?: string;
  allocated_power_mw?: number;
  blocker_count?: number;
  blocking_reasons?: string[];
  commercial_product_id?: string;
  connector_tier?: string;
  expected_revenue_eur?: number;
  live_submission?: boolean;
  market_gate_status?: string;
  market_name?: string;
  market_segment?: string;
  mode?: string;
  next_action?: string;
  next_gate_closure_at?: string;
  readiness_score?: number;
  recommendation_status?: string;
  trading_clock_status?: string;
  unlock_action?: JsonObject & {
    adapter_id?: string;
    auto_resolvable?: boolean;
    category?: string;
    href?: string;
    label?: string;
    message?: string;
    owner?: string;
    resolution_endpoint?: string | null;
    severity?: string;
  };
  unlock_category?: string;
  unlock_label?: string;
  unlock_owner?: string;
  unlock_severity?: string;
  venue?: string;
};

export type LiveTradingRunbookStep = TableRow & {
  href?: string;
  label?: string;
  next_action?: string;
  status?: string;
  step_id?: string;
};

export type LiveTradingReadinessResponse = ApiEnvelope<{
  asset_id?: string;
  country?: string;
  evidence?: JsonObject;
  generated_at?: string;
  go_live_status?: string;
  live_trading_readiness_score?: number;
  mode_recommendation?: string;
  next_best_action?: JsonObject & {
    auto_resolvable?: boolean;
    href?: string;
    label?: string;
    owner?: string;
    resolution_endpoint?: string | null;
  };
  route_readiness?: LiveTradingRouteReadiness[];
  runbook?: JsonObject & {
    blockers?: TableRow[];
    remediation_queue?: AutomationRemediationItem[];
    steps?: LiveTradingRunbookStep[];
  };
  summary?: JsonObject & {
    advisory_route_count?: number;
    best_route?: string | null;
    best_route_mode?: string | null;
    blocked_route_count?: number;
    control_blocker_count?: number;
    forecast_confidence_band?: string;
    forecast_confidence_score?: number;
    handshake_ready_count?: number;
    handshake_target_count?: number;
    live_ready_route_count?: number;
    paper_ready_route_count?: number;
    route_count?: number;
    strategy_mode?: string;
    supervised_ready_route_count?: number;
  };
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
  automation_lane?: string;
  automation_blocking_level?: string;
  bid_granularity?: string;
  credential_keys?: string[];
  family?: string;
  gate_closure_label?: string;
  connector_contract_status?: string;
  connector_family?: string;
  connector_methods?: string[];
  audit_event_count?: number;
  blocked_reasons?: string[];
  certified_for_live?: boolean;
  certified_for_paper?: boolean;
  certified_for_supervised_live?: boolean;
  integration_type?: string;
  implemented_methods?: string[];
  lifecycle_status?: string;
  live_enabled_methods?: string[];
  live_method_count?: number;
  market_lifecycle?: JsonObject;
  method_coverage?: number;
  method_count?: number;
  minutes_to_gate_closure?: number;
  missing_methods?: string[];
  missing_controls?: string[];
  missing_credentials?: string[];
  next_certification_action?: string;
  next_deadline_action?: string;
  next_gate_closure_at?: string;
  next_integration_action?: string;
  order_style?: string;
  official_api_blockers?: string[];
  official_api_check_count?: number;
  official_api_checks?: TableRow[];
  official_api_compliance_score?: number;
  official_api_compliance_status?: string;
  official_api_next_action?: string;
  official_api_passed_count?: number;
  official_system?: string;
  paper_supported?: boolean;
  passed_method_count?: number;
  preview_methods?: string[];
  preview_available?: boolean;
  priority?: number;
  production_readiness_tier?: string;
  readiness_score?: number;
  required_evidence?: string[];
  raw_reference_fields?: string[];
  route_credential_status?: string;
  route_missing_credentials?: string[];
  route_missing_env_keys?: string[];
  route_onboarding_next_action?: string;
  route_handshake_blockers?: string[];
  route_handshake_next_action?: string;
  route_handshake_ready?: boolean;
  route_handshake_status?: string;
  route_handshake_target_count?: number;
  route_handshake_targets?: string[];
  route_certification_blockers?: string[];
  route_certification_evidence?: JsonObject;
  route_certification_next_action?: string;
  route_certification_rank?: number;
  route_certification_score?: number;
  route_certification_stage?: string;
  route_certification_status?: string;
  sandbox_certification_status?: string;
  sandbox_results?: TableRow[];
  supervised_live_blockers?: string[];
  supervised_live_candidate?: boolean;
  supervised_live_checks?: TableRow[];
  supervised_live_gate_status?: string;
  supervised_live_next_action?: string;
  synthetic_order_count?: number;
  gate_check_count?: number;
  gate_passed_count?: number;
  gate_score?: number;
  paper_ready_live_blocked?: boolean;
  supported_order_types?: string[];
  trading_clock_status?: string;
  contract_next_action?: string;
};

export type RouteAutomationCertification = TableRow & {
  adapter_id?: string;
  adapter_name?: string;
  certified_for_live?: boolean;
  certified_for_paper?: boolean;
  certified_for_supervised?: boolean;
  latest_route_drill_at?: string;
  latest_route_drill_event_id?: number;
  latest_route_drill_status?: string;
  latest_route_drill_target_count?: number;
  market_segment?: string;
  official_api_compliance_status?: string;
  official_system?: string;
  route_certification_blockers?: string[];
  route_certification_evidence?: JsonObject;
  route_certification_next_action?: string;
  route_certification_rank?: number;
  route_certification_score?: number;
  route_certification_stage?: string;
  route_certification_status?: string;
  venue?: string;
};

export type OfficialApiComplianceRoute = TableRow & {
  access_model?: string;
  adapter_id?: string;
  fail_closed?: boolean;
  official_api_blockers?: string[];
  official_api_check_count?: number;
  official_api_checks?: TableRow[];
  official_api_compliance_score?: number;
  official_api_compliance_status?: string;
  official_api_next_action?: string;
  official_api_passed_count?: number;
  official_system?: string;
  public_download_reference?: string;
  public_reference?: string;
  required_access_modes?: string[];
};

export type OfficialApiEvidenceRequirement = TableRow & {
  access_model?: string;
  adapter_id?: string;
  evidence_expired?: boolean;
  evidence_owner?: string | null;
  evidence_readiness?: string;
  evidence_reference?: string | null;
  evidence_status?: string;
  evidence_type?: string | null;
  evidence_valid?: boolean;
  expires_at?: string | null;
  label?: string;
  next_action?: string;
  official_system?: string;
  public_download_reference?: string;
  public_reference?: string;
  recorded_at?: string | null;
  requirement_id?: string;
  required_env_keys?: string[];
  required_value?: string;
  review_at?: string | null;
  unlocks_mode?: string | null;
};

export type OfficialApiEvidenceRecord = TableRow & {
  adapter_id?: string;
  evidence_owner?: string | null;
  evidence_reference?: string | null;
  evidence_status?: string;
  evidence_type?: string | null;
  expires_at?: string | null;
  label?: string;
  official_system?: string;
  recorded_at?: string;
  requirement_id?: string;
  review_at?: string | null;
  unlocks_mode?: string | null;
};

export type OfficialApiEvidenceVaultResponse = ApiEnvelope<{
  country?: string;
  evidence_records?: OfficialApiEvidenceRecord[];
  evidence_vault_status?: string;
  generated_at?: string;
  recommended_actions?: string[];
  requirements?: OfficialApiEvidenceRequirement[];
  summary?: JsonObject & {
    approved_evidence_count?: number;
    expired_evidence_count?: number;
    missing_evidence_count?: number;
    required_evidence_count?: number;
    review_evidence_count?: number;
  };
}>;

export type MarketConnectorReadinessResponse = ApiEnvelope<{
  connector_status?: string;
  connector_contract_status?: string;
  credential_readiness_status?: string;
  handshake_readiness_status?: string;
  handshake_env_checklist?: LiveAdapterHandshakeEnvItem[];
  handshake_env_activation_guide?: LiveAdapterHandshakeEnvActivationGuide[];
  official_api_compliance_status?: string;
  official_api_compliance?: OfficialApiComplianceRoute[];
  route_certification_status?: string;
  route_certifications?: RouteAutomationCertification[];
  sandbox_certification_status?: string;
  supervised_live_gate_status?: string;
  connectors?: MarketConnectorReadiness[];
  country?: string;
  generated_at?: string;
  integrations?: MarketConnectorReadiness[];
  recommended_actions?: string[];
  summary?: JsonObject & {
    ancillary_count?: number;
    average_passed_method_count?: number;
    average_gate_score?: number;
    average_official_api_compliance_score?: number;
    average_readiness_score?: number;
    closed_gate_count?: number;
    connector_count?: number;
    connector_contract_count?: number;
    credential_blocked_route_count?: number;
    credential_count?: number;
    credential_ready_route_count?: number;
    handshake_blocked_count?: number;
    handshake_disabled_count?: number;
    env_checklist_count?: number;
    env_configured_count?: number;
    env_endpoint_count?: number;
    env_missing_count?: number;
    env_mode_count?: number;
    env_secret_count?: number;
    env_activation_route_count?: number;
    env_activation_configured_route_count?: number;
    env_activation_setup_required_route_count?: number;
    handshake_ready_count?: number;
    handshake_target_count?: number;
    route_handshake_blocked_count?: number;
    route_handshake_count?: number;
    route_handshake_disabled_count?: number;
    route_handshake_ready_count?: number;
    configured_credential_count?: number;
    configured_market_lifecycle_count?: number;
    credentials_required_count?: number;
    data_feed_count?: number;
    epex_count?: number;
    live_auto_blocking_count?: number;
    live_certified_count?: number;
    live_contract_ready_count?: number;
    live_submission_count?: number;
    missing_credential_count?: number;
    missing_method_count?: number;
    official_api_blocked_route_count?: number;
    official_api_check_count?: number;
    official_api_compliant_route_count?: number;
    official_api_passed_check_count?: number;
    official_api_route_count?: number;
    partial_contract_count?: number;
    paper_certified_count?: number;
    preview_ready_count?: number;
    preview_contract_ready_count?: number;
    production_ready_count?: number;
    ready_for_drill_count?: number;
    route_certification_count?: number;
    average_route_certification_score?: number;
    certified_route_count?: number;
    drill_failed_count?: number;
    live_certified_route_count?: number;
    not_configured_count?: number;
    paper_certified_route_count?: number;
    supervised_certified_route_count?: number;
    sandbox_certification_count?: number;
    supervised_live_blocked_count?: number;
    supervised_live_candidate_count?: number;
    supervised_live_gate_count?: number;
    paper_ready_live_blocked_count?: number;
    supervised_live_certified_count?: number;
    supervised_auto_blocking_count?: number;
    urgent_gate_count?: number;
    next_gate_closure_at?: string;
  };
}>;

export type CredentialReadinessItem = TableRow & {
  accepted_env_keys?: string[];
  blocks_mode?: string;
  configured?: boolean;
  configured_env_key?: string;
  credential_id?: string;
  group?: string;
  label?: string;
  missing_env_keys?: string[];
  next_action?: string;
  required_for?: string[];
  secret_value_exposed?: boolean;
  status?: string;
};

export type CredentialRouteRequirement = TableRow & {
  adapter_id?: string;
  configured_credential_count?: number;
  credential_status?: string;
  missing_credential_count?: number;
  missing_credentials?: string[];
  missing_env_keys?: string[];
  onboarding_next_action?: string;
  required_credential_count?: number;
  required_credentials?: string[];
};

export type CredentialReadinessResponse = ApiEnvelope<{
  credential_readiness_status?: string;
  credentials?: CredentialReadinessItem[];
  generated_at?: string;
  recommended_actions?: string[];
  route_requirements?: CredentialRouteRequirement[];
  summary?: JsonObject & {
    credential_blocked_route_count?: number;
    credential_count?: number;
    credential_ready_route_count?: number;
    configured_credential_count?: number;
    missing_credential_count?: number;
    route_count?: number;
  };
}>;

export type LiveAdapterHandshakeTarget = TableRow & {
  audit_event_captured?: boolean;
  auth_attempt_mode?: string;
  blockers?: string[];
  configured_endpoint_key?: string;
  credential_status?: string;
  default_endpoint_used?: boolean;
  endpoint_env_keys?: string[];
  endpoint_status?: string;
  expected_response_schema?: string[];
  group?: string;
  handshake_mode?: string;
  handshake_status?: string;
  label?: string;
  last_successful_handshake_at?: string | null;
  latest_drill_at?: string;
  latest_drill_event_id?: number;
  latest_drill_status?: string;
  missing_credentials?: string[];
  missing_env_keys?: string[];
  next_handshake_action?: string;
  no_order_submission?: boolean;
  order_submission_performed?: boolean;
  required_for?: string[];
  response_schema_status?: string;
  target_id?: string;
};

export type LiveAdapterHandshakeEnvItem = TableRow & {
  blocks_routes?: string[];
  configured_env_key?: string;
  credential_id?: string;
  env_keys?: string[];
  group?: string;
  item_type?: string;
  next_action?: string;
  required_value?: string;
  secret?: boolean;
  status?: string;
  target?: string;
  target_id?: string;
  value_exposed?: boolean;
};

export type LiveAdapterHandshakeEnvActivationGuide = TableRow & {
  activation_status?: string;
  adapter_id?: string;
  configured_count?: number;
  configured_env_keys?: string[];
  endpoint_status?: string;
  handshake_drill_enabled_after_setup?: boolean;
  market_family?: string;
  missing_count?: number;
  missing_env_keys?: string[];
  mode_status?: string;
  next_action?: string;
  next_unlock_category?: string;
  next_unlock_label?: string;
  required_count?: number;
  required_env_keys?: string[];
  required_mode?: string;
  route_label?: string;
  route_drill_endpoint?: string | null;
  run_drill_endpoint?: string | null;
  safe_deployment_steps?: string[];
  secret_count?: number;
  secret_env_keys?: string[];
  secret_values_exposed?: boolean;
  system_route_drill_endpoint?: string | null;
};

export type LiveAdapterHandshakeDrill = TableRow & {
  action?: string;
  asset_id?: string;
  automation_event_id?: number;
  blocked_count?: number;
  created_at?: string;
  order_submission_performed?: boolean;
  passed_count?: number;
  results?: TableRow[];
  route_id?: string;
  status?: string;
  target_count?: number;
  target_id?: string;
};

export type LiveAdapterRouteHandshake = TableRow & {
  adapter_id?: string;
  route_handshake_blockers?: string[];
  route_handshake_next_action?: string;
  route_handshake_ready?: boolean;
  route_handshake_ready_count?: number;
  route_handshake_status?: string;
  route_handshake_target_count?: number;
  route_handshake_targets?: string[];
};

export type LiveAdapterHandshakeResponse = ApiEnvelope<{
  country?: string;
  generated_at?: string;
  handshake_readiness_status?: string;
  env_checklist?: LiveAdapterHandshakeEnvItem[];
  env_activation_guide?: LiveAdapterHandshakeEnvActivationGuide[];
  recommended_actions?: string[];
  routes?: LiveAdapterRouteHandshake[];
  summary?: JsonObject & {
    handshake_blocked_count?: number;
    handshake_disabled_count?: number;
    env_checklist_count?: number;
    env_configured_count?: number;
    env_endpoint_count?: number;
    env_missing_count?: number;
    env_mode_count?: number;
    env_secret_count?: number;
    handshake_ready_count?: number;
    handshake_target_count?: number;
    route_handshake_blocked_count?: number;
    route_handshake_count?: number;
    route_handshake_disabled_count?: number;
    route_handshake_ready_count?: number;
  };
  targets?: LiveAdapterHandshakeTarget[];
}>;

export type LiveAdapterHandshakeHistoryResponse = ApiEnvelope<{
  asset_id?: string;
  drills?: LiveAdapterHandshakeDrill[];
  event_type?: string;
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
  automation_lane?: string;
  bid_granularity?: string;
  blocking_reasons?: string[];
  commercial_product_id?: string;
  connector_family?: string;
  connector_readiness_score?: number;
  connector_readiness_tier?: string;
  data_dependencies?: string[];
  expected_revenue_eur?: number;
  execution_role?: string;
  gate_closure_label?: string;
  lifecycle_status?: string;
  live_submission?: boolean;
  market_lifecycle?: JsonObject;
  market_gate_missing_controls?: string[];
  market_gate_next_action?: string;
  market_gate_score?: number;
  market_gate_settlement_basis?: string;
  market_gate_status?: string;
  market_name?: string;
  market_segment?: string;
  minutes_to_gate_closure?: number;
  missing_connector_controls?: string[];
  missing_credentials?: string[];
  next_deadline_action?: string;
  next_gate_closure_at?: string;
  operator_next_action?: string;
  order_style?: string;
  preview_status?: string;
  preview_validation_status?: string;
  recommendation_status?: string;
  risk_score?: number;
  required_evidence?: string[];
  supported_order_types?: string[];
  trading_clock_status?: string;
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
    live_ready_route_count?: number;
    market_gate_status?: string;
    paper_only_route_count?: number;
    readiness_score?: number;
    readiness_status?: string;
    supervised_ready_route_count?: number;
    total_allocated_power_mw?: number;
    total_expected_revenue_eur?: number;
  };
}>;

export type MarketAdapterRouteGate = TableRow & {
  adapter_id?: string;
  adapter_name?: string;
  automation_lane?: string;
  blocking_levels?: string[];
  checks?: TableRow[];
  gate_closure_label?: string;
  gate_status?: string;
  live_submission?: boolean;
  market_family?: string;
  missing_controls?: string[];
  next_action?: string;
  order_style?: string;
  readiness_score?: number;
  required_controls?: JsonObject;
  settlement_basis?: string;
  trading_clock_status?: string;
};

export type MarketAdapterReadinessGateResponse = ApiEnvelope<{
  asset_id?: string;
  country?: string;
  evidence?: JsonObject;
  gate_status?: string;
  generated_at?: string;
  recommended_actions?: string[];
  route_gates?: MarketAdapterRouteGate[];
  summary?: JsonObject & {
    ancillary_ready_count?: number;
    average_readiness_score?: number;
    blocked_count?: number;
    epex_ready_count?: number;
    live_ready_count?: number;
    paper_only_count?: number;
    route_count?: number;
    supervised_ready_count?: number;
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

export type MarketSubmissionLifecycleStep = TableRow & {
  evidence?: JsonObject;
  label?: string;
  message?: string;
  owner?: string;
  status?: string;
  step?: string;
};

export type MarketSubmissionLifecycleResponse = ApiEnvelope<{
  adapter_id?: string;
  asset_id?: string;
  blockers?: TableRow[];
  current_step?: MarketSubmissionLifecycleStep | null;
  evidence?: JsonObject;
  generated_at?: string;
  lifecycle_status?: string;
  market_route_status?: string;
  next_action?: string;
  settlement_basis?: string;
  steps?: MarketSubmissionLifecycleStep[];
  summary?: JsonObject & {
    blocked?: number;
    complete?: number;
    review?: number;
    total?: number;
    waiting?: number;
  };
}>;

export type ExecutionRecoveryAction = TableRow & {
  action?: string;
  auto_resolvable?: boolean;
  category?: string;
  label?: string;
  message?: string;
  requires_human_approval?: boolean;
  resolution_endpoint?: string | null;
  safe_to_auto_run?: boolean;
  severity?: string;
  source?: string;
};

export type ExecutionRecoveryPlanResponse = ApiEnvelope<{
  asset_id?: string;
  evidence?: JsonObject;
  generated_at?: string;
  primary_action?: ExecutionRecoveryAction;
  recovery_queue?: ExecutionRecoveryAction[];
  recovery_status?: string;
  root_cause?: JsonObject & {
    category?: string;
    message?: string;
  };
  stuck_step?: MarketSubmissionLifecycleStep;
  summary?: JsonObject & {
    auto_resolvable_count?: number;
    lifecycle_status?: string;
    manual_review_count?: number;
    market_route_status?: string;
  };
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
  asset_id?: string;
  report_file?: string;
  report_name?: string;
  viewer_route?: string;
}>;

export type MonthlyReportListResponse = ApiEnvelope<{
  report_count?: number;
  reports?: TableRow[];
}>;

export type ClientConfigResponse = ApiEnvelope<{
  config?: JsonObject;
}>;

