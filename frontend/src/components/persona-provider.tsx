"use client";

import {
  createContext,
  useContext,
  useMemo,
  useSyncExternalStore,
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
const PERSONA_STORAGE_EVENT = "battery-trader-persona-change";

export function PersonaProvider({ children }: { children: React.ReactNode }) {
  const personaId = useSyncExternalStore(
    subscribeToPersonaStorage,
    getStoredPersonaId,
    getDefaultPersonaId,
  );

  const setPersonaId = (nextPersonaId: PersonaId) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, nextPersonaId);
      window.dispatchEvent(new Event(PERSONA_STORAGE_EVENT));
    }
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

function subscribeToPersonaStorage(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(PERSONA_STORAGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(PERSONA_STORAGE_EVENT, onStoreChange);
  };
}

function getStoredPersonaId(): PersonaId {
  return (
    migrateStoredPersonaId(window.localStorage.getItem(STORAGE_KEY)) ??
    DEFAULT_PERSONA_ID
  );
}

function getDefaultPersonaId(): PersonaId {
  return DEFAULT_PERSONA_ID;
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
