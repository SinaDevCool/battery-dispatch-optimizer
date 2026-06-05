import { cn } from "@/lib/utils";

const accentClassNames = {
  amber: "border-amber-400/25 bg-amber-400/5",
  blue: "border-sky-400/25 bg-sky-400/5",
  emerald: "border-emerald-400/25 bg-emerald-400/5",
  red: "border-red-400/25 bg-red-400/5",
  slate: "border-slate-700 bg-slate-900/75",
};

export function KpiCard({
  accent = "slate",
  label,
  value,
  helper,
}: {
  accent?: keyof typeof accentClassNames;
  label: string;
  value: React.ReactNode;
  helper?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "min-h-28 rounded-lg border p-4 shadow-sm shadow-black/20",
        accentClassNames[accent],
      )}
    >
      <div className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-slate-400">
        {label}
      </div>
      <div className="mt-3 break-words text-2xl font-semibold leading-tight text-slate-50">
        {value}
      </div>
      {helper ? (
        <div className="mt-2 text-sm leading-5 text-slate-400">{helper}</div>
      ) : null}
    </div>
  );
}
