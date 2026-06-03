"use client";

import { useEffect, useRef, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DispatchRow } from "@/types/api";

export function DispatchChart({ rows }: { rows: DispatchRow[] }) {
  const { ref, width } = useChartWidth();
  const data = rows.map((row) => ({
    ...row,
    time: String(row.timestamp).slice(11, 16),
  }));

  return (
    <div className="h-[340px] min-h-[340px] w-full min-w-0" ref={ref}>
      {width > 0 ? (
        <LineChart
          data={data}
          height={340}
          margin={{ bottom: 10, left: 0, right: 6, top: 8 }}
          width={width}
        >
          <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
          <YAxis
            stroke="#38bdf8"
            tick={{ fontSize: 11 }}
            yAxisId="price"
          />
          <YAxis
            orientation="right"
            stroke="#34d399"
            tick={{ fontSize: 11 }}
            yAxisId="soc"
          />
          <Tooltip
            contentStyle={{
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#e2e8f0",
            }}
          />
          <Legend
            iconType="circle"
            wrapperStyle={{
              color: "#cbd5e1",
              fontSize: 12,
              paddingTop: 8,
            }}
          />
          <Line
            dataKey="price"
            dot={false}
            name="Price"
            stroke="#38bdf8"
            strokeWidth={2}
            type="monotone"
            yAxisId="price"
          />
          <Line
            dataKey="soc_mwh"
            dot={false}
            name="SOC"
            stroke="#34d399"
            strokeWidth={2}
            type="stepAfter"
            yAxisId="soc"
          />
          <Line
            dataKey="total_pnl_eur"
            dot={false}
            name="Cumulative PnL"
            stroke="#fbbf24"
            strokeWidth={2}
            type="monotone"
            yAxisId="price"
          />
        </LineChart>
      ) : null}
    </div>
  );
}

function useChartWidth() {
  const ref = useRef<HTMLDivElement | null>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const element = ref.current;

    if (!element) {
      return undefined;
    }

    const observer = new ResizeObserver(([entry]) => {
      const nextWidth = Math.floor(entry.contentRect.width);

      if (nextWidth > 0) {
        setWidth(nextWidth);
      }
    });

    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  return { ref, width };
}
