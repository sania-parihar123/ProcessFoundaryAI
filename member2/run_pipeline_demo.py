import json
from pathlib import Path

from member2.pipeline import run_member2_pipeline
from member2.state_adapter import to_state_update


if __name__ == "__main__":
    member2_dir = Path(__file__).resolve().parent
    sample_path = member2_dir / "samples" / "sample_scholarship.txt"
    output = run_member2_pipeline(
        str(sample_path),
        project_id="demo-project",
        document_id="DOC-DEMO",
    )

    print(f"sections: {len(output.sections)}")
    print(f"evidence: {len(output.evidence)}")
    print(f"steps: {len(output.steps)}")
    print(f"rules: {len(output.rules)}")
    for warning in output.warnings:
        print(f"Warning: {warning}")

    output_path = member2_dir / "out" / "demo_output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    print(f"Output written to {output_path}")

    state_update_path = member2_dir / "out" / "demo_state_update.json"
    state_update_path.write_text(
        json.dumps(to_state_update(output), indent=2),
        encoding="utf-8",
    )
    print(f"State update written to {state_update_path}")
