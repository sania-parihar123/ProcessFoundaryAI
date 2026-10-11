from __future__ import annotations

import re
from pydantic import BaseModel

from member2.llm_helper import call_llm
from member2.prompts import AS_IS_SYSTEM_PROMPT, build_as_is_user_prompt, build_evidence_line
from member2.schemas import DiscoveredStep, EvidenceRecord, StepLink


class RawStep(BaseModel):
    name: str
    actor: str | None
    inputs: list[str]
    outputs: list[str]
    evidence_ids: list[str]


class RawStepList(BaseModel):
    steps: list[RawStep]


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold()


def _is_evidence_id(value: str, evidence_ids: set[str]) -> bool:
    return value in evidence_ids or re.search(r"-EVD-\d+$", value) is not None


def build_as_is(
    evidence: list[EvidenceRecord],
    project_id: str,
) -> list[DiscoveredStep]:
    if not evidence:
        print("Warning: no evidence was supplied; no process steps can be built.")
        return []

    evidence_lines = [
        build_evidence_line(item.id, item.claim_type, item.quote)
        for item in evidence
    ]
    raw_steps = call_llm(
        system_prompt=AS_IS_SYSTEM_PROMPT,
        user_prompt=build_as_is_user_prompt(evidence_lines),
        response_model=RawStepList,
        source_wrapped=True,
    )
    if raw_steps is None:
        print("Warning: As-Is step extraction failed; returning no steps.")
        return []

    evidence_by_id = {item.id: item for item in evidence}
    known_evidence_ids = set(evidence_by_id)
    validated_steps: list[tuple[RawStep, list[str]]] = []

    for raw_step in raw_steps.steps:
        valid_evidence_ids: list[str] = []
        for evidence_id in raw_step.evidence_ids:
            if evidence_id not in evidence_by_id:
                print(f"Warning: removed unknown evidence ID {evidence_id!r} from step {raw_step.name!r}.")
                continue
            valid_evidence_ids.append(evidence_id)

        if not valid_evidence_ids:
            print(f"Rejected step {raw_step.name!r}: it has no valid supporting evidence IDs.")
            continue

        actor = raw_step.actor
        if actor is not None:
            actor = re.sub(r"^the ", "", actor, count=1, flags=re.IGNORECASE)
            actor_text = _normalize_for_match(actor)
            cited_quotes = [evidence_by_id[evidence_id].quote for evidence_id in valid_evidence_ids]
            if not any(actor_text in _normalize_for_match(quote) for quote in cited_quotes):
                print(f"Warning: removed unsupported actor {actor!r} from step {raw_step.name!r}.")
                actor = None

        # Inputs and outputs are things the step consumes or produces, such as forms or
        # documents; evidence IDs belong only in evidence_ids.
        inputs = [
            value for value in raw_step.inputs
            if not _is_evidence_id(value, known_evidence_ids)
        ]
        outputs = [
            value for value in raw_step.outputs
            if not _is_evidence_id(value, known_evidence_ids)
        ]

        validated_steps.append(
            (
                RawStep(
                    name=raw_step.name,
                    actor=actor,
                    inputs=inputs,
                    outputs=outputs,
                    evidence_ids=valid_evidence_ids,
                ),
                valid_evidence_ids,
            )
        )

    discovered_steps: list[DiscoveredStep] = []
    for index, (raw_step, valid_evidence_ids) in enumerate(validated_steps, start=1):
        step_id = f"{project_id}-STEP-{index:03d}"
        # Branches (for example a returned application) are not modelled yet.
        next_steps = (
            [StepLink(to_step_id=f"{project_id}-STEP-{index + 1:03d}")]
            if index < len(validated_steps)
            else []
        )
        discovered_steps.append(
            DiscoveredStep(
                step_id=step_id,
                name=raw_step.name,
                actor=raw_step.actor,
                inputs=raw_step.inputs,
                outputs=raw_step.outputs,
                next_steps=next_steps,
                evidence_ids=valid_evidence_ids,
                unknowns=["actor not stated in source"] if raw_step.actor is None else [],
            )
        )

    return discovered_steps
