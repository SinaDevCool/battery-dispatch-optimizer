import {
  BatteryCharging,
  BrainCircuit,
  Cable,
  ClipboardCheck,
  FileCheck2,
  GitBranch,
  Gauge,
  Layers3,
  LineChart,
  ReceiptText,
  Scale,
  ShieldCheck,
  SlidersHorizontal,
  SquareActivity,
  Zap,
  type LucideIcon,
} from "lucide-react";

export const NAVIGATION_GROUP_IDS = [
  "portfolio",
  "market_intelligence",
  "optimization",
  "automated_trading",
  "risk_compliance",
] as const;

export type NavigationGroupId = (typeof NAVIGATION_GROUP_IDS)[number];

export type NavigationItem = {
  children?: NavigationItem[];
  href: string;
  icon: LucideIcon;
  label: string;
  shortLabel?: string;
};

export type NavigationGroup = {
  id: NavigationGroupId;
  label: string;
  items: NavigationItem[];
};

export const navigationGroups: NavigationGroup[] = [
  {
    id: "portfolio",
    label: "Portfolio",
    items: [
      { href: "/", icon: Gauge, label: "Control Room" },
      { href: "/investor-demo", icon: FileCheck2, label: "Investor Demo" },
      { href: "/assets", icon: BatteryCharging, label: "Asset Registry" },
      { href: "/intelligence", icon: BrainCircuit, label: "Decision Evidence" },
      { href: "/revenue", icon: Layers3, label: "Revenue Assurance" },
      { href: "/reports", icon: ReceiptText, label: "Reports" },
    ],
  },
  {
    id: "market_intelligence",
    label: "Market Intelligence",
    items: [
      { href: "/forecasts", icon: LineChart, label: "Forecast Trust" },
      { href: "/market-prices", icon: Gauge, label: "Market Prices" },
      { href: "/market-signals", icon: Zap, label: "Market Signals" },
      { href: "/market-rules", icon: Scale, label: "Market Rules" },
    ],
  },
  {
    id: "optimization",
    label: "Optimization",
    items: [
      { href: "/dispatch", icon: Cable, label: "Dispatch Schedule" },
      { href: "/scenarios", icon: SquareActivity, label: "Scenario Lab" },
      { href: "/hedging", icon: ShieldCheck, label: "Hedging" },
    ],
  },
  {
    id: "automated_trading",
    label: "Automated Trading",
    items: [
      { href: "/execution/automation-policies", icon: SlidersHorizontal, label: "Automation Control" },
      { href: "/execution/orchestrator", icon: GitBranch, label: "Trading Orchestrator" },
      { href: "/execution", icon: ClipboardCheck, label: "Mission Control" },
    ],
  },
  {
    id: "risk_compliance",
    label: "Risk & Compliance",
    items: [
      { href: "/execution/risk-approval", icon: ShieldCheck, label: "Automation Gates" },
      { href: "/regulation", icon: Scale, label: "Regulatory Compliance" },
      { href: "/execution/settlement", icon: ReceiptText, label: "Settlement Evidence" },
      { href: "/execution/audit", icon: FileCheck2, label: "Audit Evidence" },
      { href: "/settings", icon: SlidersHorizontal, label: "Settings" },
    ],
  },
];

export function isNavigationActive(
  pathname: string,
  item: NavigationItem,
  searchParams = "",
) {
  const [itemPath = item.href, itemQuery = ""] = item.href.split("#")[0]?.split("?") ?? [item.href, ""];

  if (itemQuery) {
    return pathname === itemPath && searchParams === itemQuery;
  }

  if (pathname === itemPath && item.href === itemPath) {
    return searchParams === "";
  }

  return Boolean(
    item.children?.some((child) => {
      const childPath = child.href.split("#")[0]?.split("?")[0] ?? child.href;

      return childPath === pathname;
    }),
  );
}

export function flattenNavigationGroups(groups: NavigationGroup[]) {
  return groups.flatMap((group) =>
    group.items.flatMap((item) => [item, ...(item.children ?? [])]),
  );
}
