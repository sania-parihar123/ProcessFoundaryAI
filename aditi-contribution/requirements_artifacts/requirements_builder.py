from requirements_artifacts.artifact_schemas import (
    OpenQuestion,
    Requirement,
    RequirementsOutput,
)


def build_requirements(state_update: dict) -> RequirementsOutput:
    project_id = state_update["project_id"]
    evidence_ids = {item["id"] for item in state_update["evidence_items"]}
    requirements: list[Requirement] = []
    open_questions: list[OpenQuestion] = []
    warnings: list[str] = []

    def valid_evidence_ids(record_evidence_ids: list[str], record_id: str) -> list[str]:
        valid_ids: list[str] = []
        for evidence_id in record_evidence_ids:
            if evidence_id in evidence_ids:
                valid_ids.append(evidence_id)
            else:
                warnings.append(
                    f"Unknown evidence ID {evidence_id!r} was dropped from {record_id!r}."
                )
        return valid_ids

    def add_requirement(
        *,
        req_type: str,
        title: str,
        statement: str,
        priority: str,
        rule_ids: list[str],
        step_ids: list[str],
        source_evidence_ids: list[str],
        needs_clarification: bool = False,
    ) -> None:
        requirement_id = f"{project_id}-REQ-{len(requirements) + 1:03d}"
        validated_evidence_ids = valid_evidence_ids(
            source_evidence_ids,
            requirement_id,
        )
        status = (
            "needs_clarification"
            if needs_clarification or not validated_evidence_ids
            else "draft"
        )
        requirements.append(
            Requirement(
                id=requirement_id,
                project_id=project_id,
                req_type=req_type,
                title=title,
                statement=statement,
                priority=priority,
                rule_ids=rule_ids,
                step_ids=step_ids,
                evidence_ids=validated_evidence_ids,
                status=status,
            )
        )

    for rule in state_update["candidate_business_rules"]:
        statement = rule["statement"]
        add_requirement(
            req_type="functional",
            title=" ".join(statement.split()[:8]),
            statement=f"The system shall enforce: {statement}",
            priority="Must",
            rule_ids=[rule["rule_id"]],
            step_ids=[],
            source_evidence_ids=rule["evidence_ids"],
        )

    for step in state_update["as_is_process"]:
        name = step["name"]
        actor = step.get("actor")
        statement = f"The process shall include the step: {name}"
        if actor is not None:
            statement += f" performed by {actor}"

        unknowns = step.get("unknowns", [])
        step_id = step["step_id"]
        add_requirement(
            req_type="workflow",
            title=name,
            statement=statement,
            priority="Should",
            rule_ids=[],
            step_ids=[step_id],
            source_evidence_ids=step["evidence_ids"],
            needs_clarification=bool(unknowns),
        )
        if unknowns:
            open_questions.append(
                OpenQuestion(
                    id=f"{project_id}-Q-{len(open_questions) + 1:03d}",
                    project_id=project_id,
                    question=f"Who performs this step: {name}?",
                    reason="; ".join(unknowns),
                    related_ids=[step_id],
                )
            )

    return RequirementsOutput(
        project_id=project_id,
        requirements=requirements,
        open_questions=open_questions,
        warnings=warnings,
    )
