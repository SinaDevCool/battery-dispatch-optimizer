import { StatusPill } from "@/components/status-pill";
import { demoStatusTone, formatDemoStatus } from "@/lib/demo-status";
import type { JsonValue, TableRow } from "@/types/api";

type ProofCardField = {
  key: string;
  label: string;
};

export function ProofCardGrid({
  fields,
  rows,
  statusKey = "status",
  titleKey,
}: {
  fields: ProofCardField[];
  rows: TableRow[];
  statusKey?: string;
  titleKey: string;
}) {
  if (!rows.length) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">
        No proof available yet.
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {rows.map((row, index) => {
        const status = row[statusKey];

        return (
          <article
            className="min-h-52 rounded-lg border border-slate-800 bg-slate-900/55 p-4"
            key={`${String(row[titleKey] ?? "proof")}-${index}`}
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-sm font-semibold leading-5 text-slate-100">
                {formatValue(row[titleKey])}
              </h3>
              {status !== undefined ? (
                <StatusPill tone={demoStatusTone(status)}>
                  {formatDemoStatus(status)}
                </StatusPill>
              ) : null}
            </div>
            <div className="mt-4 space-y-3">
              {fields.map((field) => (
                <div key={field.key}>
                  <div className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-slate-500">
                    {field.label}
                  </div>
                  <p className="mt-1 text-sm leading-5 text-slate-300">
                    {formatValue(row[field.key])}
                  </p>
                </div>
              ))}
            </div>
          </article>
        );
      })}
    </div>
  );
}

function formatValue(value: JsonValue | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (Array.isArray(value)) {
    return value.length ? value.map(formatValue).join("; ") : "-";
  }

  if (typeof value === "object") {
    if ("message" in value && value.message) {
      return String(value.message);
    }

    return JSON.stringify(value);
  }

  return String(value);
}
