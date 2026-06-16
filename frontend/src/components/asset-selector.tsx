"use client";

import { BatteryCharging, Check, ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { cn } from "@/lib/utils";
import type { Asset } from "@/types/api";

export function AssetSelector() {
  const {
    assets,
    isLoadingAssets,
    selectedAsset,
    selectedAssetId,
    setSelectedAssetId,
  } = useAssetContext();
  const [isOpen, setIsOpen] = useState(false);
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement | null>(null);
  const displayAsset = selectedAsset ?? buildFallbackAsset(selectedAssetId);
  const isDisabled = isLoadingAssets || !assets.length;

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleSelectAsset = (assetId: string) => {
    setSelectedAssetId(assetId);
    setIsOpen(false);
  };

  return (
    <div className="relative min-w-72" ref={rootRef}>
      <button
        aria-controls={menuId}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        className={cn(
          "flex w-full items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-left shadow-sm shadow-black/20 transition hover:border-sky-500/40 hover:bg-slate-900/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400",
          isOpen && "border-sky-400/50 bg-slate-900",
          isDisabled && "cursor-not-allowed opacity-70 hover:border-slate-800 hover:bg-slate-950",
        )}
        disabled={isDisabled}
        onClick={() => setIsOpen((current) => !current)}
        type="button"
      >
        <BatteryCharging className="h-4 w-4 shrink-0 text-sky-300" />
        <div className="min-w-0 flex-1">
          <div className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-slate-500">
            Selected asset
          </div>
          <div className="mt-0.5 truncate text-sm font-semibold text-slate-100">
            {getAssetLabel(displayAsset)}
          </div>
          <div className="mt-0.5 flex min-w-0 items-center gap-2 text-[0.68rem] font-medium text-slate-500">
            <span className="truncate">{formatAssetType(displayAsset.asset_type)}</span>
            <span className="h-1 w-1 shrink-0 rounded-full bg-slate-700" />
            <span className="uppercase">{displayAsset.data_mode ?? "mock"}</span>
          </div>
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-slate-500 transition",
            isOpen && "rotate-180 text-sky-300",
          )}
        />
      </button>

      {isOpen ? (
        <div
          className="absolute right-0 z-50 mt-2 w-[25rem] max-w-[calc(100vw-2rem)] overflow-hidden rounded-lg border border-slate-700 bg-slate-950 shadow-2xl shadow-black/40"
          id={menuId}
          role="listbox"
        >
          <div className="border-b border-slate-800 px-3 py-2">
            <div className="text-[0.62rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
              Investor demo assets
            </div>
            <div className="mt-0.5 text-xs text-slate-400">
              Choose the mock asset profile that drives the workflow.
            </div>
          </div>
          <div className="max-h-80 overflow-y-auto p-1">
          {assets.map((asset) => {
            const assetId = asset.asset_id ?? "";
            const isSelected = assetId === selectedAssetId;

            return (
              <button
                aria-selected={isSelected}
                className={cn(
                  "grid w-full grid-cols-[1fr_auto] gap-3 rounded-md px-3 py-2.5 text-left transition hover:bg-slate-900",
                  isSelected && "bg-sky-400/10",
                )}
                key={assetId}
                onClick={() => handleSelectAsset(assetId)}
                role="option"
                type="button"
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold text-slate-100">
                    {getAssetLabel(asset)}
                  </span>
                  <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[0.7rem] font-medium text-slate-400">
                    <span>{formatAssetType(asset.asset_type)}</span>
                    <span className="text-slate-700">/</span>
                    <span>{formatAssetSize(asset)}</span>
                    <span className="text-slate-700">/</span>
                    <span>{asset.market ?? "market pending"}</span>
                  </span>
                </span>
                <span className="flex items-start gap-2">
                  <span
                    className={cn(
                      "rounded-full border px-2 py-0.5 text-[0.62rem] font-bold uppercase tracking-[0.12em]",
                      asset.data_mode === "production"
                        ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
                        : "border-sky-400/30 bg-sky-400/10 text-sky-200",
                    )}
                  >
                    {asset.data_mode ?? "mock"}
                  </span>
                  {isSelected ? (
                    <Check className="mt-0.5 h-4 w-4 text-sky-300" />
                  ) : null}
                </span>
              </button>
            );
          })}
          </div>
        </div>
      ) : null}
      <div className="sr-only" aria-live="polite">
        Selected asset: {getAssetLabel(displayAsset)}
      </div>
    </div>
  );
}

function buildFallbackAsset(assetId: string): Asset {
  return {
    asset_id: assetId,
    asset_name: assetId,
    data_mode: "mock",
  };
}

function getAssetLabel(asset?: Asset) {
  return String(
    asset?.asset_name ?? asset?.site_name ?? asset?.asset_id ?? "Asset pending",
  );
}

function formatAssetType(assetType?: string) {
  if (!assetType) {
    return "asset";
  }

  return assetType.replaceAll("_", " ");
}

function formatAssetSize(asset: Asset) {
  const capacity = formatNumber(asset.capacity_mwh);
  const power = formatNumber(asset.max_discharge_power_mw ?? asset.max_charge_power_mw);

  if (capacity && power) {
    return `${capacity} MWh / ${power} MW`;
  }

  if (capacity) {
    return `${capacity} MWh`;
  }

  if (power) {
    return `${power} MW`;
  }

  return "size pending";
}

function formatNumber(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }

  return new Intl.NumberFormat("en", {
    maximumFractionDigits: 1,
    minimumFractionDigits: Number.isInteger(value) ? 0 : 1,
  }).format(value);
}
