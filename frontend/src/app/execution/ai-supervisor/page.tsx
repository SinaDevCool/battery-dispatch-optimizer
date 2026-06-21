"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, Loader2, Play, RefreshCw, Send } from "lucide-react";
import { useState } from "react";

import { useAssetContext } from "@/components/asset-provider";
import { DataTable } from "@/components/data-table";
import { DecisionBrief } from "@/components/decision-brief";
import { KpiCard } from "@/components/kpi-card";
import { PageHeading } from "@/components/page-heading";
import { usePersona } from "@/components/persona-provider";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { apiGet, apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { PersonaId } from "@/lib/personas";
import type { ApiEnvelope, JsonObject, TableRow } from "@/types/api";

type Tone = "amber" | "blue" | "emerald" | "red" | "slate";

type TradingSupervisorException = TableRow & {
  code?: string;
  message?: string;
  next_action?: string;
  severity?: string;
  source?: string;
};

type TradingSupervisorResponse = ApiEnvelope<{
  agent?: JsonObject & {
    agent_id?: string;
    llm_model?: string;
    mode?: string;
    name?: string;
  };
  ai_brief?: JsonObject & {
    brief?: string | null;
    message?: string;
    model?: string;
    status?: string;
  };
  asset_id?: string;
  automation_action?: string;
  context?: JsonObject & {
    automation_control?: JsonObject;
    evidence?: JsonObject;
    forecast_confidence?: JsonObject;
    latest_signal?: JsonObject;
    orchestrator?: JsonObject;
  };
  daily_brief?: JsonObject;
  decision?: string;
  exception_count?: number;
  exceptions?: TradingSupervisorException[];
  generated_at?: string;
  highest_severity?: string;
  operator_question?: string | null;
  recommendation?: JsonObject & {
    next_action?: string;
    summary?: string;
  };
  safe_actions?: TableRow[];
  suggested_questions?: string[];
  supervisor_status?: string;
}>;

type TradingSupervisorHistoryResponse = ApiEnvelope<{
  history?: TableRow[];
  history_count?: number;
}>;

type PersonaAgentResponse = ApiEnvelope<{
  agent?: JsonObject & {
    agent_id?: string;
    decision_type?: string;
    name?: string;
    primary_question?: string;
  };
  ai_brief?: JsonObject & {
    brief?: string | null;
    message?: string;
    model?: string;
    status?: string;
  };
  decision?: JsonObject & {
    business_value?: string;
    decision?: string;
    human_answer?: string;
    next_action?: string;
    placeholder_calculations?: JsonObject;
    recommended_actions?: string[];
    score?: number;
    score_label?: string;
    status?: string;
    summary?: string;
    top_blocker?: string;
    what_it_means?: string;
  };
  persona_id?: string;
  suggested_questions?: string[];
}>;

export default function AiSupervisorPage() {
  const { aiEvidenceMode, selectedAsset, selectedAssetId } = useAssetContext();
  const { persona, personaId } = usePersona();
  const [question, setQuestion] = useState("Why is live execution blocked or allowed right now?");
  const [personaQuestion, setPersonaQuestion] = useState("");
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const [lastPersonaQuestion, setLastPersonaQuestion] = useState<string | null>(null);

  const supervisor = useQuery({
    queryFn: () =>
      apiGet<TradingSupervisorResponse>(
        `/assets/${selectedAssetId}/agents/trading-supervisor/status?evidence_mode=${aiEvidenceMode}`,
      ),
    queryKey: ["ai-trading-supervisor", selectedAssetId, aiEvidenceMode],
  });

  const history = useQuery({
    queryFn: () =>
      apiGet<TradingSupervisorHistoryResponse>(
        `/assets/${selectedAssetId}/agents/trading-supervisor/history?limit=8`,
      ),
    queryKey: ["ai-trading-supervisor-history", selectedAssetId],
  });

  const personaAgent = useQuery({
    queryFn: () =>
      apiGet<PersonaAgentResponse>(
        `/assets/${selectedAssetId}/agents/persona/${personaId}/status?evidence_mode=${aiEvidenceMode}`,
      ),
    queryKey: ["persona-agent-status", selectedAssetId, personaId, aiEvidenceMode],
  });

  const askSupervisor = useMutation({
    mutationFn: (operatorQuestion: string) =>
      apiPost<TradingSupervisorResponse>(
        `/assets/${selectedAssetId}/agents/trading-supervisor/run`,
        {
          include_ai_brief: true,
          evidence_mode: aiEvidenceMode,
          question: operatorQuestion,
        },
      ),
    onSuccess: (_response, operatorQuestion) => {
      setLastQuestion(operatorQuestion);
      history.refetch();
    },
  });

  const safeAction = useMutation({
    mutationFn: (actionId: string) =>
      apiPost<ApiEnvelope>(
        `/assets/${selectedAssetId}/agents/trading-supervisor/actions/${actionId}`,
      ),
    onSuccess: () => {
      supervisor.refetch();
      history.refetch();
    },
  });

  const askPersonaAgent = useMutation({
    mutationFn: (operatorQuestion: string) =>
      apiPost<PersonaAgentResponse>(
        `/assets/${selectedAssetId}/agents/persona/${personaId}/run`,
        {
          include_ai_brief: true,
          evidence_mode: aiEvidenceMode,
          question: operatorQuestion,
        },
      ),
    onSuccess: (_response, operatorQuestion) => {
      setLastPersonaQuestion(operatorQuestion);
    },
  });

  const data = supervisor.data ?? askSupervisor.data;
  const answer = askSupervisor.data;
  const aiBrief = answer?.ai_brief;
  const exceptions = data?.exceptions ?? [];
  const context = data?.context ?? {};
  const automation = context.automation_control ?? {};
  const forecast = context.forecast_confidence ?? {};
  const signal = context.latest_signal ?? {};
  const evidence = context.evidence ?? {};
  const dailyBrief = data?.daily_brief ?? {};
  const suggestedQuestions = data?.suggested_questions ?? [];
  const safeActions = data?.safe_actions ?? [];
  const currentPersonaAnswer =
    askPersonaAgent.data?.persona_id === personaId ? askPersonaAgent.data : undefined;
  const personaData = currentPersonaAnswer ?? personaAgent.data;
  const personaSuggestedQuestions = personaData?.suggested_questions?.length
    ? personaData.suggested_questions
    : getFallbackQuestions(personaId);
  const personaBrief = currentPersonaAnswer?.ai_brief;
  const personaAgentName = personaData?.agent?.name ?? `${persona.label} Agent`;
  const personaDecisionType = personaData?.agent?.decision_type ?? "persona lens";
  const tone = statusTone(data?.supervisor_status, data?.highest_severity);
  const activePersonaQuestion =
    personaQuestion ||
    personaData?.agent?.primary_question ||
    getFallbackQuestion(personaId);

  const askQuestion = () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || askSupervisor.isPending) {
      return;
    }

    askSupervisor.mutate(trimmedQuestion);
  };

  const askPersonaQuestion = () => {
    const trimmedQuestion = activePersonaQuestion.trim();

    if (!trimmedQuestion || askPersonaAgent.isPending) {
      return;
    }

    askPersonaAgent.mutate(trimmedQuestion);
  };

  return (
    <>
      <PageHeading
        description={`Persona-aware AI intelligence for ${persona.label}: operational supervision plus the highest-value business question for this user lens.`}
        eyebrow="Automated trading"
        title="AI Intelligence Agents"
      />

      <SectionCard
        action={
          <div className="flex flex-wrap gap-2">
            <StatusPill tone={aiEvidenceMode === "mock" ? "emerald" : "blue"}>
              {aiEvidenceMode === "mock" ? "Mock data mode" : "Live data mode"}
            </StatusPill>
            <StatusPill tone={decisionTone(String(personaData?.decision?.status ?? ""))}>
              {personaDecisionType}
            </StatusPill>
          </div>
        }
        className="mb-6"
        title={personaAgentName}
      >
        <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Persona answer
            </div>
            <div className="mt-3 text-lg font-semibold leading-snug text-white">
              {personaData?.decision?.human_answer ?? `Ready to answer as ${persona.label}.`}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <StatusPill tone={decisionTone(String(personaData?.decision?.status ?? ""))}>
                {personaData?.decision?.score !== undefined ? `${String(personaData.decision.score)}/100` : "loading"}
              </StatusPill>
              <StatusPill tone="blue">
                {personaData?.decision?.score_label ?? personaData?.decision?.decision ?? "evidence loading"}
              </StatusPill>
            </div>
            <div className="mt-3 text-sm leading-6 text-slate-300">
              {personaData?.decision?.what_it_means ?? personaData?.decision?.summary ?? "Ask a business question and I will use the selected asset evidence as soon as it is loaded."}
            </div>
            <div className="mt-4 rounded-md border border-sky-400/20 bg-sky-400/10 p-3 text-sm leading-5 text-sky-100">
              {personaData?.decision?.next_action ?? personaData?.agent?.primary_question}
            </div>
            <div className="mt-4 rounded-md border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm leading-5 text-emerald-100">
              {personaData?.decision?.business_value ?? "The answer will include revenue, allocation, forecast, settlement, and readiness numbers where available."}
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <MiniList
                items={personaData?.decision?.recommended_actions ?? []}
                title="Recommended actions"
              />
              <MiniList
                items={placeholderRows(personaData?.decision?.placeholder_calculations)}
                title="Calculation note"
              />
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-4">
            <div className="mb-3 text-sm font-semibold text-slate-100">
              Ask as {persona.label}
            </div>
            <div className="mb-3 flex flex-wrap gap-2">
              {personaSuggestedQuestions.slice(0, 6).map((suggestedQuestion) => (
                <button
                  className="rounded-md border border-slate-700 bg-slate-950/80 px-2.5 py-1.5 text-left text-xs leading-5 text-slate-300 transition hover:border-sky-400/50 hover:text-sky-100"
                  key={suggestedQuestion}
                  onClick={() => setPersonaQuestion(suggestedQuestion)}
                  type="button"
                >
                  {suggestedQuestion}
                </button>
              ))}
            </div>
            <textarea
              className="min-h-24 w-full resize-y rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-400/60"
              onChange={(event) => setPersonaQuestion(event.target.value)}
              value={activePersonaQuestion}
            />
            <button
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md border border-emerald-400/35 bg-emerald-400/15 px-3 py-2 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-400/25 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={askPersonaAgent.isPending || !activePersonaQuestion.trim()}
              onClick={askPersonaQuestion}
              type="button"
            >
              {askPersonaAgent.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              {askPersonaAgent.isPending ? "Asking..." : `Ask ${personaAgentName}`}
            </button>
            <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/70 p-4 text-sm leading-6 text-slate-300">
              {lastPersonaQuestion && currentPersonaAnswer ? (
                <div className="mb-3 rounded-md border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs leading-5 text-slate-300">
                  {lastPersonaQuestion}
                </div>
              ) : null}
              <div className="whitespace-pre-wrap">
                {askPersonaAgent.isPending
                  ? "Asking the persona agent against selected asset evidence..."
                  : personaBrief?.brief ??
                    personaBrief?.message ??
                    "No persona-specific answer has been generated yet."}
              </div>
            </div>
          </div>
        </div>
      </SectionCard>

      <DecisionBrief
        blockers={exceptions
          .filter((exception) => exception.severity !== "info")
          .map((exception) => String(exception.message ?? exception.code ?? "Supervisor exception"))}
        className="mb-6"
        decision={
          <span className="inline-flex flex-wrap items-center gap-2">
            <StatusPill tone={tone}>{data?.supervisor_status ?? "pending"}</StatusPill>
            <span>{data?.decision ?? "Supervisor decision pending"}</span>
          </span>
        }
        evidence={[
          `Automation mode: ${String(automation.automation_mode ?? "-")}.`,
          `Forecast confidence: ${String(forecast.confidence_band ?? "-")} (${String(forecast.confidence_score ?? "-")}).`,
          `Latest signal: ${String(signal.signal ?? "-")} / ${String(signal.opportunity_level ?? "-")}.`,
          `Next action: ${String(data?.recommendation?.next_action ?? "-")}.`,
        ]}
        eyebrow="AI supervisor"
        nextAction={data?.recommendation?.summary ?? "Waiting for supervisor status."}
        title="Supervisor Decision"
        tone={tone}
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent={tone}
          helper={data?.recommendation?.next_action ?? "No next action returned"}
          label="Supervisor status"
          value={data?.supervisor_status ?? "-"}
        />
        <KpiCard
          accent={severityTone(data?.highest_severity)}
          helper="Material events only"
          label="Exceptions"
          value={data?.exception_count ?? 0}
        />
        <KpiCard
          accent={automation.live_trading_allowed ? "emerald" : "amber"}
          helper={String(automation.policy_decision ?? "No policy decision")}
          label="Live allowed"
          value={automation.live_trading_allowed ? "Yes" : "No"}
        />
        <KpiCard
          accent={confidenceTone(forecast.confidence_band)}
          helper={String(forecast.automation_eligibility ?? "No eligibility")}
          label="Forecast confidence"
          value={String(forecast.confidence_band ?? "-")}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.78fr)]">
        <div className="space-y-5">
          <SectionCard title="Daily Supervisor Brief">
            <DataTable
              columns={["field", "value"]}
              rows={Object.entries(dailyBrief).map(([field, value]) => ({
                field,
                value: formatEvidenceValue(value),
              }))}
            />
          </SectionCard>

          <SectionCard
            action={
              <button
                className="inline-flex items-center justify-center gap-2 rounded-md border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-xs font-semibold text-sky-100 transition hover:bg-sky-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={supervisor.isFetching}
                onClick={() => supervisor.refetch()}
                type="button"
              >
                {supervisor.isFetching ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="h-3.5 w-3.5" />
                )}
                Refresh
              </button>
            }
            title="Material Exceptions"
          >
            <DataTable
              columns={["severity", "source", "code", "message", "next_action"]}
              rows={exceptions}
            />
          </SectionCard>

          <SectionCard title="Supervisor Context">
            <DataTable
              columns={["signal", "automation_mode", "policy_decision", "connector_status", "orchestrator_status"]}
              rows={[
                {
                  automation_mode: automation.automation_mode,
                  connector_status: automation.connector_status,
                  orchestrator_status: (context.orchestrator ?? {}).orchestrator_status,
                  policy_decision: automation.policy_decision,
                  signal: signal.signal,
                },
              ]}
            />
          </SectionCard>

          <SectionCard title="Audit Evidence">
            <DataTable
              columns={["evidence", "value"]}
              rows={Object.entries(evidence).map(([key, value]) => ({
                evidence: key,
                value: formatEvidenceValue(value),
              }))}
            />
          </SectionCard>

          <SectionCard title="Recent Agent Runs">
            <DataTable
              columns={["recorded_at", "question", "decision", "top_exception_code", "next_action", "ai_brief_status"]}
              rows={history.data?.history ?? []}
            />
          </SectionCard>
        </div>

        <div className="space-y-5">
          <SectionCard
            action={
              <StatusPill tone={briefTone(aiBrief?.status)}>
                {askSupervisor.isPending ? "asking" : aiBrief?.status ?? "idle"}
              </StatusPill>
            }
            title="Ask Supervisor"
          >
            <div className="space-y-4">
              {suggestedQuestions.length ? (
                <div className="flex flex-wrap gap-2">
                  {suggestedQuestions.slice(0, 6).map((suggestedQuestion) => (
                    <button
                      className="rounded-md border border-slate-700 bg-slate-900/80 px-2.5 py-1.5 text-left text-xs leading-5 text-slate-300 transition hover:border-sky-400/50 hover:text-sky-100"
                      key={suggestedQuestion}
                      onClick={() => setQuestion(suggestedQuestion)}
                      type="button"
                    >
                      {suggestedQuestion}
                    </button>
                  ))}
                </div>
              ) : null}
              <textarea
                className="min-h-28 w-full resize-y rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-400/60"
                onChange={(event) => setQuestion(event.target.value)}
                value={question}
              />
              <button
                className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-emerald-400/35 bg-emerald-400/15 px-3 py-2 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-400/25 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={askSupervisor.isPending || !question.trim()}
                onClick={askQuestion}
                type="button"
              >
                {askSupervisor.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                {askSupervisor.isPending ? "Asking..." : "Ask AI Supervisor"}
              </button>
            </div>

            <div
              className={cn(
                "mt-5 rounded-lg border p-4 text-sm leading-6",
                aiBrief?.brief
                  ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-50"
                  : "border-slate-800 bg-slate-900/45 text-slate-400",
              )}
            >
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                <Bot className="h-4 w-4" />
                Supervisor answer
              </div>
              {lastQuestion ? (
                <div className="mb-3 rounded-md border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs leading-5 text-slate-300">
                  {lastQuestion}
                </div>
              ) : null}
              <div className="whitespace-pre-wrap">
                {askSupervisor.isPending
                  ? "Asking the supervisor against the latest automation evidence..."
                  : aiBrief?.brief ??
                    aiBrief?.message ??
                    "No AI brief has been generated for this asset yet."}
              </div>
            </div>
          </SectionCard>

          <SectionCard
            action={
              <StatusPill tone={safeAction.isPending ? "amber" : "slate"}>
                {safeAction.isPending ? "running" : "safe only"}
              </StatusPill>
            }
            title="Safe Agent Actions"
          >
            <div className="grid gap-3">
              {safeActions.map((action) => {
                const actionId = String(action.action_id ?? "");

                return (
                  <button
                    className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-3 text-left transition hover:border-emerald-400/40 hover:bg-emerald-400/10 disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={!actionId || safeAction.isPending}
                    key={actionId}
                    onClick={() => safeAction.mutate(actionId)}
                    type="button"
                  >
                    <span>
                      <span className="block text-sm font-semibold text-slate-100">
                        {String(action.label ?? actionId)}
                      </span>
                      <span className="mt-1 block text-xs leading-5 text-slate-400">
                        {String(action.description ?? "Run safe agent action.")}
                      </span>
                    </span>
                    {safeAction.isPending && safeAction.variables === actionId ? (
                      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-emerald-200" />
                    ) : (
                      <Play className="h-4 w-4 shrink-0 text-emerald-200" />
                    )}
                  </button>
                );
              })}
              {safeAction.data?.message ? (
                <div className="rounded-md border border-emerald-400/25 bg-emerald-400/10 px-3 py-2 text-xs leading-5 text-emerald-100">
                  {safeAction.data.message}
                </div>
              ) : null}
            </div>
          </SectionCard>

          <SectionCard title="Selected Asset">
            <DataTable
              columns={["field", "value"]}
              rows={[
                { field: "Asset", value: selectedAsset?.asset_name ?? selectedAsset?.site_name ?? selectedAssetId },
                { field: "Asset ID", value: selectedAssetId },
                { field: "Country", value: selectedAsset?.country },
                { field: "Market", value: selectedAsset?.market },
                { field: "Agent model", value: data?.agent?.llm_model },
              ]}
            />
          </SectionCard>
        </div>
      </div>
    </>
  );
}

