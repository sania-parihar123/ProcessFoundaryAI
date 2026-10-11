from pathlib import Path

from member2.doc_parser import parse_document
from member2.evidence_node import extract_evidence


if __name__ == "__main__":
    sample_path = Path(__file__).resolve().parent / "samples" / "sample_scholarship.txt"
    sections = parse_document(sample_path, document_id="DOC-DEMO")
    counter = 1

    for section in sections:
        records = extract_evidence(section, project_id="demo-project", counter_start=counter)
        for record in records:
            print(
                f"{record.id} | {record.claim_type} | {record.confidence} | "
                f"{section['section_title']} | {record.quote}"
            )
        counter += len(records)
