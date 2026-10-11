"""The HITL store: keeps questions, answers and human decisions, and enforces the rules.

Rules enforced here:
  * Same problem asked twice -> only one question (idempotent add).
  * An answer needs a real name and a role. Empty text is refused.
  * Re-answering keeps the old answer (marked superseded); nothing is deleted.
  * Questions whose source changed can be marked stale and must be answered again.
  * Only an allowed role may decide; "approve" is refused while questions are open.
  * Nothing here ever approves automatically.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import ClarificationQuestion, HumanAnswer, HumanDecision
from .question_builder import build_questions

DEFAULT_APPROVER_ROLES = ("approver", "process_owner", "admin")


class HitlError(ValueError):
    """Raised when a human action breaks a rule."""


class ClarificationStore:
    def __init__(self, project_id: str, approver_roles=DEFAULT_APPROVER_ROLES):
        self.project_id = project_id
        self.approver_roles = tuple(approver_roles)
        self.questions: Dict[str, ClarificationQuestion] = {}
        self.answers: List[HumanAnswer] = []
        self.decisions: List[HumanDecision] = []

    # ---------- questions ----------
    def add_questions(self, new: List[ClarificationQuestion]) -> List[ClarificationQuestion]:
        """Add questions; skips ones already known (same fingerprint). Returns the ones actually added."""
        known = {q.fingerprint: q for q in self.questions.values()}
        added = []
        for q in new:
            if q.fingerprint in known:
                old = known[q.fingerprint]
                if old.status == "stale":          # same problem came back -> ask again
                    old.status = "open"
                continue
            q = q.model_copy(update={
                "question_id": f"{self.project_id}-Q-{len(self.questions) + 1:03d}",
                "project_id": self.project_id})
            self.questions[q.question_id] = q
            known[q.fingerprint] = q
            added.append(q)
        return added

    def load_from_state(self, update: Dict[str, Any]) -> List[ClarificationQuestion]:
        return self.add_questions(build_questions(update))

    def mark_stale(self, question_ids: List[str]) -> None:
        for qid in question_ids:
            self._q(qid).status = "stale"

    def _q(self, qid: str) -> ClarificationQuestion:
        if qid not in self.questions:
            raise HitlError(f"Unknown question: {qid}")
        return self.questions[qid]

    def pending_question_ids(self) -> List[str]:
        return [q.question_id for q in self.questions.values() if q.status in ("open", "stale")]

    # ---------- answers ----------
    def record_answer(self, question_id: str, answer_text: str, answered_by: str, role: str) -> HumanAnswer:
        q = self._q(question_id)
        if not answer_text or not answer_text.strip():
            raise HitlError("Answer cannot be empty.")
        if not answered_by or not answered_by.strip() or not role or not role.strip():
            raise HitlError("Every answer must say who answered and in what role.")
        answer_text = answer_text.strip()
        current = self.current_answer(question_id)
        if current and current.answer_text == answer_text and q.status == "answered":
            return current                          # same answer sent twice -> no duplicate
        if q.options and answer_text not in q.options and not answer_text.lower().startswith("other"):
            raise HitlError(f"Answer must be one of {q.options} (or start with 'Other').")
        if current:
            current.superseded = True
        a = HumanAnswer(answer_id=f"{self.project_id}-ANS-{len(self.answers) + 1:03d}",
                        question_id=question_id, answer_text=answer_text,
                        answered_by=answered_by.strip(), role=role.strip())
        self.answers.append(a)
        q.status = "answered"
        return a

    def current_answer(self, question_id: str) -> Optional[HumanAnswer]:
        for a in reversed(self.answers):
            if a.question_id == question_id and not a.superseded:
                return a
        return None

    # ---------- decisions ----------
    def record_decision(self, subject: str, decision: str, decided_by: str, role: str, reason: str = "") -> HumanDecision:
        if role not in self.approver_roles:
            raise HitlError(f"Role '{role}' is not allowed to decide. Allowed: {list(self.approver_roles)}")
        if not decided_by or not decided_by.strip():
            raise HitlError("A decision must say who made it.")
        if decision in ("reject", "request_changes") and not reason.strip():
            raise HitlError("A reason is required when rejecting or requesting changes.")
        if decision == "approve" and self.pending_question_ids():
            raise HitlError("Cannot approve while questions are still open: " + ", ".join(self.pending_question_ids()))
        d = HumanDecision(decision_id=f"{self.project_id}-DEC-{len(self.decisions) + 1:03d}",
                          subject=subject, decision=decision, decided_by=decided_by.strip(),
                          role=role, reason=reason.strip())
        self.decisions.append(d)
        return d

    def approval_status(self) -> str:
        """pending / approved / rejected - derived ONLY from the latest human decision."""
        if not self.decisions or self.pending_question_ids():
            return "pending"          # open/stale questions always cancel an earlier approval
        last = self.decisions[-1].decision
        return {"approve": "approved", "reject": "rejected"}.get(last, "pending")

    # ---------- resume contract ----------
    def is_ready_to_resume(self) -> bool:
        return not self.pending_question_ids()

    def to_state_update(self) -> Dict[str, Any]:
        """Keys match Sania's ProcessFoundryState field names. Records are plain dicts."""
        pending = self.pending_question_ids()
        return {
            "clarification_questions": [q.model_dump() for q in self.questions.values()],
            "human_answers": [a.model_dump() for a in self.answers],
            "decisions": [d.model_dump() for d in self.decisions],
            "pending_question_ids": pending,
            "approval_status": self.approval_status(),
            "lifecycle_status": "paused_for_human" if pending else "running",
        }

    # ---------- save / load ----------
    def save(self, path) -> None:
        data = {"project_id": self.project_id, "approver_roles": list(self.approver_roles),
                "questions": [q.model_dump() for q in self.questions.values()],
                "answers": [a.model_dump() for a in self.answers],
                "decisions": [d.model_dump() for d in self.decisions]}
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path) -> "ClarificationStore":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        s = cls(data["project_id"], data.get("approver_roles", DEFAULT_APPROVER_ROLES))
        s.questions = {q["question_id"]: ClarificationQuestion(**q) for q in data["questions"]}
        s.answers = [HumanAnswer(**a) for a in data["answers"]]
        s.decisions = [HumanDecision(**d) for d in data["decisions"]]
        return s
