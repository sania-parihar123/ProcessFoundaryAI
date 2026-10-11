import json
from pathlib import Path

from requirements_artifacts.requirements_builder import build_requirements


def main() -> None:
    artifacts_dir = Path(__file__).resolve().parent
    state_update_path = artifacts_dir / "samples" / "demo_state_update.json"
    state_update = json.loads(state_update_path.read_text(encoding="utf-8"))

    print(f"Input file: {state_update_path}")
    print(f"Extracted sections: {len(state_update['extracted_sections'])}")
    print(f"Evidence items: {len(state_update['evidence_items'])}")
    print(f"As-Is process steps: {len(state_update['as_is_process'])}")
    print(f"Candidate business rules: {len(state_update['candidate_business_rules'])}")
    if not state_update["as_is_process"] and not state_update["candidate_business_rules"]:
        raise SystemExit("input has no steps or rules")

    output = build_requirements(state_update)

    for requirement in output.requirements:
        print(
            f"{requirement.id} | {requirement.req_type} | "
            f"{requirement.status} | {requirement.statement}"
        )
    print(
        "Functional requirements: "
        f"{sum(req.req_type == 'functional' for req in output.requirements)}"
    )
    print(
        "Workflow requirements: "
        f"{sum(req.req_type == 'workflow' for req in output.requirements)}"
    )
    print(f"Open questions: {len(output.open_questions)}")
    for question in output.open_questions:
        print(
            f"Open question: {question.id} | {question.question} | "
            f"{question.reason}"
        )

    output_dir = artifacts_dir / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "demo_requirements.json"
    output_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
