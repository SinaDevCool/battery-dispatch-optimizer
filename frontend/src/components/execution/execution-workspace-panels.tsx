import { Activity, Send, ShieldCheck, UserCheck } from "lucide-react";

import { ActionButton } from "@/components/action-button";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { ExecutionMetric } from "@/components/execution/execution-metric";
import { AssetTelemetryPanel } from "@/components/execution/market-evidence-panels";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { formatCurrency, formatNumber } from "@/lib/format";
import type {
  AssetMarketAdapterStatusResponse,
  AssetTelemetryResponse,
  AutomationEvent,
  AutomationFreshnessGate,
  AutomationRemediationItem,
  ExecutionApproval,
  ExecutionPaperTrade,
  ExecutionProposal,
  ExecutionReadinessResponse,
  ExecutionRecoveryPlanResponse,
  JsonObject,
  MarketSubmissionLifecycleResponse,
  TableRow,
} from "@/types/api";
import type { PersonaId, PersonaLayer } from "@/lib/personas";

type RefetchExecution = () => Promise<unknown>;

export function ExecutionOverviewPanel({
  approvalData,
  automationStatus,
  bids,
  hardBlockers,
  marketAdapterStatus,
  paperTrade,
  personaId,
  proposal,
  readiness,
  refetchExecution,
  selectedAssetId,
  submission,
  telemetryData,
}: {
  approvalData?: ExecutionApproval | null;
  automationStatus?: string;
  bids: TableRow[];
  hardBlockers: string[];
  marketAdapterStatus?: AssetMarketAdapterStatusResponse;
  paperTrade?: TableRow | null;
  personaId: PersonaId;
  proposal?: ExecutionProposal | null;
  readiness?: ExecutionReadinessResponse;
  refetchExecution: RefetchExecution;
  selectedAssetId: string;
  submission?: TableRow | null;
  telemetryData: AssetTelemetryResponse["telemetry"];
}) {
  const framing = getOverviewPersonaFraming(personaId);

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
      <SectionCard
        action={<StatusPill tone={automationTone(automationStatus)}>{automationStatus ?? "not evaluated"}</StatusPill>}
        title={framing.commandTitle}
      >
        <div className="mb-5 flex flex-wrap gap-3">
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/proposal/build`}
            label={framing.buildProposalLabel}
            refetch={refetchExecution}
            variant="primary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/approval/request`}
            label={framing.requestGateLabel}
            refetch={refetchExecution}
            variant="secondary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/approval/approve`}
            label={framing.clearGateLabel}
            refetch={refetchExecution}
            variant="secondary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/paper-trade/run`}
            label={framing.runPaperLabel}
            refetch={refetchExecution}
            variant="secondary"
          />
          <ActionButton
            endpoint={`/assets/${selectedAssetId}/execution/demo-submit`}
            label={framing.simulateSubmissionLabel}
            refetch={refetchExecution}
            variant="secondary"
          />
        </div>
        <div className="grid gap-3 md:grid-cols-5">
          <WorkflowStep icon={<Activity className="h-4 w-4" />} label="Signal" status={proposal?.signal_id ? "complete" : "pending"} />
          <WorkflowStep icon={<ShieldCheck className="h-4 w-4" />} label="Risk" status={hardBlockers.length ? "blocked" : bids.length ? "complete" : "pending"} />
          <WorkflowStep icon={<UserCheck className="h-4 w-4" />} label="Human gate" status={approvalData?.status === "approved" ? "complete" : "required"} />
          <WorkflowStep icon={<Activity className="h-4 w-4" />} label="Paper" status={paperTrade ? "complete" : "pending"} />
          <WorkflowStep icon={<Send className="h-4 w-4" />} label="Submit" status={submission ? "complete" : "disabled"} />
        </div>
      </SectionCard>

      <div className="space-y-5">
        <SectionCard
          action={<StatusPill tone={readinessTone(readiness?.readiness_status)}>{readiness?.readiness_status ?? "not evaluated"}</StatusPill>}
          title={framing.evidenceTitle}
        >
          <div className="grid gap-3 md:grid-cols-2">
            <ExecutionMetric
              label="Readiness score"
              value={formatNumber(readiness?.readiness_score, 1)}
            />
            <ExecutionMetric
              label="Connected markets"
              value={formatNumber(marketAdapterStatus?.connected_adapter_count, 0)}
            />
            <ExecutionMetric
              label="SOC"
              value={`${formatNumber(telemetryData?.soc_percent, 1)}%`}
            />
            <ExecutionMetric
              label="Draft bids"
              value={formatNumber(bids.length, 0)}
            />
          </div>
          <div className="mt-4">
            <DataTable
              columns={["evidence", "status", "automation_use"]}
              rows={[
                {
                  automation_use: "Blocks live submission when readiness is red",
                  evidence: "Execution readiness",
                  status: readiness?.readiness_status ?? "-",
                },
                {
                  automation_use: "Selects whether EPEX or ancillary routes can be submitted",
                  evidence: "Market adapters",
                  status: marketAdapterStatus?.market_adapter_status ?? "-",
                },
                {
                  automation_use: "Validates physical ability to follow automated orders",
                  evidence: "Asset telemetry",
                  status: telemetryData?.availability_status ?? "missing",
                },
                {
                  automation_use: "Carries the proposed automated order package",
                  evidence: "Bid package",
                  status: proposal?.status ?? "-",
                },
              ]}
            />
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

function getOverviewPersonaFraming(personaId: PersonaId) {
  const defaults = {
    buildProposalLabel: "Build proposal",
    clearGateLabel: "Clear human gate",
    commandTitle: "Automation command sequence",
    evidenceTitle: "Automation evidence snapshot",
    requestGateLabel: "Request human gate",
    runPaperLabel: "Run auto paper",
    simulateSubmissionLabel: "Simulate submission",
  };

  const framing: Partial<Record<PersonaId, typeof defaults>> = {
    automation_operator: {
      buildProposalLabel: "Build order package",
      clearGateLabel: "Clear live gate",
      commandTitle: "Automation run sequence",
      evidenceTitle: "Operator readiness snapshot",
      requestGateLabel: "Request gate review",
      runPaperLabel: "Run paper validation",
      simulateSubmissionLabel: "Run submission drill",
    },
    market_operations: {
      buildProposalLabel: "Build routed package",
      clearGateLabel: "Clear route gate",
      commandTitle: "Market route command sequence",
      evidenceTitle: "Market operations evidence",
      requestGateLabel: "Request route approval",
      runPaperLabel: "Validate route paper",
      simulateSubmissionLabel: "Run route drill",
    },
    risk_compliance: {
      buildProposalLabel: "Create review packet",
      clearGateLabel: "Approve governed gate",
      commandTitle: "Governed automation sequence",
      evidenceTitle: "Risk evidence snapshot",
      requestGateLabel: "Request approval evidence",
      runPaperLabel: "Run control test",
      simulateSubmissionLabel: "Simulate controlled submission",
    },
    trading_desk: {
      buildProposalLabel: "Build tradable package",
      clearGateLabel: "Clear desk gate",
      commandTitle: "Trading desk execution sequence",
      evidenceTitle: "Desk readiness snapshot",
      requestGateLabel: "Request desk approval",
      runPaperLabel: "Run paper PnL",
      simulateSubmissionLabel: "Test submission path",
    },
  };

  return framing[personaId] ?? defaults;
}

