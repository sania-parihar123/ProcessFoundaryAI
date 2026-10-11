from member2.schemas import MemberTwoOutput


def to_state_update(output: MemberTwoOutput) -> dict:
    # These names follow the team's ProcessFoundryState. Records are plain dicts because
    # the contracts are still provisional; mode="json" serializes Decimal confidence values
    # as strings so checkpoints can serialize them.
    return {
        "project_id": output.project_id,
        "source_document_ids": [output.document_id],
        "extracted_sections": [
            section.model_dump(mode="json") for section in output.sections
        ],
        "evidence_items": [
            evidence.model_dump(mode="json") for evidence in output.evidence
        ],
        "as_is_process": [step.model_dump(mode="json") for step in output.steps],
        "candidate_business_rules": [
            rule.model_dump(mode="json") for rule in output.rules
        ],
        "validation_errors": list(output.warnings),
    }
