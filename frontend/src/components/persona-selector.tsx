"use client";

import { Building2, MonitorCog, Users } from "lucide-react";

import { usePersona } from "@/components/persona-provider";
import { PERSONA_GROUPS, type PersonaId, personaProfiles } from "@/lib/personas";
import { cn } from "@/lib/utils";

export function PersonaSelector() {
  const { personaId, setPersonaId } = usePersona();
  const activeGroup =
    PERSONA_GROUPS.find((group) =>
      (group.ids as readonly PersonaId[]).includes(personaId),
    ) ??
    PERSONA_GROUPS[0];

  return (
    <div className="inline-flex items-center gap-2">
      <div className="flex rounded-md border border-slate-800 bg-slate-950/80 p-1">
        {PERSONA_GROUPS.map((group) => {
          const isActive = group.label === activeGroup.label;
          const Icon =
            group.label === "Client Evidence Portal"
              ? Building2
              : group.label === "Internal Trading OS"
                ? MonitorCog
                : Users;

          return (
            <button
              aria-label={group.label}
              className={cn(
                "inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition hover:bg-slate-900 hover:text-slate-100",
                isActive && "bg-sky-400/10 text-sky-100",
              )}
              key={group.label}
              onClick={() => setPersonaId(group.ids[0] as PersonaId)}
              title={group.label}
              type="button"
            >
              <Icon className="h-3.5 w-3.5" />
            </button>
          );
        })}
      </div>

      <label className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs font-semibold text-slate-200">
        <Users className="h-3.5 w-3.5 text-sky-300" />
        <select
          aria-label="Persona view"
          className="max-w-44 bg-transparent text-xs font-semibold text-slate-100 outline-none"
          onChange={(event) => setPersonaId(event.target.value as PersonaId)}
          value={personaId}
        >
          {activeGroup.ids.map((id) => (
            <option className="bg-slate-950 text-slate-100" key={id} value={id}>
              {personaProfiles[id].label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
