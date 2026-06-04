"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
} from "react";

import {
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

    if (storedValue && isPersonaId(storedValue)) {
      return storedValue;
    }

    return "all";
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

export function usePersona() {
  const context = useContext(PersonaContext);

  if (!context) {
    throw new Error("usePersona must be used within PersonaProvider.");
  }

  return context;
}
