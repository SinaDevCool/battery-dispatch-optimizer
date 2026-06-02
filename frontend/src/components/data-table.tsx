import type { JsonValue, TableRow } from "@/types/api";

export function DataTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: TableRow[];
}) {
  if (!rows.length) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">
        No rows available.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table>
        <thead className="bg-slate-900/80">
          <tr>
            {columns.map((column) => (
              <th key={column}>{column.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr className="bg-slate-950/40" key={rowIndex}>
              {columns.map((column) => (
                <td key={column}>{formatCell(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: JsonValue | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? value : value.toFixed(2);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}
