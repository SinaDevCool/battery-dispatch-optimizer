"use client";

import { cn } from "@/lib/utils";

export type WorkspaceTab<T extends string = string> = {
  helper?: string;
  id: T;
  label: string;
};

export function WorkspaceTabs<T extends string>({
  activeTab,
  onTabChange,
  tabs,
}: {
  activeTab: T;
  onTabChange: (tab: T) => void;
  tabs: readonly WorkspaceTab<T>[];
}) {
  const active = tabs.find((tab) => tab.id === activeTab);

  return (
    <div className="mb-5 rounded-lg border border-slate-800 bg-slate-950/70 p-2">
      <div className="flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            aria-current={activeTab === tab.id ? "page" : undefined}
            className={cn(
              "min-w-fit rounded-md px-4 py-2.5 text-left text-sm font-semibold text-slate-400 transition hover:bg-slate-900 hover:text-slate-100",
              activeTab === tab.id && "bg-sky-400/10 text-sky-100",
            )}
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>
      {active?.helper ? (
        <div className="px-2 pb-1 pt-2 text-sm text-slate-500">
          {active.helper}
        </div>
      ) : null}
    </div>
  );
}
