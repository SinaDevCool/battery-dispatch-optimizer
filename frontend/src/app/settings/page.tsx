"use client";

import { useQuery } from "@tanstack/react-query";

import { DataTable } from "@/components/data-table";
import { PageHeading } from "@/components/page-heading";
import { SectionCard } from "@/components/section-card";
import { apiGet } from "@/lib/api";
import type { ClientConfigResponse } from "@/types/api";

export default function SettingsPage() {
  const config = useQuery({
    queryFn: () => apiGet<ClientConfigResponse>("/client/config"),
    queryKey: ["client-config"],
  });

  return (
    <>
      <PageHeading
        description="Configuration is shown read-only in the first product UI. Editing should later move behind role-based permissions and audit logging."
        eyebrow="Configuration"
        title="Settings"
      />

      <SectionCard title="Client configuration">
        <DataTable
          columns={["field", "value"]}
          rows={Object.entries(config.data?.config ?? {}).map(([field, value]) => ({
            field,
            value,
          }))}
        />
      </SectionCard>
    </>
  );
}