export function ExecutionRiskApprovalPanel({
  approvalData,
  automationBlockers,
  automationStatus,
  confidence,
  freshnessGates,
  guardrailSummary,
  guardrails,
  hardBlockers,
  personaId,
  refetchExecution,
  recoveryPlan,
  remediationItems,
  selectedAssetId,
}: {
  approvalData?: ExecutionApproval | null;
  automationBlockers: string[];
  automationStatus?: string;
  confidence?: JsonObject;
  freshnessGates: AutomationFreshnessGate[];
  guardrailSummary: JsonObject;
  guardrails: TableRow[];
  hardBlockers: string[];
  personaId: PersonaId;
  refetchExecution: RefetchExecution;
  recoveryPlan?: ExecutionRecoveryPlanResponse;
  remediationItems: AutomationRemediationItem[];
  selectedAssetId: string;
}) {
  const framing = getRiskApprovalPersonaFraming(personaId);
  const riskPolicy = confidence?.risk_policy as JsonObject | undefined;
  const blockedGuardrails = Number(guardrailSummary.blocked ?? 0);
  const reviewGuardrails = Number(guardrailSummary.review ?? 0);
  const staleFreshnessGates = freshnessGates.filter((gate) => gate.freshness_status !== "fresh");
  const totalBlockers = blockedGuardrails + hardBlockers.length + automationBlockers.length + staleFreshnessGates.length;
  const decisionStatus = totalBlockers > 0 ? "blocked" : approvalData?.status === "approved" ? "approved" : "review";
  const decisionTitle =
    decisionStatus === "approved"
      ? "Automation can advance under approved risk limits"
      : "Hold automation until the risk and evidence gates are clear";
  const nextAction =
    textValue(
      recoveryPlan?.primary_action?.required_action ??
        recoveryPlan?.primary_action?.message ??
        remediationItems[0]?.required_action ??
        remediationItems[0]?.message ??
        hardBlockers[0] ??
        automationBlockers[0],
      "Keep guardrails monitored before increasing automation mode.",
    );
  const unblockRows = buildRiskUnblockRows({
    automationBlockers,
    freshnessGates,
    hardBlockers,
    remediationItems,
  });
  const gateRows = [
    {
      evidence: `${formatNumber(guardrailSummary.passed, 0)} passed / ${formatNumber(reviewGuardrails, 0)} review / ${formatNumber(blockedGuardrails, 0)} blocked`,
      gate: "Automation guardrails",
      next_action: blockedGuardrails ? "Clear blocked guardrails before live trading" : "Keep guardrails monitored",
      status: blockedGuardrails ? "blocked" : reviewGuardrails ? "review" : "passed",
    },
    {
      evidence: approvalData?.execution_proposal_id ? `Proposal ${approvalData.execution_proposal_id}` : "No proposal approval evidence",
      gate: "Human approval",
      next_action: approvalData?.status === "approved" ? "Approval available for current proposal" : "Request or clear the human gate",
      status: approvalData?.status ?? "missing",
    },
    {
      evidence: `Score ${formatNumber(confidence?.confidence_score, 1)} / multiplier ${formatNumber(riskPolicy?.volume_multiplier, 2)}`,
      gate: "Forecast confidence",
      next_action: String(confidence?.automation_eligibility ?? "Validate forecast performance before live escalation"),
      status: String(confidence?.confidence_band ?? "unscored"),
    },
    {
      evidence: `${freshnessGates.length - staleFreshnessGates.length}/${freshnessGates.length} fresh`,
      gate: "Freshness and trust",
      next_action: staleFreshnessGates[0]?.required_action ?? "All freshness gates are current",
      status: staleFreshnessGates.length ? "review" : "fresh",
    },
    {
      evidence: `${hardBlockers.length} hard blocker(s)`,
      gate: "Hard blockers",
      next_action: hardBlockers[0] ?? "No hard blockers",
      status: hardBlockers.length ? "blocked" : "passed",
    },
    {
      evidence: `${automationBlockers.length} automation blocker(s)`,
      gate: "Automation blockers",
      next_action: automationBlockers[0] ?? "No automation blockers",
      status: automationBlockers.length ? "blocked" : "passed",
    },
  ];

  return (
    <div className="space-y-5">
      <SectionCard
        action={<StatusPill tone={gateTone(decisionStatus)}>{decisionStatus}</StatusPill>}
        title={framing.decisionTitle}
      >
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(420px,0.75fr)]">
          <div className="rounded border border-slate-700 bg-slate-950/40 p-4">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-slate-500">Decision</p>
            <p className="mt-2 text-lg font-semibold text-slate-50">{decisionTitle}</p>
            <div className="mt-4 rounded border border-sky-700 bg-sky-950/50 px-3 py-2 text-sm font-medium text-sky-100">
              {nextAction}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <ExecutionMetric label="Automation mode" value={automationStatus ?? "not evaluated"} />
            <ExecutionMetric label="Blocked gates" value={formatNumber(totalBlockers, 0)} />
            <ExecutionMetric label="Review gates" value={formatNumber(reviewGuardrails + remediationItems.length, 0)} />
            <ExecutionMetric label="Human gate" value={approvalData?.status ?? "missing"} />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <ActionButton endpoint={`/assets/${selectedAssetId}/execution/approval/request`} label={framing.requestGateLabel} refetch={refetchExecution} variant="primary" />
          <ActionButton endpoint={`/assets/${selectedAssetId}/execution/approval/approve`} label={framing.clearGateLabel} refetch={refetchExecution} variant="secondary" />
          <ActionButton endpoint={`/assets/${selectedAssetId}/execution/approval/reject`} label={framing.blockGateLabel} refetch={refetchExecution} variant="secondary" />
        </div>
      </SectionCard>

      <SectionCard
        action={<StatusPill tone={unblockRows.length ? "amber" : "emerald"}>{unblockRows.length ? "priority queue" : "clear"}</StatusPill>}
        title={framing.pathTitle}
      >
        <DataTable columns={["priority", "source", "blocker", "owner", "next_action"]} rows={unblockRows.slice(0, 10)} />
      </SectionCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
        <SectionCard title={framing.gateMatrixTitle}>
          <DataTable columns={["gate", "status", "evidence", "next_action"]} rows={gateRows} />
        </SectionCard>
        <SectionCard
          action={<StatusPill tone={approvalTone(approvalData?.status)}>{approvalData?.status ?? "missing"}</StatusPill>}
          title={framing.humanGateTitle}
        >
          <DataTable
            columns={["approval_id", "execution_proposal_id", "status", "requested_by", "decided_by", "reason"]}
            rows={approvalData ? [approvalData] : []}
          />
        </SectionCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard
          action={<StatusPill tone={automationTone(automationStatus)}>{automationStatus ?? "not evaluated"}</StatusPill>}
          title={framing.guardrailTitle}
        >
          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <ExecutionMetric label="Passed" value={formatNumber(guardrailSummary.passed, 0)} />
            <ExecutionMetric label="Review" value={formatNumber(guardrailSummary.review, 0)} />
            <ExecutionMetric label="Blocked" value={formatNumber(guardrailSummary.blocked, 0)} />
          </div>
          <DataTable columns={["guardrail", "status", "message", "context"]} rows={guardrails.slice(0, 8)} />
        </SectionCard>
        <SectionCard
          action={<StatusPill tone={confidenceTone(confidence?.confidence_band)}>{String(confidence?.confidence_band ?? "unscored")}</StatusPill>}
          title={framing.confidenceTitle}
        >
          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <ExecutionMetric label="Confidence score" value={formatNumber(confidence?.confidence_score, 1)} />
            <ExecutionMetric label="Volume multiplier" value={formatNumber(riskPolicy?.volume_multiplier, 2)} />
            <ExecutionMetric label="Automation" value={String(confidence?.automation_eligibility ?? "-")} />
          </div>
          <DataTable
            columns={["forecast_actual_id", "forecast_model", "mae_eur_per_mwh", "rmse_eur_per_mwh", "revenue_delta_eur", "score"]}
            rows={((confidence?.evidence as TableRow[]) ?? []).slice(0, 8)}
          />
        </SectionCard>
      </div>

      <SectionCard
        action={<StatusPill tone={staleFreshnessGates.length ? "amber" : "emerald"}>{staleFreshnessGates.length ? "review" : "fresh"}</StatusPill>}
        title={framing.freshnessTitle}
      >
        <DataTable
          columns={["gate_id", "label", "freshness_status", "age_minutes", "max_age_minutes", "required_action"]}
          rows={freshnessGates.slice(0, 8)}
        />
      </SectionCard>
    </div>
  );
}

