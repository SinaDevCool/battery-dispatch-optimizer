"use client";

import { useQuery } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import { apiGet } from "@/lib/api";
import type { Asset, AssetListResponse } from "@/types/api";

type AssetContextValue = {
  assets: Asset[];
  isLoadingAssets: boolean;
  selectedAsset?: Asset;
  selectedAssetId: string;
  setSelectedAssetId: (assetId: string) => void;
};

const DEFAULT_ASSET_ID = "default_site";
const STORAGE_KEY = "battery_optimizer_selected_asset_id";

const AssetContext = createContext<AssetContextValue | undefined>(undefined);

export function AssetProvider({ children }: { children: React.ReactNode }) {
  const [selectedAssetId, setSelectedAssetIdState] = useState(() => {
    if (typeof window === "undefined") {
      return DEFAULT_ASSET_ID;
    }

    return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_ASSET_ID;
  });

  const assetsQuery = useQuery({
    queryFn: () => apiGet<AssetListResponse>("/assets"),
    queryKey: ["assets"],
  });

  const assets = useMemo(() => assetsQuery.data?.assets ?? [], [assetsQuery.data]);

  const setSelectedAssetId = useCallback((assetId: string) => {
    setSelectedAssetIdState(assetId);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, assetId);
    }
  }, []);

  const effectiveSelectedAssetId = useMemo(() => {
    if (!assets.length) {
      return selectedAssetId;
    }

    const selectedExists = assets.some(
      (asset) => asset.asset_id === selectedAssetId,
    );

    return selectedExists
      ? selectedAssetId
      : assets[0]?.asset_id ?? DEFAULT_ASSET_ID;
  }, [assets, selectedAssetId]);

  const selectedAsset = assets.find(
    (asset) => asset.asset_id === effectiveSelectedAssetId,
  );

  const value = useMemo(
    () => ({
      assets,
      isLoadingAssets: assetsQuery.isLoading,
      selectedAsset,
      selectedAssetId: effectiveSelectedAssetId,
      setSelectedAssetId,
    }),
    [
      assets,
      assetsQuery.isLoading,
      effectiveSelectedAssetId,
      selectedAsset,
      setSelectedAssetId,
    ],
  );

  return (
    <AssetContext.Provider value={value}>{children}</AssetContext.Provider>
  );
}

export function useAssetContext() {
  const context = useContext(AssetContext);

  if (!context) {
    throw new Error("useAssetContext must be used inside AssetProvider");
  }

  return context;
}
