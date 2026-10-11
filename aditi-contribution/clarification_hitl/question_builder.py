"""Turns a state update (the dict from the AI layer) into clarification questions.

Plain Python, no LLM. Reads: project_id, as_is_process, candidate_business_rules.
Field names are read tolerantly (several spellings) because the shared schema is
still being agreed; unknown fields are ignored.
"""
import hashlib
import re
from typing import Any, Dict, List

from .schemas import ClarificationQuestion

VAGUE_TERMS = ["eligible", "appropriate", "as soon as possible", "reasonable", "etc", "suitable", "relevant", "promptly"]
MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december"
DATE_RE = re.compile(r"\b(\d{1,2}\s+(?:%s)|(?:%s)\s+\d{1,2})\b" % (MONTHS, MONTHS), re.I)
DEADLINE_WORDS = ("deadline", "last date", "before", "no later than", "by ")


def _get(d: Dict[str, Any], *names, default=None):
    for n in names:
        if d.get(n) not in (None, "", []):
            return d[n]
    return default


def _fp(*parts: str) -> str:
    return hashlib.sha1("|".join(p.lower().strip() for p in parts).encode()).hexdigest()[:12]


def _steps(update: Dict[str, Any]) -> List[Dict[str, Any]]:
    ap = update.get("as_is_process") or {}
    return ap.get("steps", []) if isinstance(ap, dict) else []


def _rules(update: Dict[str, Any]) -> List[Dict[str, Any]]:
    return update.get("candidate_business_rules") or []


def _rule_text(r: Dict[str, Any]) -> str:
    return str(_get(r, "statement", "description", "rule_text", default=""))


def build_questions(update: Dict[str, Any]) -> List[ClarificationQuestion]:
    """Return questions in a stable order. IDs are assigned by store.add_questions()."""
    project = update.get("project_id") or "project"
    out: List[ClarificationQuestion] = []

    # 1) steps with no actor
    for s in _steps(update):
        sid = str(_get(s, "step_id", "id", default=""))
        name = str(_get(s, "name", "title", default=sid))
        if not _get(s, "actor"):
            out.append(ClarificationQuestion(
                question_id="", project_id=project, kind="missing_actor",
                text=f"Who performs this step: {name}?",
                reason="Actor not stated in the source documents.",
                fingerprint=_fp("actor", sid, name), step_ids=[sid] if sid else [],
                evidence_ids=list(_get(s, "evidence_ids", default=[]))))

    # 2) conflicting deadline-style rules (different dates for the same kind of deadline)
    dated = []
    for r in _rules(update):
        t = _rule_text(r)
        m = DATE_RE.findall(t)
        if m and any(w in t.lower() for w in DEADLINE_WORDS):
            dated.append((r, m[0].lower()))
    dates = {d for _, d in dated}
    if len(dates) > 1:
        ids = [str(_get(r, "rule_id", "id", default="")) for r, _ in dated]
        ev = sorted({e for r, _ in dated for e in _get(r, "evidence_ids", default=[])})
        out.append(ClarificationQuestion(
            question_id="", project_id=project, kind="conflicting_rules",
            text="The documents give different dates (" + " vs ".join(sorted(d.title() for d in dates)) + "). Which one is correct?",
            reason="Conflicting statements are kept separate; a human must choose.",
            fingerprint=_fp("conflict", *sorted(dates)), rule_ids=[i for i in ids if i],
            evidence_ids=ev, options=sorted(d.title() for d in dates) + ["Neither / other"]))

    # 3) explicit conflicts flagged by the AI layer
    for r in _rules(update):
        if str(r.get("status", "")).lower() in ("conflict", "conflicting") or r.get("conflicts_with"):
            rid = str(_get(r, "rule_id", "id", default=""))
            out.append(ClarificationQuestion(
                question_id="", project_id=project, kind="conflicting_rules",
                text=f"Rule {rid} conflicts with another rule. Which one applies?",
                reason="Flagged as conflicting.", fingerprint=_fp("flagged", rid),
                rule_ids=[rid] + list(r.get("conflicts_with") or []),
                evidence_ids=list(_get(r, "evidence_ids", default=[]))))

    # 4) vague wording in rules
    for r in _rules(update):
        t = _rule_text(r)
        hit = next((v for v in VAGUE_TERMS if re.search(r"\b%s\b" % re.escape(v), t, re.I)), None)
        if hit:
            rid = str(_get(r, "rule_id", "id", default=""))
            out.append(ClarificationQuestion(
                question_id="", project_id=project, kind="ambiguous_term",
                text=f'The term "{hit}" is not defined. What exactly does it mean here?',
                reason=f'Rule text: "{t}"', fingerprint=_fp("vague", hit, t),
                rule_ids=[rid] if rid else [], evidence_ids=list(_get(r, "evidence_ids", default=[]))))

    # 5) other unknowns listed by the AI layer on steps
    for s in _steps(update):
        for u in s.get("unknowns") or []:
            if "actor" in str(u).lower():
                continue   # already covered by question type 1
            sid = str(_get(s, "step_id", "id", default=""))
            out.append(ClarificationQuestion(
                question_id="", project_id=project, kind="missing_info",
                text=f"Missing information for step {_get(s, 'name', default=sid)}: {u}",
                reason="Listed as unknown by the discovery step.", fingerprint=_fp("unk", sid, str(u)),
                step_ids=[sid] if sid else []))
    return out