function getRiskApprovalPersonaFraming(personaId: PersonaId) {
  const defaults = {
    blockGateLabel: "Block gate",
    clearGateLabel: "Clear gate",
    confidenceTitle: "Forecast confidence evidence",
    decisionTitle: "Risk-to-live decision",
    freshnessTitle: "Freshness and trust evidence",
    gateMatrixTitle: "Gate matrix",
    guardrailTitle: "Guardrail evidence",
    humanGateTitle: "Human gate evidence",
    pathTitle: "Path to live automation",
    requestGateLabel: "Request human gate",
  };

  const framing: Partial<Record<PersonaId, typeof defaults>> = {
    automation_operator: {
      blockGateLabel: "Hold automation",
      clearGateLabel: "Clear operator gate",
      confidenceTitle: "Forecast control input",
      decisionTitle: "Operator go-live gate",
      freshnessTitle: "Fresh data gates",
      gateMatrixTitle: "Automation blocker matrix",
      guardrailTitle: "Automation guardrails",
      humanGateTitle: "Operator approval evidence",
      pathTitle: "Operator unblock queue",
      requestGateLabel: "Request operator review",
    },
    market_operations: {
      blockGateLabel: "Block route",
      clearGateLabel: "Clear route gate",
      confidenceTitle: "Route confidence evidence",
      decisionTitle: "Market route approval gate",
      freshnessTitle: "Market data freshness",
      gateMatrixTitle: "Route gate matrix",
      guardrailTitle: "Route guardrails",
      humanGateTitle: "Route approval evidence",
      pathTitle: "Route unblock queue",
      requestGateLabel: "Request route approval",
    },
    risk_compliance: {
      blockGateLabel: "Reject gate",
      clearGateLabel: "Approve governed gate",
      confidenceTitle: "Model confidence controls",
      decisionTitle: "Governance approval decision",
      freshnessTitle: "Evidence freshness controls",
      gateMatrixTitle: "Control matrix",
      guardrailTitle: "Policy guardrail evidence",
      humanGateTitle: "Approval record",
      pathTitle: "Compliance remediation queue",
      requestGateLabel: "Request approval record",
    },
    trading_desk: {
      blockGateLabel: "Hold desk action",
      clearGateLabel: "Clear desk gate",
      confidenceTitle: "Desk confidence evidence",
      decisionTitle: "Desk go/no-go decision",
      freshnessTitle: "Market freshness evidence",
      gateMatrixTitle: "Desk gate matrix",
      guardrailTitle: "Trading guardrails",
      humanGateTitle: "Desk approval evidence",
      pathTitle: "Desk unblock path",
      requestGateLabel: "Request desk approval",
    },
  };

  return framing[personaId] ?? defaults;
}

export function ExecutionSimulationPanel({
  paperFills,
  paperHistoryRows,
  paperTrade,
  paperTradeRunCount,
  personaId,
  refetchExecution,
  selectedAssetId,
  submission,
  submissionLifecycle,
  submissionSummary,
}: {
  paperFills: TableRow[];
  paperHistoryRows: TableRow[];
  paperTrade?: ExecutionPaperTrade | null;
  paperTradeRunCount: number;
  personaId: PersonaId;
  refetchExecution: RefetchExecution;
  selectedAssetId: string;
  submission?: TableRow | null;
  submissionLifecycle?: MarketSubmissionLifecycleResponse;
  submissionSummary: JsonObject;
}) {
  const lifecycleSteps = submissionLifecycle?.steps ?? [];
  const framing = getSimulationPersonaFraming(personaId);

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <div className="space-y-5">
        <SectionCard
          action={<ActionButton endpoint={`/assets/${selectedAssetId}/execution/paper-trade/run`} label={framing.runPaperLabel} refetch={refetchExecution} variant="primary" />}
          title={framing.paperTitle}
        >
          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <ExecutionMetric
              label="Execution model"
              value={String(paperTrade?.market_execution_model ?? "-").replaceAll("_", " ")}
            />
            <ExecutionMetric
              label="Settlement basis"
              value={String(paperTrade?.settlement_basis ?? "-").replaceAll("_", " ")}
            />
            <ExecutionMetric
              label="Validation"
              value={String(paperTrade?.validation?.status ?? "-")}
            />
          </div>
          <DataTable
            columns={[
              "delivery_time",
              "market_product_id",
              "execution_detail",
              "side",
              "filled_volume_mwh",
              "capacity_mw",
              "fill_price_eur_mwh",
              "notional_eur",
              "status",
            ]}
            rows={paperFills.slice(0, 8)}
          />
        </SectionCard>
        <SectionCard
          action={<StatusPill tone={paperTrade?.awards?.length ? "emerald" : "slate"}>{paperTrade?.awards?.length ?? 0}</StatusPill>}
          title={framing.awardsTitle}
        >
          <div className="mb-4 grid gap-5 xl:grid-cols-2">
            <DataTable
              columns={["award_id", "bid_id", "status", "capacity_mw", "clearing_price_eur_mwh", "fill_ratio"]}
              rows={(paperTrade?.awards ?? []).slice(0, 6)}
            />
            <DataTable
              columns={["check", "status", "message"]}
              rows={(paperTrade?.validation?.checks ?? []).slice(0, 6)}
            />
          </div>
        </SectionCard>
        <SectionCard
          action={<StatusPill tone={paperTradeRunCount ? "emerald" : "slate"}>{paperTradeRunCount} run(s)</StatusPill>}
          title={framing.historyTitle}
        >
          <DataTable
            columns={[
              "paper_trade_id",
              "generated_at",
              "status",
              "filled_order_count",
              "paper_pnl_eur",
              "paper_vs_expected_delta_eur",
            ]}
            rows={paperHistoryRows.slice(0, 6)}
          />
        </SectionCard>
      </div>
      <SectionCard
        action={<ActionButton endpoint={`/assets/${selectedAssetId}/execution/demo-submit`} label={framing.simulateLabel} refetch={refetchExecution} variant="primary" />}
        title={framing.submissionTitle}
      >
        <div className="mb-4 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          <ExecutionMetric
            label="Lifecycle"
            value={String(submissionLifecycle?.lifecycle_status ?? "-").replaceAll("_", " ")}
          />
          <ExecutionMetric
            label="Current step"
            value={submissionLifecycle?.current_step?.label ?? "-"}
          />
          <ExecutionMetric
            label="Route gate"
            value={String(submissionLifecycle?.market_route_status ?? "-").replaceAll("_", " ")}
          />
          <ExecutionMetric label="Submitted" value={formatNumber(submissionSummary.submitted_bid_count, 0)} />
          <ExecutionMetric label="Accepted" value={formatNumber(submissionSummary.accepted_bid_count, 0)} />
          <ExecutionMetric label="Awarded notional" value={formatCurrency(submissionSummary.notional_eur)} />
        </div>
        <div className="mb-4 rounded-lg border border-slate-800 bg-slate-900/45 p-4 text-sm leading-6 text-slate-300">
          {submissionLifecycle?.next_action ?? "Lifecycle evidence is not available yet."}
        </div>
        <DataTable
          columns={["step", "label", "status", "owner", "message"]}
          rows={(lifecycleSteps.length ? lifecycleSteps : ((submission?.lifecycle as TableRow[]) ?? [])).slice(0, 10)}
        />
      </SectionCard>
    </div>
  );
}

