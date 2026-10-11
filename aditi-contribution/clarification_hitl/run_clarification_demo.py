"""Demo: build questions, answer them as a human, then approve. Run from the folder above this one:
    python -m clarification_hitl.run_clarification_demo
"""
import json
from pathlib import Path

from .store import ClarificationStore, HitlError

SAMPLE = Path(__file__).parent / "samples" / "demo_state_update.json"


def main() -> None:
    update = json.loads(SAMPLE.read_text(encoding="utf-8"))
    store = ClarificationStore(update["project_id"])
    store.load_from_state(update)
    print(f"Input file: {SAMPLE}")
    print(f"Questions created: {len(store.questions)}")
    for q in store.questions.values():
        print(f"  {q.question_id} | {q.kind} | {q.text}")
    print("Ready to resume?", store.is_ready_to_resume(), "| status:", store.approval_status())

    try:
        store.record_decision("requirements", "approve", "Dr. Rao", "approver")
    except HitlError as e:
        print("Blocked (good):", e)

    for q in list(store.questions.values()):
        if q.kind == "conflicting_rules":
            store.record_answer(q.question_id, q.options[0], "Dr. Rao", "process_owner")
        elif q.kind == "missing_actor":
            store.record_answer(q.question_id, "Scholarship clerk", "Dr. Rao", "process_owner")
        else:
            store.record_answer(q.question_id, "Defined by the scholarship committee", "Dr. Rao", "process_owner")
    print("Ready to resume?", store.is_ready_to_resume())

    store.record_decision("requirements", "approve", "Dr. Rao", "approver", "Reviewed")
    out = store.to_state_update()
    print("approval_status:", out["approval_status"], "| lifecycle:", out["lifecycle_status"])
    print("answers:", len(out["human_answers"]), "| decisions:", len(out["decisions"]))
    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(exist_ok=True)
    store.save(out_dir / "hitl_store.json")
    (out_dir / "hitl_state_update.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Saved to", out_dir)


if __name__ == "__main__":
    main()
