"use client";

import { useEffect, useState } from "react";

import { StatusPill } from "@/components/status-pill";
import { apiGet } from "@/lib/api";

type DataReadinessDomain = {
  current_status?: string;
  domain?: string;
  label?: string;
  production_claim_allowed?: boolean;
  source_name?: string;
  source_type?: string;
};

type DataReadinessResponse = {
  data_mode?: "live" | "mock" | string;
  domains?: DataReadinessDomain[];
  status?: string;
  summary?: {
    live_missing_count?: number;
    production_claim_allowed?: boolean;
  };
};

const visibleDomains = ["forecasts", "revenue", "telemetry", "settlement", "ai_evidence"];

export function DataSourceBadges({
  assetId,
  dataMode,
}: {
  assetId: string;
  dataMode: "live" | "mock";
}) {
  const [readiness, setReadiness] = useState<DataReadinessResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    apiGet<DataReadinessResponse>(`/system/data-readiness?asset_id=${assetId}`)
      .then((response) => {
        if (!cancelled) {
          setReadiness(response);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setReadiness(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [assetId, dataMode]);

  const domains = (readiness?.domains ?? [])
    .filter((domain) => visibleDomains.includes(String(domain.domain)))
    .slice(0, 5);

  if (!domains.length) {
    return null;
  }

  return (
    <div className="flex min-w-0 flex-wrap items-center gap-2">
      {domains.map((domain) => (
        <span
          className="inline-flex min-w-0 items-center gap-1 rounded-md border border-slate-800 bg-slate-950/70 px-2 py-1 text-[11px]"
          key={domain.domain}
          title={`${domain.source_name ?? "source"} / ${domain.source_type ?? "source type"}`}
        >
          <span className="max-w-[90px] truncate font-semibold text-slate-300">
            {domain.label ?? domain.domain}
          </span>
          <StatusPill tone={getTone(domain, dataMode)}>
            {formatStatus(domain, dataMode)}
          </StatusPill>
        </span>
      ))}
    </div>
  );
}

function getTone(domain: DataReadinessDomain, dataMode: "live" | "mock") {
  if (dataMode === "mock") {
    return "emerald" as const;
  }

  return domain.production_claim_allowed ? "emerald" as const : "amber" as const;
}

function formatStatus(domain: DataReadinessDomain, dataMode: "live" | "mock") {
  if (dataMode === "mock") {
    return "mock";
  }

  return domain.production_claim_allowed ? "live" : "missing";
}