function getSimulationPersonaFraming(personaId: PersonaId) {
  const defaults = {
    awardsTitle: "Market awards and validation",
    historyTitle: "Paper trade history",
    paperTitle: "Market-specific paper execution",
    runPaperLabel: "Run paper trade",
    simulateLabel: "Simulate bid submission",
    submissionTitle: "Simulated market submission",
  };

  const frames: Partial<Record<PersonaId, typeof defaults>> = {
    automation_operator: {
      awardsTitle: "Automation validation and awards",
      historyTitle: "Automation paper run history",
      paperTitle: "Automation paper execution",
      runPaperLabel: "Run automation paper test",
      simulateLabel: "Simulate automation submission",
      submissionTitle: "Automation lifecycle simulation",
    },
    trading_desk: {
      awardsTitle: "Desk fills and validation",
      historyTitle: "Desk paper trading history",
      paperTitle: "Desk paper execution",
      runPaperLabel: "Run desk paper trade",
      simulateLabel: "Simulate desk submission",
      submissionTitle: "Desk market submission simulation",
    },
    risk_compliance: {
      awardsTitle: "Risk validation and awards",
      historyTitle: "Paper validation history",
      paperTitle: "Risk paper validation",
      runPaperLabel: "Run paper validation",
      simulateLabel: "Simulate governed submission",
      submissionTitle: "Governed market submission simulation",
    },
    market_operations: {
      awardsTitle: "Route awards and validation",
      historyTitle: "Route paper run history",
      paperTitle: "Route paper execution",
      runPaperLabel: "Run route paper trade",
      simulateLabel: "Simulate route submission",
      submissionTitle: "Route lifecycle simulation",
    },
  };

  return frames[personaId] ?? defaults;
}

export function ExecutionSettlementPanel({
  personaId,
  refetchExecution,
  selectedAssetId,
  settlementData,
  settlementSummary,
  varianceDrivers,
}: {
  personaId: PersonaId;
  refetchExecution: RefetchExecution;
  selectedAssetId: string;
  settlementData?: JsonObject | null;
  settlementSummary: JsonObject;
  varianceDrivers: TableRow[];
}) {
  const settlementFraming = getSettlementPersonaFraming(personaId);
  const evidenceStatus = (settlementData?.evidence_status ?? {}) as JsonObject;
  const links = (settlementData?.links ?? {}) as JsonObject;
  const recommendedActions = ((settlementData?.recommended_actions as string[] | undefined) ?? [])
    .map(String);
  const missingEvidence = buildMissingSettlementEvidence(evidenceStatus);
  const settlementStatus = String(settlementData?.status ?? "not reconciled");
  const paperDelta = settlementSummary.paper_delta_eur;
  const realizedDelta = settlementSummary.realized_delta_eur;
  const decision =
    settlementStatus === "settled"
      ? settlementFraming.settledDecision
      : settlementStatus === "paper_reconciled"
        ? settlementFraming.paperReconciledDecision
        : settlementStatus === "needs_paper_trade"
          ? settlementFraming.needsPaperDecision
          : settlementFraming.notReconciledDecision;
  const nextAction =
    recommendedActions[0] ??
    (settlementData
      ? settlementFraming.readyNextAction
      : settlementFraming.emptyNextAction);
  const evidence = [
    `${settlementFraming.expectedLabel} ${formatCurrency(settlementSummary.expected_pnl_eur)}.`,
    `${settlementFraming.paperDeltaLabel} ${formatCurrency(paperDelta)}.`,
    `${settlementFraming.realizedDeltaLabel} ${formatCurrency(realizedDelta)}.`,
    `Primary variance driver: ${String(settlementData?.primary_variance_driver ?? "not evaluated").replaceAll("_", " ")}.`,
  ];
  const statusRows = Object.entries(evidenceStatus).map(([evidence, status]) => ({
    evidence: evidence.replaceAll("_", " "),
    status: String(status).replaceAll("_", " "),
    business_use: settlementEvidenceBusinessUse(evidence),
  }));
  const linkRows = Object.entries(links)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([artifact, value]) => ({
      artifact: artifact.replaceAll("_", " "),
      id: value,
      business_use: settlementLinkBusinessUse(artifact),
    }));
  const actionRows = recommendedActions.map((action, index) => ({
    priority: index + 1,
    recommended_action: action,
  }));

  return (
    <div className="space-y-5">
      <DecisionBrief
        action={<StatusPill tone={settlementTone(settlementStatus)}>{settlementStatus.replaceAll("_", " ")}</StatusPill>}
        blockers={missingEvidence}
        decision={decision}
        evidence={evidence}
        eyebrow={settlementFraming.eyebrow}
        nextAction={nextAction}
        title={settlementFraming.title}
        tone={settlementTone(settlementStatus)}
      />

      <SectionCard
        action={<ActionButton endpoint={`/assets/${selectedAssetId}/settlement/reconcile`} label="Reconcile settlement" refetch={refetchExecution} variant="primary" />}
        title={settlementFraming.reconciliationTitle}
      >
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <ExecutionMetric label="Expected PnL" value={formatCurrency(settlementSummary.expected_pnl_eur)} />
          <ExecutionMetric label="Paper PnL" value={formatCurrency(settlementSummary.paper_pnl_eur)} />
          <ExecutionMetric label="Realized PnL" value={formatCurrency(settlementSummary.realized_pnl_eur)} />
        </div>
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <ExecutionMetric
            label="Execution model"
            value={String(settlementData?.market_execution_model ?? "-").replaceAll("_", " ")}
          />
          <ExecutionMetric
            label="Settlement basis"
            value={String(settlementData?.settlement_basis ?? "-").replaceAll("_", " ")}
          />
          <ExecutionMetric
            label="Reserve awarded"
            value={`${formatNumber(settlementSummary.awarded_capacity_mw, 2)} MW`}
          />
        </div>
        <DataTable columns={["driver", "severity", "delta_eur", "message"]} rows={varianceDrivers.slice(0, 8)} />
      </SectionCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)]">
        <SectionCard
          action={<StatusPill tone={missingEvidence.length ? "amber" : "emerald"}>{missingEvidence.length ? "incomplete" : "complete"}</StatusPill>}
          title={settlementFraming.completenessTitle}
        >
          <DataTable columns={["evidence", "status", "business_use"]} rows={statusRows} />
        </SectionCard>

        <SectionCard title={settlementFraming.actionsTitle}>
          <DataTable columns={["priority", "recommended_action"]} rows={actionRows} />
        </SectionCard>
      </div>

      <SectionCard title={settlementFraming.linksTitle}>
        <DataTable columns={["artifact", "id", "business_use"]} rows={linkRows} />
      </SectionCard>
    </div>
  );
}

