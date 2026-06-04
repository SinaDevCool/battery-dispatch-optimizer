export const PERSONA_IDS = [
  "all",
  "asset_owner",
  "trader",
  "optimizer",
  "risk_compliance",
  "executive",
] as const;

export type PersonaId = (typeof PERSONA_IDS)[number];

export type PersonaProfile = {
  id: PersonaId;
  label: string;
  header: string;
  focus: string;
  defaultControlRoomTab: "trading" | "readiness" | "commercial" | "execution" | "actions";
  primaryNavigationGroups: string[];
  priorityActions: string[];
};

export const personaProfiles: Record<PersonaId, PersonaProfile> = {
  all: {
    id: "all",
    label: "All teams",
    header: "Enterprise platform",
    focus: "Full portfolio, market, optimization, trading, and governance workspace.",
    defaultControlRoomTab: "trading",
    primaryNavigationGroups: [
      "Portfolio Command",
      "Market Intelligence",
      "Optimization & Markets",
      "Trading Operations",
      "Governance",
    ],
    priorityActions: [
      "Monitor portfolio control room.",
      "Review market signal and execution readiness.",
      "Keep audit evidence current.",
    ],
  },
  asset_owner: {
    id: "asset_owner",
    label: "Asset owner",
    header: "Owner value view",
    focus: "Portfolio value, bankability, risk, revenue, and investment decision evidence.",
    defaultControlRoomTab: "commercial",
    primaryNavigationGroups: [
      "Portfolio Command",
      "Optimization & Markets",
      "Governance",
    ],
    priorityActions: [
      "Review expected PnL and revenue stack.",
      "Check enterprise maturity and data completeness.",
      "Confirm commercial decision evidence before investment or operation changes.",
    ],
  },
  trader: {
    id: "trader",
    label: "Trader",
    header: "Trading desk view",
    focus: "Signals, market routes, automation policy, connectors, bids, and supervised execution.",
    defaultControlRoomTab: "execution",
    primaryNavigationGroups: [
      "Market Intelligence",
      "Trading Operations",
    ],
    priorityActions: [
      "Check market signal and orchestrator next action.",
      "Clear connector, policy, and allocation blockers.",
      "Run paper validation before approval or supervised submission.",
    ],
  },
  optimizer: {
    id: "optimizer",
    label: "Optimizer",
    header: "Commercial optimizer view",
    focus: "Dispatch strategy, revenue stacking, market eligibility, hedging, and forecast quality.",
    defaultControlRoomTab: "commercial",
    primaryNavigationGroups: [
      "Market Intelligence",
      "Optimization & Markets",
      "Portfolio Command",
    ],
    priorityActions: [
      "Validate forecast and price evidence.",
      "Review dispatch optimizer and revenue stack assumptions.",
      "Compare eligible markets and hedge alternatives.",
    ],
  },
  risk_compliance: {
    id: "risk_compliance",
    label: "Risk & compliance",
    header: "Governance view",
    focus: "Policies, approvals, settlement, audit, regulation, reports, and operational controls.",
    defaultControlRoomTab: "readiness",
    primaryNavigationGroups: [
      "Trading Operations",
      "Governance",
      "Optimization & Markets",
    ],
    priorityActions: [
      "Review automation policies and approval state.",
      "Check settlement, audit trail, and regulatory eligibility.",
      "Keep reports and assumptions ready for management or audit.",
    ],
  },
  executive: {
    id: "executive",
    label: "Executive",
    header: "Executive view",
    focus: "Portfolio performance, strategic readiness, commercial value, and major blockers.",
    defaultControlRoomTab: "trading",
    primaryNavigationGroups: [
      "Portfolio Command",
      "Governance",
      "Optimization & Markets",
    ],
    priorityActions: [
      "Review portfolio signal, expected PnL, and readiness blockers.",
      "Check strategic maturity and revenue stack direction.",
      "Use reports for board or customer-facing evidence.",
    ],
  },
};

export function isPersonaId(value: string): value is PersonaId {
  return PERSONA_IDS.includes(value as PersonaId);
}