function statusTone(status: string | undefined, severity: string | undefined): Tone {
  if (severity === "critical" || status === "exception") {
    return "red";
  }

  if (severity === "warning" || status === "review") {
    return "amber";
  }

  if (status === "normal") {
    return "emerald";
  }

  return "blue";
}

function severityTone(severity: string | undefined): Tone {
  if (severity === "critical") {
    return "red";
  }

  if (severity === "warning") {
    return "amber";
  }

  if (severity === "none") {
    return "emerald";
  }

  return "blue";
}

function confidenceTone(confidence: unknown): Tone {
  if (confidence === "high") {
    return "emerald";
  }

  if (confidence === "medium") {
    return "amber";
  }

  if (confidence === "low") {
    return "red";
  }

  return "slate";
}

function briefTone(status: string | undefined): Tone {
  if (status === "generated" || status === "fallback") {
    return "emerald";
  }

  if (status === "error" || status === "unavailable") {
    return "amber";
  }

  return "slate";
}

function MiniList({
  items,
  title,
}: {
  items: string[];
  title: string;
}) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950/70 p-3">
      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {title}
      </div>
      <div className="space-y-2">
        {items.length ? (
          items.slice(0, 3).map((item) => (
            <div className="text-xs leading-5 text-slate-300" key={item}>
              {item}
            </div>
          ))
        ) : (
          <div className="text-xs leading-5 text-slate-500">Waiting for evidence.</div>
        )}
      </div>
    </div>
  );
}

