export function ExecutionMetric({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}
