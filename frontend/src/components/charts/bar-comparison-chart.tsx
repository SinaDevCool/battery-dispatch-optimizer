"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
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
  const { ref, width } = useChartWidth();

  return (
    <div className="h-[300px] min-h-[300px] w-full min-w-0" ref={ref}>
      {width > 0 ? (
        <BarChart
          data={data}
          height={300}
          margin={{ bottom: 22, left: 0, right: 14, top: 8 }}
          width={width}
        >
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
