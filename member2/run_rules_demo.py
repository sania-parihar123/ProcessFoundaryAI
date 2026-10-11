from pathlib import Path

from member2.doc_parser import parse_document
from member2.evidence_node import extract_evidence
from member2.rules_node import extract_rules


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

    rules = extract_rules(evidence, project_id="demo-project")
    for rule in rules:
        print(
            f"{rule.rule_id} | {rule.statement} | {rule.condition} | "
            f"{rule.action} | {rule.evidence_ids}"
        )
