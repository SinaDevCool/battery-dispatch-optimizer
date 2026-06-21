export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const DATA_MODE_STORAGE_KEY = "battery_optimizer_ai_evidence_mode";

export function getApiBaseUrl() {
  if (typeof window === "undefined") {
    return API_BASE_URL;
  }

  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return normalizeBrowserApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);
  }

  return `http://${window.location.hostname}:8000`;
}

function normalizeBrowserApiBaseUrl(configuredBaseUrl: string) {
  try {
    const url = new URL(configuredBaseUrl);
    const isLoopbackTarget = ["127.0.0.1", "localhost", "::1"].includes(url.hostname);
    const isLoopbackPage = ["127.0.0.1", "localhost", "::1"].includes(window.location.hostname);

    if (isLoopbackTarget && !isLoopbackPage) {
      url.hostname = window.location.hostname;
      url.port = url.port || "8000";
      return url.toString().replace(/\/$/, "");
    }

    return configuredBaseUrl.replace(/\/$/, "");
  } catch {
    return configuredBaseUrl;
  }
}

export type ApiStatus = "ok" | "not_found" | "error" | "missing_token" | string;

function getDataModeHeader() {
  if (typeof window === "undefined") {
    return "mock";
  }

  return window.localStorage.getItem(DATA_MODE_STORAGE_KEY) === "live"
    ? "live"
    : "mock";
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    headers: {
      Accept: "application/json",
      "X-Data-Mode": getDataModeHeader(),
    },
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function apiPost<T>(endpoint: string, body?: unknown): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    body: body ? JSON.stringify(body) : undefined,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-Data-Mode": getDataModeHeader(),
    },
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}
