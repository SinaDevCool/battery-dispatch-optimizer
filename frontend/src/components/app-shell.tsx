"use client";

import { ShieldCheck, Zap } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { AssetSelector } from "@/components/asset-selector";
import { useAssetContext } from "@/components/asset-provider";
import { DataSourceBadges } from "@/components/data-source-badges";
import { PersonaAiChatWidget } from "@/components/persona-ai-chat-widget";
import { PersonaSelector } from "@/components/persona-selector";
import { usePersona } from "@/components/persona-provider";
import { cn } from "@/lib/utils";
import { StatusPill } from "@/components/status-pill";
import { useApiBaseUrl } from "@/hooks/use-api-base-url";
import { demoStatusTone, formatDemoStatus } from "@/lib/demo-status";
import {
  flattenNavigationGroups,
  isNavigationActive,
  navigationGroups,
} from "@/lib/navigation";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [searchString, setSearchString] = useState("");
  const apiBaseUrl = useApiBaseUrl();
  const { persona } = usePersona();
  const { aiEvidenceMode, selectedAsset, setAiEvidenceMode } = useAssetContext();
  const isClientPersona = persona.layer === "client";
  const selectedDataMode = selectedAsset?.data_mode ?? "mock";
  const isProductionAsset = selectedDataMode === "production";
  const visibleHrefSet = new Set<string>();
  const visibleNavigationGroups = navigationGroups
    .filter((group) =>
      persona.id === "all" || persona.primaryNavigationGroups.includes(group.id),
    )
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) => {
          const isAllowed =
            persona.id === "all" ||
            persona.allowedNavigationHrefs.includes(item.href);

          if (!isAllowed || visibleHrefSet.has(item.href)) {
            return false;
          }

          visibleHrefSet.add(item.href);
          return true;
        },
      ),
    }))
    .filter((group) => group.items.length > 0);
  const visibleNavigation = flattenNavigationGroups(visibleNavigationGroups);

  useEffect(() => {
    const syncSearchString = () => {
      setSearchString(window.location.search.replace(/^\?/, ""));
    };

    syncSearchString();
    window.addEventListener("popstate", syncSearchString);
    window.addEventListener("locationchange", syncSearchString);

    return () => {
      window.removeEventListener("popstate", syncSearchString);
      window.removeEventListener("locationchange", syncSearchString);
    };
  }, [pathname]);

  return (
    <div className="min-h-screen bg-[#080b10] text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 flex-col overflow-hidden border-r border-slate-800 bg-slate-950/95 px-4 py-5 xl:flex">
        <div className="mb-6 flex shrink-0 items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-emerald-400/30 bg-emerald-400/10">
            <Zap className="h-5 w-5 text-emerald-300" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">
              Battery Trader AI
            </div>
            <div className="text-xs text-slate-500">
              {persona.header}
            </div>
          </div>
        </div>

        <div className="mb-5 shrink-0 border-l border-emerald-400/30 px-3 py-1">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-300">
            {getPersonaLayerLabel(persona.layer)}
          </div>
          <div className="mt-1 text-xs font-semibold text-slate-200">
            {persona.label}
          </div>
          <Link
            className="mt-2 inline-flex text-xs font-semibold text-emerald-200 transition hover:text-emerald-100"
            href={persona.defaultNavigationHref}
          >
            Start: {persona.defaultNavigationLabel}
          </Link>
        </div>

        <nav className="sidebar-nav-scroll -mr-2 min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain pr-2 pb-5">
          {visibleNavigationGroups.map((group) => (
            <div key={group.id}>
              <div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => {
                  const isActive = isNavigationActive(pathname, item, searchString);
                  const Icon = item.icon;

                  return (
                    <div key={`${group.id}-${item.href}-${item.label}`}>
                      <Link
                        className={cn(
                          "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-slate-400 transition hover:bg-slate-900 hover:text-slate-100",
                          isActive &&
                            "border border-sky-400/25 bg-sky-400/10 text-sky-100",
                        )}
                        href={item.href}
                        onClick={() => setSearchString(getNavigationSearchString(item.href))}
                      >
                        <Icon className="h-4 w-4" />
                        {item.label}
                      </Link>
                      {item.children?.length && isActive ? (
                        <div className="mt-1 space-y-1 border-l border-slate-800 pl-3 ml-5">
                          {item.children.map((child) => {
                            const ChildIcon = child.icon;
                            const isChildActive = isNavigationActive(pathname, child, searchString);

                            return (
                              <Link
                                className={cn(
                                  "flex items-center gap-2 rounded-md px-2.5 py-2 text-xs font-medium text-slate-500 transition hover:bg-slate-900 hover:text-slate-100",
                                  isChildActive && "bg-emerald-400/10 text-emerald-100",
                                )}
                                href={child.href}
                                onClick={() => setSearchString(getNavigationSearchString(child.href))}
                                key={`${group.id}-${child.href}-${child.label}`}
                              >
                                <ChildIcon className="h-3.5 w-3.5" />
                                {child.label}
                              </Link>
                            );
                          })}
                        </div>
                      ) : null}
                    </div>
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
              <div className="mt-1 text-xl font-semibold text-white">
                Forecast, optimize, and execute
              </div>
            </div>

            <div className="hidden items-center gap-3 md:flex">
              {!isClientPersona ? (
                <StatusPill tone="emerald">API target: {apiBaseUrl}</StatusPill>
              ) : null}
              <div className="flex overflow-hidden rounded-md border border-slate-700 bg-slate-950 p-0.5">
                {(["mock", "live"] as const).map((mode) => (
                  <button
                    className={cn(
                      "px-3 py-1.5 text-xs font-semibold transition",
                      aiEvidenceMode === mode
                        ? mode === "mock"
                          ? "rounded bg-emerald-400 text-slate-950"
                          : "rounded bg-sky-400 text-slate-950"
                        : "text-slate-400 hover:text-slate-100",
                    )}
                    key={mode}
                    onClick={() => setAiEvidenceMode(mode)}
                    type="button"
                  >
                    {mode === "mock" ? "Mock data" : "Live data"}
                  </button>
                ))}
              </div>
              <PersonaSelector />
              <AssetSelector />
            </div>
          </div>

          <div className="border-t border-slate-900 bg-slate-950/80 px-5 py-2.5 lg:px-8">
            <div className="mx-auto flex max-w-[1500px] flex-col gap-2 text-xs text-slate-400">
              <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
                <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-sky-300" />
                <span className="font-semibold text-slate-200">
                  {isProductionAsset ? "Production asset selected" : "Investor demo mode"}
                </span>
                <span className="hidden text-slate-500 sm:inline">/</span>
                <span className="leading-5">
                  {aiEvidenceMode === "mock"
                    ? "AI agents answer from complete simulated evidence. Switch to Live Data for production proof checks."
                    : isProductionAsset
                      ? "AI agents check live-data claims against connector, telemetry, settlement, and approval evidence."
                      : "AI agents are checking production gaps for this mock asset as if it were moving toward live use."}
                </span>
              </div>
              <StatusPill tone={demoStatusTone(selectedDataMode)}>
                AI: {aiEvidenceMode === "mock" ? "Mock data" : "Live data"} / asset: {formatDemoStatus(selectedDataMode)}
              </StatusPill>
              </div>
              <DataSourceBadges
                assetId={selectedAsset?.asset_id ?? "default_site"}
                dataMode={aiEvidenceMode}
              />
            </div>
          </div>

          <nav className="flex gap-1 overflow-x-auto border-t border-slate-900 px-4 py-2 xl:hidden">
            <PersonaSelector />
            {visibleNavigation.map((item, index) => (
              <Link
                className={cn(
                  "whitespace-nowrap rounded-md px-3 py-2 text-xs font-semibold text-slate-400",
                  isNavigationActive(pathname, item, searchString) && "bg-sky-400/10 text-sky-100",
                )}
                href={item.href}
                onClick={() => setSearchString(getNavigationSearchString(item.href))}
                key={`${index}-${item.href}-${item.label}`}
              >
                {item.shortLabel ?? item.label}
              </Link>
            ))}
          </nav>
        </header>

        <main
          className="mx-auto w-full max-w-[1500px] px-5 py-8 lg:px-8"
          key={`${selectedAsset?.asset_id ?? "default_site"}-${aiEvidenceMode}`}
        >
          {children}
        </main>
      </div>
      <PersonaAiChatWidget key={`${persona.id}-${selectedAsset?.asset_id ?? "default_site"}-${aiEvidenceMode}`} />
    </div>
  );
}

function getNavigationSearchString(href: string) {
  return href.split("#")[0]?.split("?")[1] ?? "";
}

function getPersonaLayerLabel(layer: string) {
  if (layer === "client") {
    return "Client Evidence Portal";
  }

  if (layer === "internal") {
    return "Internal Trading OS";
  }

  return "Full platform";
}