function buildMissingSettlementEvidence(evidenceStatus: JsonObject) {
  return Object.entries(evidenceStatus)
    .filter(([, status]) => !["available", "ok"].includes(String(status)))
    .map(([evidence, status]) => `${evidence.replaceAll("_", " ")} is ${String(status).replaceAll("_", " ")}.`);
}

function getSettlementPersonaFraming(personaId: PersonaId) {
  const defaultFraming = {
    actionsTitle: "Recommended actions",
    completenessTitle: "Evidence completeness",
    emptyNextAction: "Run settlement reconciliation after bid proposal and paper execution evidence exist.",
    eyebrow: "Settlement evidence",
    expectedLabel: "Expected PnL",
    linksTitle: "Linked audit packet",
    needsPaperDecision: "Run paper trading before settlement can judge execution quality",
    notReconciledDecision: "Settlement evidence has not been reconciled yet",
    paperDeltaLabel: "Paper delta",
    paperReconciledDecision: "Paper economics are reconciled, but realized price evidence is still missing",
    readyNextAction: "Keep settlement evidence attached to the automated trading audit packet.",
    realizedDeltaLabel: "Realized delta",
    reconciliationTitle: "Financial reconciliation",
    settledDecision: "Realized economics are reconciled against the automation packet",
    title: "Can the trading result be defended?",
  };

  const personaFraming: Partial<Record<PersonaId, typeof defaultFraming>> = {
    asset_owner: {
      actionsTitle: "Owner next actions",
      completenessTitle: "Owner proof completeness",
      emptyNextAction: "Run settlement reconciliation before presenting realized value to the owner.",
      eyebrow: "Owner settlement evidence",
      expectedLabel: "Owner expected value",
      linksTitle: "Owner audit links",
      needsPaperDecision: "Run paper execution before owner value can be reconciled",
      notReconciledDecision: "Owner settlement evidence has not been reconciled yet",
      paperDeltaLabel: "Paper value variance",
      paperReconciledDecision: "Paper value is reconciled, but realized price proof is still missing",
      readyNextAction: "Use settlement evidence to explain whether expected value converted into execution value.",
      realizedDeltaLabel: "Realized value variance",
      reconciliationTitle: "Owner value reconciliation",
      settledDecision: "Expected owner value is reconciled against realized trading evidence",
      title: "Did expected value turn into realized or paper value?",
    },
    client_success: {
      actionsTitle: "Client explanation actions",
      completenessTitle: "Client proof completeness",
      emptyNextAction: "Run settlement reconciliation before sending the client performance narrative.",
      eyebrow: "Client settlement explanation",
      expectedLabel: "Reported expectation",
      linksTitle: "Client evidence links",
      needsPaperDecision: "Run paper trading before explaining execution quality to the client",
      notReconciledDecision: "Settlement evidence is not ready for client explanation yet",
      paperDeltaLabel: "Paper explanation variance",
      paperReconciledDecision: "Paper economics are explainable, but realized price evidence is still missing",
      readyNextAction: "Use the variance drivers and recommended actions in the client conversation.",
      realizedDeltaLabel: "Realized explanation variance",
      reconciliationTitle: "Client settlement explanation",
      settledDecision: "Settlement evidence is ready to explain client performance",
      title: "How should settlement variance be explained to the client?",
    },
    investor_lender: {
      actionsTitle: "Diligence actions",
      completenessTitle: "Bankability proof completeness",
      emptyNextAction: "Run settlement reconciliation before using this as investment evidence.",
      eyebrow: "Investment settlement evidence",
      expectedLabel: "Underwritten value",
      linksTitle: "Diligence evidence links",
      needsPaperDecision: "Paper execution is required before investment-quality settlement review",
      notReconciledDecision: "Settlement evidence is not bankable yet",
      paperDeltaLabel: "Paper downside variance",
      paperReconciledDecision: "Paper economics are available, but realized settlement proof is incomplete",
      readyNextAction: "Use settlement variance to support bankability and downside-risk review.",
      realizedDeltaLabel: "Realized downside variance",
      reconciliationTitle: "Bankability reconciliation",
      settledDecision: "Settlement evidence supports investment-quality revenue review",
      title: "Does settlement evidence support bankability?",
    },
    risk_compliance: {
      actionsTitle: "Governance actions",
      completenessTitle: "Governance evidence completeness",
      emptyNextAction: "Run settlement reconciliation before approving the trading packet.",
      eyebrow: "Governance settlement evidence",
      expectedLabel: "Approved expected PnL",
      linksTitle: "Governance audit links",
      needsPaperDecision: "Paper execution is required before variance can be approved",
      notReconciledDecision: "Settlement evidence is missing for governance review",
      paperDeltaLabel: "Paper control variance",
      paperReconciledDecision: "Paper variance is available, but realized evidence is still missing",
      readyNextAction: "Use variance drivers to decide whether the trading packet remains defensible.",
      realizedDeltaLabel: "Realized control variance",
      reconciliationTitle: "Governance reconciliation",
      settledDecision: "Settlement variance can be defended against the approved trading packet",
      title: "Can we defend the settlement variance?",
    },
    revenue_analyst: {
      actionsTitle: "Revenue model actions",
      completenessTitle: "Revenue evidence completeness",
      emptyNextAction: "Run settlement reconciliation before updating revenue assumptions.",
      eyebrow: "Revenue settlement evidence",
      expectedLabel: "Modelled revenue",
      linksTitle: "Revenue evidence links",
      needsPaperDecision: "Paper execution is required before revenue assumptions can be tested",
      notReconciledDecision: "Settlement evidence is not ready to update revenue assumptions",
      paperDeltaLabel: "Paper revenue variance",
      paperReconciledDecision: "Paper revenue is reconciled, but actual-price feedback is still missing",
      readyNextAction: "Use settlement variance to tune revenue stack, route allocation, and hedge assumptions.",
      realizedDeltaLabel: "Realized revenue variance",
      reconciliationTitle: "Revenue assumption reconciliation",
      settledDecision: "Settlement feedback is ready to update revenue assumptions",
      title: "What should change in revenue assumptions?",
    },
    executive: {
      actionsTitle: "Management actions",
      completenessTitle: "Management proof completeness",
      emptyNextAction: "Run settlement reconciliation before presenting realized performance.",
      eyebrow: "Executive settlement evidence",
      expectedLabel: "Management expected value",
      linksTitle: "Management evidence links",
      needsPaperDecision: "Paper execution is required before management performance review",
      notReconciledDecision: "Settlement evidence is not ready for management review",
      paperDeltaLabel: "Paper performance variance",
      paperReconciledDecision: "Paper performance is reconciled, but realized evidence is still incomplete",
      readyNextAction: "Use settlement evidence to explain realized performance and open variance.",
      realizedDeltaLabel: "Realized performance variance",
      reconciliationTitle: "Management performance reconciliation",
      settledDecision: "Settlement evidence is ready for management performance review",
      title: "Can management trust the performance result?",
    },
  };

  return personaFraming[personaId] ?? defaultFraming;
}

