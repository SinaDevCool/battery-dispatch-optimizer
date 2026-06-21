"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, Loader2, MessageSquareText, Send, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { usePersona } from "@/components/persona-provider";
import { apiGet, apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { PersonaId } from "@/lib/personas";
import type { ApiEnvelope, JsonObject } from "@/types/api";

type PersonaAgentResponse = ApiEnvelope<{
  agent?: JsonObject & {
    name?: string;
    primary_question?: string;
  };
  ai_brief?: JsonObject & {
    brief?: string | null;
    message?: string;
    status?: string;
  };
  decision?: JsonObject & {
    answer_sections?: JsonObject & {
      short_answer?: string;
      where_to_check?: string;
    };
    human_answer?: string;
    recommended_actions?: string[];
    summary?: string;
  };
  suggested_questions?: string[];
}>;

type ChatMessage = {
  content: string;
  role: "assistant" | "user";
};

export function PersonaAiChatWidget() {
  const { aiEvidenceMode, selectedAsset, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const status = useQuery({
    enabled: isOpen,
    queryFn: () =>
      apiGet<PersonaAgentResponse>(
        `/assets/${selectedAssetId}/agents/persona/${personaId}/status?evidence_mode=${aiEvidenceMode}`,
      ),
    queryKey: ["persona-ai-chat-status", selectedAssetId, personaId, aiEvidenceMode],
  });

  const initialQuestion = useMemo(
    () =>
      status.data?.agent?.primary_question ??
      getFallbackQuestion(personaId),
    [personaId, status.data?.agent?.primary_question],
  );

  const askPersona = useMutation({
    mutationFn: (question: string) =>
      apiPost<PersonaAgentResponse>(
        `/assets/${selectedAssetId}/agents/persona/${personaId}/run`,
        {
          include_ai_brief: true,
          evidence_mode: aiEvidenceMode,
          question,
        },
      ),
    onSuccess: (response) => {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: buildAssistantAnswer(response),
        },
      ]);
    },
    onError: () => {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "I could not reach the AI intelligence service right now. Check the relevant evidence page for the asset, then try again after the backend is running.",
        },
      ]);
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, askPersona.isPending]);

  const sendQuestion = (question = input) => {
    const trimmed = question.trim();

    if (!trimmed || askPersona.isPending) {
      return;
    }

    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setInput("");
    askPersona.mutate(trimmed);
  };

  const suggestedQuestions = (
    status.data?.suggested_questions?.length
      ? status.data.suggested_questions
      : getFallbackQuestions(personaId, initialQuestion)
  ).slice(0, 3);
  const visibleMessages = messages.length
    ? messages
    : [
        {
          role: "assistant" as const,
          content: [
            `I am looking at this as ${persona.label}.`,
            `Mode: ${aiEvidenceMode === "mock" ? "Mock Data, using complete simulated evidence." : "Live Data, checking real production proof."}`,
            `Ask me about ${selectedAsset?.asset_name ?? selectedAssetId}, or start with: ${initialQuestion}`,
          ].join("\n\n"),
        },
      ];

  return (
    <div className="fixed bottom-5 right-5 z-50 flex max-w-[calc(100vw-2.5rem)] flex-col items-end gap-3">
      {isOpen ? (
        <section className="w-[390px] max-w-full overflow-hidden rounded-lg border border-sky-400/25 bg-slate-950 shadow-2xl shadow-black/50">
          <header className="flex items-start justify-between gap-3 border-b border-slate-800 bg-slate-900/80 px-4 py-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Bot className="h-4 w-4 shrink-0 text-sky-300" />
                AI Intelligence
              </div>
              <div className="mt-1 truncate text-xs text-slate-400">
                {persona.label} · {selectedAsset?.asset_name ?? selectedAssetId}
              </div>
            </div>
            <button
              aria-label="Close AI chat"
              className="rounded-md p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white"
              onClick={() => setIsOpen(false)}
              type="button"
            >
              <X className="h-4 w-4" />
            </button>
          </header>

          <div className="max-h-[430px] space-y-3 overflow-y-auto px-4 py-4">
            {visibleMessages.map((message, index) => (
              <div
                className={cn(
                  "rounded-lg px-3 py-2 text-sm leading-6",
                  message.role === "user"
                    ? "ml-8 bg-sky-500/15 text-sky-50"
                    : "mr-6 border border-slate-800 bg-slate-900/70 text-slate-200",
                )}
                key={`${message.role}-${index}`}
              >
                <FormattedAnswer content={message.content} />
              </div>
            ))}

            {askPersona.isPending ? (
              <div className="mr-6 flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 text-sm text-slate-300">
                <Loader2 className="h-4 w-4 animate-spin text-sky-300" />
                Reading the evidence for this persona...
              </div>
            ) : null}
            <div ref={scrollRef} />
          </div>

          <div className="border-t border-slate-800 px-4 py-3">
            <div className="mb-3 flex flex-wrap gap-2">
              {suggestedQuestions.map((question) => (
                <button
                  className="rounded-md border border-slate-700 px-2.5 py-1.5 text-left text-[11px] font-semibold text-slate-300 transition hover:border-sky-400/60 hover:text-sky-100"
                  disabled={askPersona.isPending}
                  key={question}
                  onClick={() => sendQuestion(question)}
                  type="button"
                >
                  {question}
                </button>
              ))}
            </div>

            <div className="flex gap-2">
              <textarea
                className="min-h-11 flex-1 resize-none rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-sky-400"
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendQuestion();
                  }
                }}
                placeholder="Ask this persona..."
                value={input}
              />
              <button
                aria-label="Send question"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-emerald-500 text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500"
                disabled={askPersona.isPending || !input.trim()}
                onClick={() => sendQuestion()}
                type="button"
              >
                {askPersona.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        </section>
      ) : null}

      <button
        className="flex items-center gap-2 rounded-lg border border-emerald-300/40 bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 shadow-xl shadow-black/40 transition hover:bg-emerald-400"
        onClick={() => setIsOpen((current) => !current)}
        type="button"
      >
        <MessageSquareText className="h-4 w-4" />
        Ask AI
      </button>
    </div>
  );
}

