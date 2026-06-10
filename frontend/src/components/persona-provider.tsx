"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
} from "react";

import {
  DEFAULT_PERSONA_ID,
  isPersonaId,
  personaProfiles,
  type PersonaId,
  type PersonaProfile,
} from "@/lib/personas";

type PersonaContextValue = {
  persona: PersonaProfile;
  personaId: PersonaId;
  setPersonaId: (personaId: PersonaId) => void;
};

const PersonaContext = createContext<PersonaContextValue | null>(null);
const STORAGE_KEY = "battery-trader-persona";

export function PersonaProvider({ children }: { children: React.ReactNode }) {
  const [personaId, setPersonaIdState] = useState<PersonaId>(() => {
    if (typeof window === "undefined") {
      return "all";
    }

    const storedValue = window.localStorage.getItem(STORAGE_KEY);
    const migratedPersonaId = migrateStoredPersonaId(storedValue);

    if (migratedPersonaId) {
      return migratedPersonaId;
    }

    return DEFAULT_PERSONA_ID;
  });

  const setPersonaId = (nextPersonaId: PersonaId) => {
    setPersonaIdState(nextPersonaId);
    window.localStorage.setItem(STORAGE_KEY, nextPersonaId);
  };

  const value = useMemo(
    () => ({
      persona: personaProfiles[personaId],
      personaId,
      setPersonaId,
    }),
    [personaId],
  );

  return (
    <PersonaContext.Provider value={value}>
      {children}
    </PersonaContext.Provider>
  );
}

function migrateStoredPersonaId(value: string | null): PersonaId | null {
  if (!value) {
    return null;
  }

  const migrationMap: Record<string, PersonaId> = {
    automation_manager: "automation_operator",
    optimizer: "forecast_quant",
    trader: "trading_desk",
  };

  const migratedValue = migrationMap[value] ?? value;

  return isPersonaId(migratedValue) ? migratedValue : null;
}

export function usePersona() {
  const context = useContext(PersonaContext);

  if (!context) {
    throw new Error("usePersona must be used within PersonaProvider.");
  }

  return context;
}