function settlementEvidenceBusinessUse(evidence: string) {
  if (evidence === "execution_proposal") {
    return "Links settlement back to the approved automated order package.";
  }

  if (evidence === "paper_trade") {
    return "Shows whether market-specific execution was simulated before reconciliation.";
  }

  if (evidence === "paper_validation") {
    return "Confirms paper execution checks passed before live-mode learning.";
  }

  if (evidence === "forecast_actual") {
    return "Supplies actual-price proof for model and market variance.";
  }

  if (evidence === "realized_dispatch") {
    return "Converts actual prices into realized dispatch economics.";
  }

  return "Supports settlement defensibility.";
}

function settlementLinkBusinessUse(artifact: string) {
  if (artifact === "execution_proposal_id") {
    return "Source bid package used for expected PnL.";
  }

  if (artifact === "paper_trade_id") {
    return "Paper execution run used for market-clearing comparison.";
  }

  if (artifact === "forecast_actual_id") {
    return "Forecast-vs-actual run used for realized-price evidence.";
  }

  return "Linked evidence artifact.";
}

function settlementTone(value: unknown): "amber" | "blue" | "emerald" | "red" | "slate" {
  if (value === "settled") {
    return "emerald";
  }

  if (value === "paper_reconciled") {
    return "amber";
  }

  if (value === "needs_paper_trade") {
    return "red";
  }

  return "slate";
}

export function ExecutionAuditPanel({
  approvalData,
  auditRows,
  automationEvents,
  lifecycleRows,
  personaId,
  personaLayer,
  paperTrade,
  proposal,
  settlementData,
  submissionLifecycle,
  submission,
  riskChecks,
  telemetryData,
}: {
  approvalData?: ExecutionApproval | null;
  auditRows: TableRow[];
  automationEvents: AutomationEvent[];
  lifecycleRows: TableRow[];
  personaId: PersonaId;
  personaLayer: PersonaLayer;
  paperTrade?: ExecutionPaperTrade | null;
  proposal?: ExecutionProposal | null;
  settlementData?: JsonObject | null;
  submissionLifecycle?: MarketSubmissionLifecycleResponse;
  submission?: JsonObject | null;
  riskChecks: TableRow[];
  telemetryData: AssetTelemetryResponse["telemetry"];
}) {
  const auditFraming = getAuditPersonaFraming(personaId);
  const showOperationalDetail = personaLayer === "internal" || personaLayer === "platform";
  const blockedLifecycleSteps = lifecycleRows.filter((row) => row.status === "blocked");
  const failedRiskChecks = riskChecks.filter((row) => !["passed", "complete"].includes(String(row.status)));
  const auditPacketRows = buildAuditPacketRows({
    approvalData,
    automationEvents,
    paperTrade,
    proposal,
    settlementData,
    submission,
    telemetryData,
  });
  const missingPacketRows = auditPacketRows.filter((row) => row.status !== "available" && row.status !== "complete");
  const auditDecisionStatus =
    missingPacketRows.some((row) => row.severity === "high") || blockedLifecycleSteps.length
      ? "not defensible"
      : missingPacketRows.length || failedRiskChecks.length
        ? "review required"
        : "defensible";
  const auditDecision =
    auditDecisionStatus === "defensible"
      ? "The automated trading decision has enough evidence for post-trade review"
      : auditDecisionStatus === "review required"
        ? "The audit packet is usable, but key proof points still need review"
        : "The automated trading decision is not defensible until blocked evidence is cleared";
  const nextAction =
    missingPacketRows[0]?.next_action ??
    blockedLifecycleSteps[0]?.message ??
    failedRiskChecks[0]?.message ??
    "Keep this packet attached to settlement, compliance, and client reporting evidence.";
  const evidence = [
    `${formatNumber(lifecycleRows.length, 0)} lifecycle step(s) captured.`,
    `${formatNumber(riskChecks.length - failedRiskChecks.length, 0)}/${formatNumber(riskChecks.length, 0)} backend risk checks passed.`,
    `${formatNumber(automationEvents.length, 0)} automation event(s) recorded.`,
    `Telemetry ${telemetryData?.availability_status ?? "missing"}.`,
  ];
  const blockers = [
    ...missingPacketRows.map((row) => `${row.evidence}: ${row.next_action}`),
    ...blockedLifecycleSteps.map((row) => `${row.label ?? row.step ?? "Lifecycle step"}: ${row.message ?? "Blocked"}`),
  ].slice(0, 6);

  return (
    <div className="space-y-5">
      <DecisionBrief
        action={<StatusPill tone={auditDecisionTone(auditDecisionStatus)}>{auditDecisionStatus}</StatusPill>}
        blockers={blockers}
        decision={auditDecision}
        evidence={evidence}
        eyebrow={auditFraming.eyebrow}
        nextAction={nextAction}
        title={auditFraming.title}
        tone={auditDecisionTone(auditDecisionStatus)}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <ExecutionMetric label="Lifecycle" value={submissionLifecycle?.lifecycle_status ?? "not evaluated"} />
        <ExecutionMetric label="Blocked steps" value={formatNumber(blockedLifecycleSteps.length, 0)} />
        <ExecutionMetric label="Risk checks passed" value={`${formatNumber(riskChecks.length - failedRiskChecks.length, 0)}/${formatNumber(riskChecks.length, 0)}`} />
        <ExecutionMetric label="Automation events" value={formatNumber(automationEvents.length, 0)} />
        <ExecutionMetric label="Telemetry" value={telemetryData?.availability_status ?? "missing"} />
      </div>

      <SectionCard
        action={<StatusPill tone={missingPacketRows.length ? "amber" : "emerald"}>{missingPacketRows.length ? "incomplete" : "complete"}</StatusPill>}
        title={auditFraming.packetTitle}
      >
        <DataTable columns={["evidence", "status", "severity", "business_use", "next_action"]} rows={auditPacketRows} />
      </SectionCard>

      {showOperationalDetail ? (
        <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard
          action={<StatusPill tone={lifecycleTone(submissionLifecycle?.lifecycle_status)}>{submissionLifecycle?.lifecycle_status ?? "not evaluated"}</StatusPill>}
          title="Submission lifecycle"
        >
          <div className="mb-4 grid gap-3 md:grid-cols-4">
            <ExecutionMetric label="Current step" value={submissionLifecycle?.current_step?.label ?? "-"} />
            <ExecutionMetric label="Adapter" value={submissionLifecycle?.adapter_id ?? "-"} />
            <ExecutionMetric label="Complete" value={formatNumber(submissionLifecycle?.summary?.complete, 0)} />
            <ExecutionMetric label="Blocked" value={formatNumber(submissionLifecycle?.summary?.blocked, 0)} />
          </div>
          <DataTable columns={["step", "label", "status", "owner", "message"]} rows={lifecycleRows.slice(0, 10)} />
        </SectionCard>
        <SectionCard title="Backend risk checks">
          <DataTable columns={["check", "status", "message"]} rows={riskChecks.slice(0, 8)} />
        </SectionCard>

        <SectionCard
          action={<StatusPill tone={automationEvents.length ? "emerald" : "slate"}>{automationEvents.length}</StatusPill>}
          title="Automation event trail"
        >
          <DataTable
            columns={[
              "created_at",
              "event_type",
              "action",
              "status",
              "automation_mode_after",
              "strategy_mode_after",
              "error_type",
            ]}
            rows={automationEvents.slice(0, 8)}
          />
        </SectionCard>

        <SectionCard
          action={<StatusPill tone="blue">Pre-trade audit</StatusPill>}
          title="Execution audit trail"
        >
          <DataTable columns={["event", "actor", "status", "note"]} rows={auditRows.slice(0, 10)} />
        </SectionCard>
        <AssetTelemetryPanel telemetryData={telemetryData} />
        </div>
      ) : (
        <SectionCard
          action={<StatusPill tone={blockers.length ? "amber" : "emerald"}>{blockers.length ? "review" : "clear"}</StatusPill>}
          title={auditFraming.clientSummaryTitle}
        >
          <DataTable
            columns={["proof_point", "status", "client_value", "next_action"]}
            rows={buildClientAuditSummaryRows({
              auditPacketRows,
              automationEvents,
              lifecycleRows,
              riskChecks,
              telemetryData,
            })}
          />
        </SectionCard>
      )}
    </div>
  );
}

