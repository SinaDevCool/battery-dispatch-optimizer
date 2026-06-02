"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMemo } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useMemo(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchInterval: 30_000,
            retry: 1,
            staleTime: 15_000,
          },
        },
      }),
    [],
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
