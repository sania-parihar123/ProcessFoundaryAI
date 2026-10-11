"""Append-only workflow audit log with a hash chain (tamper-evident).

Each event stores the hash of the previous event. Changing or deleting an old event
breaks the chain and verify() reports it. Events are plain dicts (JSON-friendly) and
match a `trace_events` list.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

GENESIS = "0" * 64


def _hash(prev: str, body: Dict[str, Any]) -> str:
    return hashlib.sha256((prev + json.dumps(body, sort_keys=True, default=str)).encode()).hexdigest()


class AuditLog:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.events: List[Dict[str, Any]] = []

    def record(self, event_type: str, actor: str, subject: str = "", details: Optional[Dict[str, Any]] = None,
               timestamp: Optional[str] = None) -> Dict[str, Any]:
        if not event_type or not actor:
            raise ValueError("event_type and actor are required")
        body = {"event_id": f"{self.project_id}-EVT-{len(self.events) + 1:04d}", "event_type": event_type,
                "actor": actor, "subject": subject, "details": details or {},
                "timestamp": timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds")}
        prev = self.events[-1]["hash"] if self.events else GENESIS
        ev = {**body, "prev_hash": prev, "hash": _hash(prev, body)}
        self.events.append(ev)
        return ev

    def import_hitl(self, state_update: Dict[str, Any]) -> int:
        """Add events for questions, answers and decisions that are not logged yet (idempotent)."""
        logged = {(e["event_type"], e["subject"]) for e in self.events}
        n = 0
        for q in state_update.get("clarification_questions") or []:
            if ("question_asked", q["question_id"]) not in logged:
                self.record("question_asked", "system", q["question_id"], {"text": q.get("text", "")}, q.get("created_at")); n += 1
        for a in state_update.get("human_answers") or []:
            if ("answer_recorded", a["answer_id"]) not in logged:
                self.record("answer_recorded", a.get("answered_by", "?"), a["answer_id"],
                            {"question_id": a.get("question_id"), "role": a.get("role"), "superseded": a.get("superseded", False)},
                            a.get("answered_at")); n += 1
        for d in state_update.get("decisions") or []:
            if ("decision_recorded", d["decision_id"]) not in logged:
                self.record("decision_recorded", d.get("decided_by", "?"), d["decision_id"],
                            {"decision": d.get("decision"), "role": d.get("role"), "reason": d.get("reason", "")},
                            d.get("decided_at")); n += 1
        return n

    def verify(self) -> Dict[str, Any]:
        prev = GENESIS
        for i, e in enumerate(self.events):
            body = {k: v for k, v in e.items() if k not in ("prev_hash", "hash")}
            if e["prev_hash"] != prev or e["hash"] != _hash(prev, body):
                return {"ok": False, "broken_at": i, "event_id": e.get("event_id")}
            prev = e["hash"]
        return {"ok": True, "events": len(self.events)}

    def save(self, path) -> None:
        Path(path).write_text(json.dumps({"project_id": self.project_id, "events": self.events}, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path) -> "AuditLog":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        log = cls(data["project_id"])
        log.events = data["events"]
        return log
