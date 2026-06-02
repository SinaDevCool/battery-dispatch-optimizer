import { cn } from "@/lib/utils";

const toneClassNames = {
  amber: "border-amber-400/35 bg-amber-400/10 text-amber-200",
  blue: "border-sky-400/35 bg-sky-400/10 text-sky-200",
  emerald: "border-emerald-400/35 bg-emerald-400/10 text-emerald-200",
  red: "border-red-400/35 bg-red-400/10 text-red-200",
  slate: "border-slate-500/40 bg-slate-800 text-slate-200",
};

export function StatusPill({
  children,
  tone = "slate",
}: {
  children: React.ReactNode;
  tone?: keyof typeof toneClassNames;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold",
        toneClassNames[tone],
      )}
    >
      {children}
    </span>
  );
}
