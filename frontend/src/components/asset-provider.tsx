"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
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
const ASSET_STORAGE_EVENT = "battery-optimizer-selected-asset-change";

const AssetContext = createContext<AssetContextValue | undefined>(undefined);

export function AssetProvider({ children }: { children: React.ReactNode }) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isLoadingAssets, setIsLoadingAssets] = useState(true);
  const [selectedAssetId, setSelectedAssetIdState] = useState(DEFAULT_ASSET_ID);

  useEffect(() => {
    const syncSelectedAssetId = () => {
      setSelectedAssetIdState(getStoredSelectedAssetId());
    };

    syncSelectedAssetId();
    return subscribeToSelectedAssetStorage(syncSelectedAssetId);
  }, []);

  useEffect(() => {
    let isCancelled = false;

    apiGet<AssetListResponse>("/assets")
      .then((response) => {
        if (!isCancelled) {
          setAssets(response.assets ?? []);
          setSelectedAssetIdState(getStoredSelectedAssetId());
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setAssets([]);
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoadingAssets(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  const setSelectedAssetId = useCallback((assetId: string) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, assetId);
      window.dispatchEvent(new Event(ASSET_STORAGE_EVENT));
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
      isLoadingAssets,
      selectedAsset,
      selectedAssetId: effectiveSelectedAssetId,
      setSelectedAssetId,
    }),
    [
      assets,
      effectiveSelectedAssetId,
      isLoadingAssets,
      selectedAsset,
      setSelectedAssetId,
    ],
  );

  return (
    <AssetContext.Provider value={value}>{children}</AssetContext.Provider>
  );
}

function subscribeToSelectedAssetStorage(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(ASSET_STORAGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(ASSET_STORAGE_EVENT, onStoreChange);
  };
}

function getStoredSelectedAssetId() {
  return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_ASSET_ID;
}

export function useAssetContext() {
  const context = useContext(AssetContext);

  if (!context) {
    throw new Error("useAssetContext must be used inside AssetProvider");
  }

  return context;
}
