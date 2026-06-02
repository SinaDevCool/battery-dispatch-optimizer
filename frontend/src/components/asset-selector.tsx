"use client";

import { BatteryCharging } from "lucide-react";

import { useAssetContext } from "@/components/asset-provider";

export function AssetSelector() {
  const {
    assets,
    isLoadingAssets,
    selectedAsset,
    selectedAssetId,
    setSelectedAssetId,
  } = useAssetContext();

  return (
    <label className="flex min-w-64 items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2">
      <BatteryCharging className="h-4 w-4 text-sky-300" />
      <div className="min-w-0 flex-1">
        <div className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-slate-500">
          Selected asset
        </div>
        <select
          className="mt-0.5 w-full bg-transparent text-sm font-semibold text-slate-100 outline-none"
          disabled={isLoadingAssets || !assets.length}
          onChange={(event) => setSelectedAssetId(event.target.value)}
          value={selectedAssetId}
        >
          {!assets.length ? (
            <option value={selectedAssetId}>{selectedAssetId}</option>
          ) : null}
          {assets.map((asset) => {
            const assetId = asset.asset_id ?? "";
            const label =
              asset.asset_name ?? asset.site_name ?? asset.asset_id ?? assetId;

            return (
              <option key={assetId} value={assetId}>
                {String(label)}
              </option>
            );
          })}
        </select>
      </div>
      <div className="hidden text-xs text-slate-500 2xl:block">
        {selectedAsset?.asset_id ?? selectedAssetId}
      </div>
    </label>
  );
}
