"use client";

import {
  BarChart3,
  BatteryCharging,
  Cable,
  Gauge,
  LineChart,
  ReceiptText,
  Scale,
  ShieldCheck,
  SlidersHorizontal,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { API_BASE_URL } from "@/lib/api";
import { AssetSelector } from "@/components/asset-selector";
import { cn } from "@/lib/utils";
import { StatusPill } from "@/components/status-pill";

const navigation = [
  { href: "/", icon: Gauge, label: "Overview" },
  { href: "/assets", icon: BatteryCharging, label: "Assets" },
  { href: "/forecasts", icon: LineChart, label: "Forecasts" },
  { href: "/dispatch", icon: Cable, label: "Dispatch" },
  { href: "/revenue", icon: BarChart3, label: "Revenue Stack" },
  { href: "/regulation", icon: Scale, label: "Regulation" },
  { href: "/hedging", icon: ShieldCheck, label: "Hedging" },
  { href: "/reports", icon: ReceiptText, label: "Reports" },
  { href: "/settings", icon: SlidersHorizontal, label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#080b10] text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-slate-800 bg-slate-950/95 px-4 py-5 xl:block">
        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-emerald-400/30 bg-emerald-400/10">
            <Zap className="h-5 w-5 text-emerald-300" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">
              Battery Optimizer
            </div>
            <div className="text-xs text-slate-500">Enterprise control room</div>
          </div>
        </div>

        <nav className="space-y-1">
          {navigation.map((item) => {
            const isActive =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
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
        </nav>
      </aside>

      <div className="xl:pl-72">
        <header className="sticky top-0 z-20 border-b border-slate-800 bg-[#080b10]/90 backdrop-blur">
          <div className="mx-auto flex max-w-[1500px] items-center justify-between gap-4 px-5 py-4 lg:px-8">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Battery Dispatch Optimizer
              </div>
              <h1 className="mt-1 text-xl font-semibold text-white">
                Quantitative asset operations
              </h1>
            </div>

            <div className="hidden items-center gap-3 md:flex">
              <StatusPill tone="emerald">API target: {API_BASE_URL}</StatusPill>
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