function getAuditPersonaFraming(personaId: PersonaId) {
  const defaultFraming = {
    clientSummaryTitle: "Client-facing audit summary",
    eyebrow: "Audit evidence",
    packetTitle: "Audit packet completeness",
    title: "Can the automated decision be defended?",
  };

  const framing: Partial<Record<PersonaId, typeof defaultFraming>> = {
    asset_owner: {
      clientSummaryTitle: "Owner-facing proof summary",
      eyebrow: "Owner audit evidence",
      packetTitle: "Owner evidence packet",
      title: "Can the owner trust the automated decision?",
    },
    investor_lender: {
      clientSummaryTitle: "Bankability proof summary",
      eyebrow: "Investment audit evidence",
      packetTitle: "Bankability audit packet",
      title: "Is the decision defensible for diligence?",
    },
    executive: {
      clientSummaryTitle: "Executive proof summary",
      eyebrow: "Executive audit evidence",
      packetTitle: "Board evidence packet",
      title: "Is the automated decision board-defensible?",
    },
    client_success: {
      clientSummaryTitle: "Client explanation summary",
      eyebrow: "Client audit evidence",
      packetTitle: "Client evidence packet",
      title: "Can client success explain and defend this decision?",
    },
    project_developer: {
      clientSummaryTitle: "Development proof summary",
      eyebrow: "Development audit evidence",
      packetTitle: "Development evidence packet",
      title: "Does the audit trail support development readiness?",
    },
  };

  return framing[personaId] ?? defaultFraming;
}

function buildClientAuditSummaryRows({
  auditPacketRows,
  automationEvents,
  lifecycleRows,
  riskChecks,
  telemetryData,
}: {
  auditPacketRows: TableRow[];
  automationEvents: AutomationEvent[];
  lifecycleRows: TableRow[];
  riskChecks: TableRow[];
  telemetryData: AssetTelemetryResponse["telemetry"];
}) {
  const missingEvidence = auditPacketRows.filter((row) => row.status !== "available" && row.status !== "complete");
  const blockedLifecycleSteps = lifecycleRows.filter((row) => row.status === "blocked");
  const failedRiskChecks = riskChecks.filter((row) => !["passed", "complete"].includes(String(row.status)));

  return [
    {
      client_value: "Shows whether the complete decision packet exists.",
      next_action: missingEvidence[0]?.next_action ?? "Keep the audit packet attached to reports.",
      proof_point: "Evidence packet",
      status: missingEvidence.length ? `${missingEvidence.length} gap(s)` : "complete",
    },
    {
      client_value: "Shows whether the trading workflow reached a defendable state.",
      next_action: blockedLifecycleSteps[0]?.message ?? "Keep lifecycle status available for review.",
      proof_point: "Submission lifecycle",
      status: blockedLifecycleSteps.length ? `${blockedLifecycleSteps.length} blocked` : "no blocked steps",
    },
    {
      client_value: "Confirms risk checks do not contradict the report narrative.",
      next_action: failedRiskChecks[0]?.message ?? "Keep risk checks linked to the audit packet.",
      proof_point: "Risk checks",
      status: failedRiskChecks.length ? `${failedRiskChecks.length} review` : "passed",
    },
    {
      client_value: "Proves the asset could physically support the automated decision.",
      next_action: telemetryData ? "Keep telemetry snapshot for client evidence." : "Capture telemetry before client sign-off.",
      proof_point: "Asset telemetry",
      status: telemetryData?.availability_status ?? "missing",
    },
    {
      client_value: "Shows automation actions were recorded for post-trade review.",
      next_action: automationEvents.length ? "Keep event trail archived." : "Record automation activity before sign-off.",
      proof_point: "Automation events",
      status: automationEvents.length ? `${automationEvents.length} event(s)` : "missing",
    },
  ];
}

