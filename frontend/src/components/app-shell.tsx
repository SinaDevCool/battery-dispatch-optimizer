"use client";

import {
  BatteryCharging,
  BrainCircuit,
  Cable,
  ClipboardCheck,
  Gauge,
  Layers3,
  LineChart,
  ReceiptText,
  Scale,
  ShieldCheck,
  SlidersHorizontal,
  Zap,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { AssetSelector } from "@/components/asset-selector";
import { cn } from "@/lib/utils";
import { StatusPill } from "@/components/status-pill";
import { useApiBaseUrl } from "@/hooks/use-api-base-url";

type NavigationItem = {
  href: string;
  icon: LucideIcon;
  label: string;
};

type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

const navigationGroups: NavigationGroup[] = [
  {
    label: "Command Center",
    items: [
      { href: "/", icon: Gauge, label: "Control Room" },
      { href: "/intelligence", icon: BrainCircuit, label: "Decision Intelligence" },
      { href: "/assets", icon: BatteryCharging, label: "Asset Registry" },
    ],
  },
  {
    label: "AI Forecast Engine",
    items: [
      { href: "/forecasts", icon: LineChart, label: "Forecast Trading Desk" },
    ],
  },
  {
    label: "Multi-Market Optimization",
    items: [
      { href: "/dispatch", icon: Cable, label: "Dispatch Optimizer" },
      { href: "/revenue", icon: Layers3, label: "Revenue Stack" },
      { href: "/regulation", icon: Scale, label: "Regulation & Eligibility" },
      { href: "/hedging", icon: ShieldCheck, label: "Hedged Revenue" },
    ],
  },
  {
    label: "Automated Execution",
    items: [
      { href: "/execution", icon: ClipboardCheck, label: "Execution Control" },
    ],
  },
  {
    label: "Platform",
    items: [
      { href: "/reports", icon: ReceiptText, label: "Reports" },
      { href: "/settings", icon: SlidersHorizontal, label: "Settings" },
    ],
  },
];

const navigation = navigationGroups.flatMap((group) => group.items);

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const apiBaseUrl = useApiBaseUrl();

  return (
    <div className="min-h-screen bg-[#080b10] text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-slate-800 bg-slate-950/95 px-4 py-5 xl:block">
        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-emerald-400/30 bg-emerald-400/10">
            <Zap className="h-5 w-5 text-emerald-300" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">
              Battery Trader AI
            </div>
            <div className="text-xs text-slate-500">
              Autonomous trading OS
            </div>
          </div>
        </div>

        <nav className="space-y-5">
          {navigationGroups.map((group) => (
            <div key={group.label}>
              <div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => {
                  const isActive =
                    item.href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(item.href);
                  const Icon = item.icon;

                  return (
                    <Link
                      className={cn(
                        "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-slate-400 transition hover:bg-slate-900 hover:text-slate-100",
                        isActive &&
                          "border border-sky-400/25 bg-sky-400/10 text-sky-100",
                      )}
                      href={item.href}
                      key={item.href}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      <div className="xl:pl-72">
        <header className="sticky top-0 z-20 border-b border-slate-800 bg-[#080b10]/90 backdrop-blur">
          <div className="mx-auto flex max-w-[1500px] items-center justify-between gap-4 px-5 py-4 lg:px-8">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Battery Trading Intelligence
              </div>
              <h1 className="mt-1 text-xl font-semibold text-white">
                Forecast, optimize, and execute
              </h1>
            </div>

            <div className="hidden items-center gap-3 md:flex">
              <StatusPill tone="emerald">API target: {apiBaseUrl}</StatusPill>
              <AssetSelector />
            </div>
          </div>

          <nav className="flex gap-1 overflow-x-auto border-t border-slate-900 px-4 py-2 xl:hidden">
            {navigation.map((item) => (
              <Link
                className={cn(
                  "whitespace-nowrap rounded-md px-3 py-2 text-xs font-semibold text-slate-400",
                  pathname === item.href && "bg-sky-400/10 text-sky-100",
                )}
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>

        <main className="mx-auto w-full max-w-[1500px] px-5 py-8 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
