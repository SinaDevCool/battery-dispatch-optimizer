"use client";

import { useSyncExternalStore } from "react";

import { API_BASE_URL, getApiBaseUrl } from "@/lib/api";

export function useApiBaseUrl() {
  return useSyncExternalStore(subscribe, getApiBaseUrl, getServerSnapshot);
}

function subscribe() {
  return () => {};
}

function getServerSnapshot() {
  return API_BASE_URL;
}
