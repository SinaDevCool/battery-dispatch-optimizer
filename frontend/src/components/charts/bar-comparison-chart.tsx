"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TableRow } from "@/types/api";

export function BarComparisonChart({
  data,
  xKey,
  yKey,
}: {
  data: TableRow[];
  xKey: string;
  yKey: string;
}) {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer height="100%" width="100%">
        <BarChart data={data} margin={{ bottom: 22, left: 0, right: 14, top: 8 }}>
          <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
          <XAxis
            angle={-8}
            dataKey={xKey}
            height={48}
            stroke="#64748b"
            tick={{ fontSize: 11 }}
          />
          <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#e2e8f0",
            }}
          />
          <Bar dataKey={yKey} fill="#60a5fa" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
