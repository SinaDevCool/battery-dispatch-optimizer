"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DispatchRow } from "@/types/api";

export function DispatchChart({ rows }: { rows: DispatchRow[] }) {
  const data = rows.map((row) => ({
    ...row,
    time: String(row.timestamp).slice(11, 16),
  }));

  return (
    <div className="h-[340px] w-full">
      <ResponsiveContainer height="100%" width="100%">
        <LineChart data={data} margin={{ bottom: 10, left: 0, right: 14, top: 8 }}>
          <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
          <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#e2e8f0",
            }}
          />
          <Line
            dataKey="price"
            dot={false}
            name="Price"
            stroke="#38bdf8"
            strokeWidth={2}
            type="monotone"
          />
          <Line
            dataKey="soc_mwh"
            dot={false}
            name="SOC"
            stroke="#34d399"
            strokeWidth={2}
            type="stepAfter"
          />
          <Line
            dataKey="total_pnl_eur"
            dot={false}
            name="Cumulative PnL"
            stroke="#fbbf24"
            strokeWidth={2}
            type="monotone"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
