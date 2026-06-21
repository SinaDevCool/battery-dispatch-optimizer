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
  aiEvidenceMode: AiEvidenceMode;
  assets: Asset[];
  isLoadingAssets: boolean;
  selectedAsset?: Asset;
  selectedAssetId: string;
  setAiEvidenceMode: (mode: AiEvidenceMode) => void;
  setSelectedAssetId: (assetId: string) => void;
};

export type AiEvidenceMode = "live" | "mock";

const DEFAULT_ASSET_ID = "default_site";
const STORAGE_KEY = "battery_optimizer_selected_asset_id";
const AI_EVIDENCE_MODE_STORAGE_KEY = "battery_optimizer_ai_evidence_mode";
const ASSET_STORAGE_EVENT = "battery-optimizer-selected-asset-change";
const AI_EVIDENCE_MODE_STORAGE_EVENT = "battery-optimizer-ai-evidence-mode-change";

const AssetContext = createContext<AssetContextValue | undefined>(undefined);

export function AssetProvider({ children }: { children: React.ReactNode }) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [aiEvidenceMode, setAiEvidenceModeState] = useState<AiEvidenceMode>("mock");
  const [isLoadingAssets, setIsLoadingAssets] = useState(true);
  const [selectedAssetId, setSelectedAssetIdState] = useState(DEFAULT_ASSET_ID);

  useEffect(() => {
    const syncSelectedAssetId = () => {
      setSelectedAssetIdState(getStoredSelectedAssetId());
      setAiEvidenceModeState(getStoredAiEvidenceMode());
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
  }, [aiEvidenceMode]);

  const setSelectedAssetId = useCallback((assetId: string) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, assetId);
      window.dispatchEvent(new Event(ASSET_STORAGE_EVENT));
    }
  }, []);

  const setAiEvidenceMode = useCallback((mode: AiEvidenceMode) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(AI_EVIDENCE_MODE_STORAGE_KEY, mode);
      window.dispatchEvent(new Event(AI_EVIDENCE_MODE_STORAGE_EVENT));
    }

    setAiEvidenceModeState(mode);
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
      aiEvidenceMode,
      assets,
      isLoadingAssets,
      selectedAsset,
      selectedAssetId: effectiveSelectedAssetId,
      setAiEvidenceMode,
      setSelectedAssetId,
    }),
    [
      aiEvidenceMode,
      assets,
      effectiveSelectedAssetId,
      isLoadingAssets,
      selectedAsset,
      setAiEvidenceMode,
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
  window.addEventListener(AI_EVIDENCE_MODE_STORAGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(ASSET_STORAGE_EVENT, onStoreChange);
    window.removeEventListener(AI_EVIDENCE_MODE_STORAGE_EVENT, onStoreChange);
  };
}

function getStoredSelectedAssetId() {
  return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_ASSET_ID;
}

function getStoredAiEvidenceMode(): AiEvidenceMode {
  const value = window.localStorage.getItem(AI_EVIDENCE_MODE_STORAGE_KEY);
  return value === "live" ? "live" : "mock";
}

export function useAssetContext() {
  const context = useContext(AssetContext);

  if (!context) {
    throw new Error("useAssetContext must be used inside AssetProvider");
  }

  return context;
}
