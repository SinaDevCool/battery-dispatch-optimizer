"use client";

import { AlertTriangle, CheckCircle2, FileWarning, Scale } from "lucide-react";

import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type {
  AncillaryEligibilityResponse,
  EegComplianceResponse,
  LatestSignalResponse,
  StorageClassificationResponse,
} from "@/types/api";

export function RiskCompliancePanel({
  ancillary,
  classification,
  eeg,
  signal,
}: {
  ancillary?: AncillaryEligibilityResponse;
  classification?: StorageClassificationResponse;
  eeg?: EegComplianceResponse;
  signal?: LatestSignalResponse;
}) {
  const validationStatus =
    signal?.data?.metadata && signal.status === "ok" ? "audit trail present" : "not ready";

  return (
    <SectionCard title="Risk and compliance">
      <div className="space-y-3">
        <RiskRow
          icon={<Scale className="h-4 w-4" />}
          label="Storage classification"
          tone="blue"
          value={classification?.storage_classification ?? "not checked"}
        />
        <RiskRow
          icon={<CheckCircle2 className="h-4 w-4" />}
          label="EEG eligibility"
          tone={eeg?.eeg_eligible ? "emerald" : "amber"}
          value={eeg?.eeg_eligible ? "eligible" : eeg?.status ?? "not checked"}
        />
        <RiskRow
          icon={<AlertTriangle className="h-4 w-4" />}
          label="Ancillary products"
          tone={ancillary?.eligible ? "emerald" : "amber"}
          value={ancillary?.eligible ? "eligible" : ancillary?.reason ?? "not checked"}
        />
        <RiskRow
          icon={<FileWarning className="h-4 w-4" />}
          label="Dispatch audit"
          tone={validationStatus === "audit trail present" ? "emerald" : "amber"}
          value={validationStatus}
        />
      </div>
    </SectionCard>
  );
}

function RiskRow({
  icon,
  label,
  tone,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  tone: "amber" | "blue" | "emerald" | "red" | "slate";
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-800 bg-slate-900/45 px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <span className="text-slate-400">{icon}</span>
        <span className="text-sm text-slate-300">{label}</span>
      </div>
      <StatusPill tone={tone}>{value}</StatusPill>
    </div>
  );
}
