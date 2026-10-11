from pathlib import Path

from member2.as_is_node import build_as_is
from member2.doc_parser import parse_document
from member2.evidence_node import extract_evidence


if __name__ == "__main__":
    sample_path = Path(__file__).resolve().parent / "samples" / "sample_scholarship.txt"
    sections = parse_document(sample_path, document_id="DOC-DEMO")
    evidence = []
    evidence_counter = 1

    for section in sections:
        section_evidence = extract_evidence(
            section,
            project_id="demo-project",
            counter_start=evidence_counter,
        )
        evidence.extend(section_evidence)
        evidence_counter += len(section_evidence)

    steps = build_as_is(evidence, project_id="demo-project")
    for step in steps:
        print(f"{step.step_id} | {step.actor} | {step.name} | {step.evidence_ids}")