function placeholderRows(value: JsonObject | undefined) {
  if (!value) {
    return [];
  }

  return [
    `Method: ${String(value.method ?? "-")}`,
    `Future backend: ${String(value.future_backend_needed ?? "-")}`,
  ];
}

function decisionTone(status: string | undefined): Tone {
  if (status === "blocked") {
    return "red";
  }

  if (status === "review") {
    return "amber";
  }

  return "emerald";
}

function formatEvidenceValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return value;
  }

  return JSON.stringify(value);
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

function getFallbackQuestions(personaId: PersonaId) {
  const questions: Partial<Record<PersonaId, string[]>> = {
    asset_owner: [
      "How much value did the asset create this month?",
      "What revenue is modelled versus proven?",
      "Which product creates the most owner value?",
    ],
    investor_lender: [
      "Is this battery bankable or profitable this month?",
      "What downside evidence supports financing?",
      "What revenue is contracted, modelled, or simulated?",
    ],
    project_developer: [
      "Is this project ready for investment planning?",
      "Which assumption changes the project value most?",
      "What market evidence should I collect next?",
    ],
    executive: [
      "What is the commercial result this month?",
      "What should I escalate first?",
      "Where is the biggest value unlock?",
    ],
    client_success: [
      "Is this battery bankable or profitable this month?",
      "What numbers should I show in the client update?",
      "Which revenue products created the value?",
    ],
    trading_desk: [
      "Can I trade, paper trade, or wait?",
      "What PnL does the current signal create?",
      "Should bid sizing be reduced?",
    ],
    automation_operator: [
      "Can automation continue safely?",
      "Is simulated live operation clean right now?",
      "What control would block live mode?",
    ],
    risk_compliance: [
      "Can I defend this decision?",
      "What numbers support the approval?",
      "What should stay out of client claims?",
    ],
    market_operations: [
      "Which market route creates the most value?",
      "Which connector should I configure first?",
      "What can run in paper mode today?",
    ],
    forecast_quant: [
      "Can I trust the forecast for bidding?",
      "What forecast error affects revenue?",
      "Should bid sizing be reduced?",
    ],
    revenue_analyst: [
      "Which revenue product creates most value?",
      "How much revenue is allocated versus excluded?",
      "Where is revenue leaking?",
    ],
    all: [
      "Is this battery bankable or profitable this month?",
      "What is the commercial result this month?",
      "Which value unlock should we build next?",
    ],
  };

  return questions[personaId] ?? questions.all ?? [getFallbackQuestion(personaId)];
}
