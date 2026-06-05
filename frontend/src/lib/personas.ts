import type { NavigationGroupId } from "@/lib/navigation";

export const PERSONA_IDS = [
  "all",
  "asset_owner",
  "trader",
  "automation_manager",
  "optimizer",
  "risk_compliance",
  "executive",
] as const;

export type PersonaId = (typeof PERSONA_IDS)[number];

export const DEFAULT_PERSONA_ID: PersonaId = "all";

export const VISIBLE_PERSONA_IDS = [
  "all",
  "asset_owner",
  "trader",
  "automation_manager",
  "risk_compliance",
  "executive",
] as const satisfies readonly PersonaId[];

export type PersonaProfile = {
  allowedAutomationActions: string[];
  defaultNavigationHref: string;
  defaultNavigationLabel: string;
  id: PersonaId;
  label: string;
  header: string;
  focus: string;
  defaultControlRoomTab: "trading" | "readiness" | "commercial" | "execution" | "actions";
  primaryNavigationGroups: NavigationGroupId[];
  priorityActions: string[];
  priorityKpis: string[];
};

export const personaProfiles: Record<PersonaId, PersonaProfile> = {
  all: {
    id: "all",
    label: "Full platform",
    header: "Enterprise platform",
    focus: "Full portfolio, market, optimization, automated trading, and governance workspace.",
    defaultNavigationHref: "/",
    defaultNavigationLabel: "Control Room",
    defaultControlRoomTab: "trading",
    primaryNavigationGroups: [
      "portfolio",
      "market_intelligence",
      "optimization",
      "automated_trading",
      "risk_compliance",
    ],
    priorityActions: [
      "Monitor portfolio control room.",
      "Review market signal and automation readiness.",
      "Keep audit evidence current.",
    ],
    priorityKpis: ["automation_mode", "expected_pnl", "readiness_score"],
    allowedAutomationActions: ["build_proposal", "run_paper_trade", "request_human_gate"],
  },
  asset_owner: {
    id: "asset_owner",
    label: "Asset owner",
    header: "Owner value view",
    focus: "Revenue, bankability, downside protection, and proof that automation creates owner value.",
    defaultNavigationHref: "/revenue",
    defaultNavigationLabel: "Revenue Assurance",
    defaultControlRoomTab: "commercial",
    primaryNavigationGroups: [
      "portfolio",
      "optimization",
      "risk_compliance",
    ],
    priorityActions: [
      "Review expected PnL and revenue stack.",
      "Check production readiness and data completeness.",
      "Confirm automation blockers before investment or operation changes.",
    ],
    priorityKpis: ["modelled_revenue", "downside_risk", "production_readiness"],
    allowedAutomationActions: ["view_status", "approve_gate"],
  },
  trader: {
    id: "trader",
    label: "Trading desk",
    header: "Trading desk view",
    focus: "Signals, market routes, automation control, connectors, bids, and supervised/live execution.",
    defaultNavigationHref: "/execution/automation-policies",
    defaultNavigationLabel: "Automation Control",
    defaultControlRoomTab: "execution",
    primaryNavigationGroups: [
      "automated_trading",
      "market_intelligence",
      "risk_compliance",
    ],
    priorityActions: [
      "Check automation mode and orchestrator next action.",
      "Clear connector, policy, and allocation blockers.",
      "Run paper validation before supervised or live submission.",
    ],
    priorityKpis: ["automation_mode", "primary_market", "next_auto_action"],
    allowedAutomationActions: ["build_proposal", "run_paper_trade", "request_human_gate", "simulate_submission"],
  },
  automation_manager: {
    id: "automation_manager",
    label: "Automation control",
    header: "Autonomous trading view",
    focus: "Automation mode, gates, limits, market connectivity, paper validation, and live-readiness escalation.",
    defaultNavigationHref: "/execution/automation-policies",
    defaultNavigationLabel: "Automation Control",
    defaultControlRoomTab: "execution",
    primaryNavigationGroups: [
      "automated_trading",
      "risk_compliance",
      "market_intelligence",
    ],
    priorityActions: [
      "Keep the automation control plane unblocked.",
      "Escalate from paper trading to supervised automation only with evidence.",
      "Track connector and telemetry gates before limited live mode.",
    ],
    priorityKpis: ["live_trading_allowed", "human_gate", "blocker_count"],
    allowedAutomationActions: ["build_proposal", "run_paper_trade", "simulate_submission", "enable_supervised_auto"],
  },
  optimizer: {
    id: "optimizer",
    label: "Dispatch analyst",
    header: "Dispatch analyst view",
    focus: "Strategy, dispatch quality, revenue stacking, market eligibility, hedging, and forecast performance.",
    defaultNavigationHref: "/dispatch",
    defaultNavigationLabel: "Trading Schedule",
    defaultControlRoomTab: "commercial",
    primaryNavigationGroups: [
      "optimization",
      "market_intelligence",
      "portfolio",
    ],
    priorityActions: [
      "Validate forecast and price evidence.",
      "Review dispatch optimizer and revenue stack assumptions.",
      "Compare eligible markets and hedge alternatives.",
    ],
    priorityKpis: ["forecast_error", "profit_per_mw_day", "revenue_stack"],
    allowedAutomationActions: ["view_status", "run_scenarios"],
  },
  risk_compliance: {
    id: "risk_compliance",
    label: "Risk & compliance",
    header: "Governance view",
    focus: "Automation gates, approval policy, settlement, audit, regulation, reports, and operating limits.",
    defaultNavigationHref: "/execution/risk-approval",
    defaultNavigationLabel: "Automation Gates",
    defaultControlRoomTab: "readiness",
    primaryNavigationGroups: [
      "risk_compliance",
      "automated_trading",
      "optimization",
    ],
    priorityActions: [
      "Review automation gates and approval state.",
      "Check settlement, audit trail, and regulatory eligibility.",
      "Keep reports and assumptions ready for management or audit.",
    ],
    priorityKpis: ["blocked_gates", "approval_status", "settlement_variance"],
    allowedAutomationActions: ["view_status", "approve_gate", "block_gate"],
  },
  executive: {
    id: "executive",
    label: "Executive",
    header: "Executive view",
    focus: "Portfolio performance, strategic readiness, automation maturity, commercial value, and major blockers.",
    defaultNavigationHref: "/",
    defaultNavigationLabel: "Control Room",
    defaultControlRoomTab: "trading",
    primaryNavigationGroups: [
      "portfolio",
      "risk_compliance",
      "optimization",
    ],
    priorityActions: [
      "Review portfolio signal, expected PnL, and automation blockers.",
      "Check automation maturity and revenue stack direction.",
      "Use reports for board or customer-facing evidence.",
    ],
    priorityKpis: ["portfolio_pnl", "automation_maturity", "top_blocker"],
    allowedAutomationActions: ["view_status"],
  },
};

export function isPersonaId(value: string): value is PersonaId {
  return PERSONA_IDS.includes(value as PersonaId);
}