function buildAuditPacketRows({
  approvalData,
  automationEvents,
  paperTrade,
  proposal,
  settlementData,
  submission,
  telemetryData,
}: {
  approvalData?: ExecutionApproval | null;
  automationEvents: AutomationEvent[];
  paperTrade?: ExecutionPaperTrade | null;
  proposal?: ExecutionProposal | null;
  settlementData?: JsonObject | null;
  submission?: JsonObject | null;
  telemetryData: AssetTelemetryResponse["telemetry"];
}) {
  return [
    {
      business_use: "Proves the optimizer produced the source order package.",
      evidence: "Signal and proposal",
      next_action: proposal ? "Keep proposal linked to audit evidence." : "Build a pre-trade proposal from the latest signal.",
      severity: proposal ? "low" : "high",
      status: proposal ? "available" : "missing",
    },
    {
      business_use: "Shows market-specific execution was tested before submission.",
      evidence: "Paper execution",
      next_action: paperTrade ? "Use paper result in settlement and go-live review." : "Run paper trading before audit sign-off.",
      severity: paperTrade ? "low" : "high",
      status: paperTrade ? "available" : "missing",
    },
    {
      business_use: "Documents who allowed or blocked the automated package.",
      evidence: "Human gate",
      next_action: approvalData ? "Retain approval decision with the packet." : "Request or record the human approval gate.",
      severity: approvalData?.status === "approved" ? "low" : "medium",
      status: approvalData?.status ?? "missing",
    },
    {
      business_use: "Records what was submitted or simulated against the market adapter.",
      evidence: "Market submission",
      next_action: submission ? "Keep submission ID linked to lifecycle evidence." : "Simulate or submit after proposal and paper gates pass.",
      severity: submission ? "low" : "medium",
      status: submission ? "available" : "missing",
    },
    {
      business_use: "Reconciles expected, paper, and realized economics.",
      evidence: "Settlement evidence",
      next_action: settlementData ? "Use variance feedback in automation learning." : "Run settlement reconciliation after execution evidence exists.",
      severity: settlementData ? "low" : "medium",
      status: settlementData ? "available" : "missing",
    },
    {
      business_use: "Proves the asset could physically follow the automated schedule.",
      evidence: "Asset telemetry",
      next_action: telemetryData ? "Keep telemetry snapshot with the audit packet." : "Capture telemetry before live automation sign-off.",
      severity: telemetryData ? "low" : "high",
      status: telemetryData?.availability_status ?? "missing",
    },
    {
      business_use: "Shows what automation did and in which mode.",
      evidence: "Automation event trail",
      next_action: automationEvents.length ? "Keep event trail for post-trade review." : "Run or record an automation action before audit sign-off.",
      severity: automationEvents.length ? "low" : "medium",
      status: automationEvents.length ? "available" : "missing",
    },
  ];
}

function auditDecisionTone(value: string): "amber" | "blue" | "emerald" | "red" | "slate" {
  if (value === "defensible") {
    return "emerald";
  }

  if (value === "review required") {
    return "amber";
  }

  if (value === "not defensible") {
    return "red";
  }

  return "slate";
}

function WorkflowStep({
  icon,
  label,
  status,
}: {
  icon: React.ReactNode;
  label: string;
  status: "blocked" | "complete" | "disabled" | "pending" | "required";
}) {
  const toneByStatus = {
    blocked: "red",
    complete: "emerald",
    disabled: "amber",
    pending: "slate",
    required: "blue",
  } as const;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <span className="text-sky-300">{icon}</span>
        {label}
      </div>
      <div className="mt-4">
        <StatusPill tone={toneByStatus[status]}>{status}</StatusPill>
      </div>
    </div>
  );
}

function textValue(value: unknown, fallback = "-"): string {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    const rendered = value.map((item) => textValue(item, "")).filter(Boolean).join(", ");
    return rendered || fallback;
  }

  if (typeof value === "object" && "message" in value) {
    return textValue((value as { message?: unknown }).message, fallback);
  }

  if (typeof value === "object" && "required_action" in value) {
    return textValue((value as { required_action?: unknown }).required_action, fallback);
  }

  return fallback;
}

function buildRiskUnblockRows({
  automationBlockers,
  freshnessGates,
  hardBlockers,
  remediationItems,
}: {
  automationBlockers: string[];
  freshnessGates: AutomationFreshnessGate[];
  hardBlockers: string[];
  remediationItems: AutomationRemediationItem[];
}) {
  const rows = [
    ...remediationItems.map((item) => ({
      blocker: item.blocker_id ?? item.message ?? item.required_action ?? "Review automation blocker",
      next_action: item.required_action ?? item.message ?? "Resolve blocker",
      owner: item.auto_resolvable ? "automation" : item.evidence_link ? "operator" : "risk",
      priority: item.severity ?? "review",
      source: item.source ?? item.category ?? "remediation",
    })),
    ...hardBlockers.map((blocker) => ({
      blocker,
      next_action: "Clear before live trading",
      owner: "risk engine",
      priority: "high",
      source: "hard gate",
    })),
    ...automationBlockers.map((blocker) => ({
      blocker,
      next_action: "Resolve automation blocker",
      owner: "automation policy",
      priority: "medium",
      source: "automation",
    })),
    ...freshnessGates
      .filter((gate) => gate.freshness_status !== "fresh")
      .map((gate) => ({
        blocker: gate.label ?? gate.gate_id ?? "Freshness gate",
        next_action: gate.required_action ?? "Refresh evidence before live escalation",
        owner: "data operations",
        priority: gate.freshness_status === "missing" ? "high" : "medium",
        source: "freshness",
      })),
  ];

  const uniqueRows = new Map<string, TableRow>();

  rows.forEach((row) => {
    const key = `${row.source}:${row.blocker}:${row.next_action}`;
    if (!uniqueRows.has(key)) {
      uniqueRows.set(key, row);
    }
  });

  return Array.from(uniqueRows.values());
}

function confidenceTone(value: unknown) {
  if (value === "high") {
    return "emerald";
  }

  if (value === "medium") {
    return "blue";
  }

  if (value === "low") {
    return "amber";
  }

  return "slate";
}

function gateTone(value: unknown) {
  if (value === "approved" || value === "passed" || value === "fresh") {
    return "emerald";
  }

  if (value === "review" || value === "requested" || value === "medium") {
    return "blue";
  }

  if (value === "low" || value === "missing" || value === "unscored") {
    return "amber";
  }

  if (value === "blocked" || value === "rejected") {
    return "red";
  }

  return "slate";
}

function automationTone(value: unknown) {
  if (value === "supervised_live_candidate") {
    return "emerald";
  }

  if (value === "human_approval_required") {
    return "blue";
  }

  if (value === "paper_only") {
    return "amber";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function approvalTone(value: unknown) {
  if (value === "approved") {
    return "emerald";
  }

  if (value === "requested") {
    return "blue";
  }

  if (value === "rejected") {
    return "red";
  }

  return "slate";
}

function readinessTone(value: unknown) {
  if (value === "supervised_ready" || value === "ready") {
    return "emerald";
  }

  if (value === "operator_review_required" || value === "review") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}

function lifecycleTone(value: unknown) {
  if (value === "complete") {
    return "emerald";
  }

  if (value === "in_progress" || value === "review") {
    return "blue";
  }

  if (value === "blocked") {
    return "red";
  }

  return "slate";
}
