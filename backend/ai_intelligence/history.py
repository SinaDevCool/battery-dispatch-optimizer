import json
from datetime import datetime

from backend.config.paths import OUTPUT_DATA_DIR


AI_HISTORY_DIR = OUTPUT_DATA_DIR / "ai_intelligence"
TRADING_SUPERVISOR_HISTORY_FILE = AI_HISTORY_DIR / "trading_supervisor_history.jsonl"


def append_trading_supervisor_history(run):
    AI_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    record = build_history_record(run)

    with open(TRADING_SUPERVISOR_HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, default=str) + "\n")

    return record


def list_trading_supervisor_history(asset_id, limit=20):
    if not TRADING_SUPERVISOR_HISTORY_FILE.exists():
        return {
            "status": "ok",
            "asset_id": asset_id,
            "history": [],
            "history_count": 0,
        }

    records = []
    with open(TRADING_SUPERVISOR_HISTORY_FILE, "r", encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("asset_id") == asset_id:
                records.append(record)

    records = records[-limit:]
    records.reverse()

    return {
        "status": "ok",
        "asset_id": asset_id,
        "history": records,
        "history_count": len(records),
    }


def build_history_record(run):
    exceptions = run.get("exceptions") or []
    ai_brief = run.get("ai_brief") or {}
    recommendation = run.get("recommendation") or {}
    top_exception = exceptions[0] if exceptions else {}

    return {
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "generated_at": run.get("generated_at"),
        "asset_id": run.get("asset_id"),
        "agent_id": (run.get("agent") or {}).get("agent_id"),
        "question": run.get("operator_question"),
        "decision": run.get("decision"),
        "supervisor_status": run.get("supervisor_status"),
        "highest_severity": run.get("highest_severity"),
        "exception_count": run.get("exception_count"),
        "top_exception_code": top_exception.get("code"),
        "top_exception_message": top_exception.get("message"),
        "next_action": recommendation.get("next_action"),
        "ai_brief_status": ai_brief.get("status"),
        "answer": ai_brief.get("brief") or ai_brief.get("message"),
    }

