"use client";

import { Loader2, Play, RefreshCw } from "lucide-react";
import { useState } from "react";

import { apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ApiEnvelope } from "@/types/api";

type ActionButtonProps = {
  endpoint: string;
  label: string;
  onSuccess?: (response: ApiEnvelope) => void;
  refetch?: () => void | Promise<unknown>;
  variant?: "primary" | "secondary";
};

export function ActionButton({
  endpoint,
  label,
  onSuccess,
  refetch,
  variant = "secondary",
}: ActionButtonProps) {
  const [isPending, setIsPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [tone, setTone] = useState<"error" | "success" | "warning">("success");

  const runAction = async () => {
    setIsPending(true);
    setMessage(null);

    try {
      const response = await apiPost<ApiEnvelope>(endpoint);

      if (response.status === "ok") {
        setTone("success");
      } else if (response.status === "error") {
        setTone("error");
      } else {
        setTone("warning");
      }

      setMessage(response.message ?? `Action returned status: ${response.status}`);
      onSuccess?.(response);
      await refetch?.();
    } catch (error) {
      setTone("error");
      setMessage(error instanceof Error ? error.message : "Action failed.");
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <button
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
          variant === "primary"
            ? "border-emerald-400/35 bg-emerald-400/15 text-emerald-100 hover:bg-emerald-400/25"
            : "border-sky-400/30 bg-sky-400/10 text-sky-100 hover:bg-sky-400/20",
        )}
        disabled={isPending}
        onClick={runAction}
        type="button"
      >
        {isPending ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : variant === "primary" ? (
          <Play className="h-3.5 w-3.5" />
        ) : (
          <RefreshCw className="h-3.5 w-3.5" />
        )}
        {isPending ? "Running..." : label}
      </button>

      {message ? (
        <div
          className={cn(
            "max-w-sm rounded-md border px-3 py-2 text-xs leading-5",
            tone === "success" &&
              "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
            tone === "warning" &&
              "border-amber-400/30 bg-amber-400/10 text-amber-100",
            tone === "error" && "border-red-400/30 bg-red-400/10 text-red-100",
          )}
        >
          {message}
        </div>
      ) : null}
    </div>
  );
}
