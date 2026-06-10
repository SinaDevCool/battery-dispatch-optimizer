"use client";

import { Users } from "lucide-react";

import { usePersona } from "@/components/persona-provider";
import { PERSONA_GROUPS, personaProfiles } from "@/lib/personas";

export function PersonaSelector() {
  const { personaId, setPersonaId } = usePersona();

  return (
    <label className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs font-semibold text-slate-200">
      <Users className="h-3.5 w-3.5 text-sky-300" />
      <select
        aria-label="Persona view"
        className="bg-transparent text-xs font-semibold text-slate-100 outline-none"
        onChange={(event) => setPersonaId(event.target.value as typeof personaId)}
        value={personaId}
      >
        {PERSONA_GROUPS.map((group) => (
          <optgroup
            className="bg-slate-950 text-slate-400"
            key={group.label}
            label={group.label}
          >
            {group.ids.map((id) => (
              <option className="bg-slate-950 text-slate-100" key={id} value={id}>
                {personaProfiles[id].label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
  );
}
