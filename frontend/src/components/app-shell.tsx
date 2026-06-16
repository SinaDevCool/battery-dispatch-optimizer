"use client";

import { Zap } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { AssetSelector } from "@/components/asset-selector";
import { PersonaSelector } from "@/components/persona-selector";
import { usePersona } from "@/components/persona-provider";
import { cn } from "@/lib/utils";
import { StatusPill } from "@/components/status-pill";
import { useApiBaseUrl } from "@/hooks/use-api-base-url";
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
  const isClientPersona = persona.layer === "client";
  const visibleNavigationGroups = navigationGroups
    .filter((group) =>
      persona.id === "all" || persona.primaryNavigationGroups.includes(group.id),
    )
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) =>
          persona.id === "all" ||
          persona.allowedNavigationHrefs.includes(item.href),
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
              <h1 className="mt-1 text-xl font-semibold text-white">
                Forecast, optimize, and execute
              </h1>
            </div>

            <div className="hidden items-center gap-3 md:flex">
              {!isClientPersona ? (
                <StatusPill tone="emerald">API target: {apiBaseUrl}</StatusPill>
              ) : null}
              <PersonaSelector />
              <AssetSelector />
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

        <main className="mx-auto w-full max-w-[1500px] px-5 py-8 lg:px-8">
          {children}
        </main>
      </div>
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
