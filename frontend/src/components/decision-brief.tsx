import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";

export type DecisionBriefTone = "amber" | "blue" | "emerald" | "red" | "slate";

export function DecisionBrief({
  action,
  blockers = [],
  className,
  decision,
  evidence = [],
  eyebrow,
  nextAction,
  tone = "blue",
  title,
}: {
  action?: React.ReactNode;
  blockers?: string[];
  className?: string;
  decision: React.ReactNode;
  evidence?: string[];
  eyebrow: string;
  nextAction?: React.ReactNode;
  title: string;
  tone?: DecisionBriefTone;
}) {
  return (
    <SectionCard
      action={action ?? <StatusPill tone={tone}>{eyebrow}</StatusPill>}
      className={className}
      title={title}
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Decision
          </div>
          <div className="mt-3 text-lg font-semibold leading-snug text-white">
            {decision}
          </div>
          {nextAction ? (
            <div className="mt-4 rounded-md border border-sky-400/20 bg-sky-400/10 p-3 text-sm leading-5 text-sky-100">
              {nextAction}
            </div>
          ) : null}
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <BriefList
            emptyText="No supporting evidence is available yet."
            items={evidence}
            title="Why"
            tone="emerald"
          />
          <BriefList
            emptyText="No blockers are currently shown."
            items={blockers}
            title="Blockers"
            tone={blockers.length ? "amber" : "emerald"}
          />
        </div>
      </div>
    </SectionCard>
  );
}

function BriefList({
  emptyText,
  items,
  title,
  tone,
}: {
  emptyText: string;
  items: string[];
  title: string;
  tone: DecisionBriefTone;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-slate-100">{title}</div>
        <StatusPill tone={tone}>{items.length}</StatusPill>
      </div>
      <div className="space-y-2">
        {items.length ? (
          items.slice(0, 4).map((item) => (
            <div className="text-xs leading-5 text-slate-400" key={item}>
              {item}
            </div>
          ))
        ) : (
          <div className="text-xs leading-5 text-slate-500">{emptyText}</div>
        )}
      </div>
    </div>
  );
}