function getFallbackQuestion(personaId: PersonaId) {
  const questions: Partial<Record<PersonaId, string>> = {
    asset_owner: "What should I tell the owner this week?",
    investor_lender: "Is this bankable or still mock-backed?",
    project_developer: "Is this project ready for investment planning?",
    executive: "What should I escalate first?",
    client_success: "Is this battery bankable or profitable this month?",
    trading_desk: "Can I trade, paper trade, or wait?",
    automation_operator: "Can automation continue safely?",
    risk_compliance: "Can I defend this decision?",
    market_operations: "Which connector should I configure first?",
    forecast_quant: "Can I trust the forecast for bidding?",
    revenue_analyst: "Which revenue product creates most value?",
    all: "Which production gap should we solve first?",
  };

  return questions[personaId] ?? "Which production gap should we solve first?";
}

function getFallbackQuestions(personaId: PersonaId, initialQuestion: string) {
  const extras: Partial<Record<PersonaId, string[]>> = {
    client_success: [
      "What numbers should I show in the client update?",
      "Which revenue products created the value?",
    ],
    asset_owner: [
      "What revenue is modelled versus proven?",
      "Which production proof should I ask for next?",
    ],
    investor_lender: [
      "What diligence risk remains?",
      "What proof would make this lender-ready?",
    ],
    market_operations: [
      "What blocks production market access?",
      "Which credential unlocks the most evidence?",
    ],
    trading_desk: [
      "What blocks supervised live trading?",
      "Should bid sizing be reduced?",
    ],
    revenue_analyst: [
      "Which products were excluded from allocation and why?",
      "What is the next highest-value unlock?",
    ],
  };

  return [initialQuestion, ...(extras[personaId] ?? [
    "What is mock-ready versus production-ready?",
    "Which production gap should we solve first?",
  ])];
}

function buildAssistantAnswer(response: PersonaAgentResponse) {
  const aiBrief = response.ai_brief?.brief;
  if (typeof aiBrief === "string" && aiBrief.trim()) {
    return aiBrief;
  }

  const decision = response.decision;
  const sections = decision?.answer_sections;
  const recommendedActions = decision?.recommended_actions ?? [];
  const parts = [
    sections?.short_answer ?? decision?.human_answer ?? decision?.summary,
    sections?.where_to_check,
  ].filter(Boolean);

  if (recommendedActions.length) {
    parts.push(["Recommended next steps:", ...recommendedActions.slice(0, 3).map((action) => `- ${action}`)].join("\n"));
  }

  return (
    parts.join("\n\n") ||
    "I do not have enough evidence to answer this confidently. Check the relevant page for this persona, then ask me again with the specific asset or metric."
  );
}

function FormattedAnswer({ content }: { content: string }) {
  return (
    <div className="space-y-2">
      {content.split(/\n{2,}/).map((paragraph, index) => {
        const lines = paragraph.split("\n");
        const isList = lines.every((line) => line.trim().startsWith("- "));

        if (isList) {
          return (
            <ul className="list-disc space-y-1 pl-5" key={`${paragraph}-${index}`}>
              {lines.map((line) => (
                <li key={line}>{line.replace(/^- /, "")}</li>
              ))}
            </ul>
          );
        }

        return (
          <p className="whitespace-pre-wrap" key={`${paragraph}-${index}`}>
            {paragraph}
          </p>
        );
      })}
    </div>
  );
}
