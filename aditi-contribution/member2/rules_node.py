from __future__ import annotations

import re

from pydantic import BaseModel

from member2.llm_helper import call_llm
from member2.prompts import RULES_SYSTEM_PROMPT, build_evidence_line, build_rules_user_prompt
from member2.schemas import EvidenceRecord, RuleRecord

CLAIM_TYPE_LABELS = {"step", "rule", "actor", "deadline", "form", "other"}
NULL_FIELD_VALUES = {"null", "none", "n/a", "unknown"}


class RawRule(BaseModel):
    statement: str
    condition: str | None
    action: str | None
    scope: str | None
    effective_context: str | None
    evidence_ids: list[str]


class RawRuleList(BaseModel):
    rules: list[RawRule]


def _clean_optional_field(
    value: str | None,
    statement: str,
    evidence_ids: set[str],
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    normalized_value = " ".join(cleaned.split()).casefold()
    normalized_statement = " ".join(statement.split()).casefold()
    if normalized_value in NULL_FIELD_VALUES | CLAIM_TYPE_LABELS:
        return None
    if normalized_value == normalized_statement:
        return None
    if _is_evidence_id(cleaned, evidence_ids):
        return None
    return cleaned


def _is_evidence_id(value: str, evidence_ids: set[str]) -> bool:
    return value in evidence_ids or re.search(r"-EVD-\d+$", value) is not None


def _normalize_for_containment(value: str) -> str:
    return "".join(value.split()).casefold()


def extract_rules(
    evidence: list[EvidenceRecord],
    project_id: str,
) -> list[RuleRecord]:
    evidence_by_section: dict[str, list[EvidenceRecord]] = {}
    for item in evidence:
        # Steps belong to the As-Is node; this keeps process steps out of the rules list.
        if item.claim_type not in {"rule", "deadline", "form", "other"}:
            continue
        evidence_by_section.setdefault(item.document_section_id, []).append(item)

    rules: list[RuleRecord] = []

    # Smaller requests help small models avoid stopping early; cross-section conflicts remain
    # separate rules for gap analysis rather than being reconciled here.
    for section_id, section_evidence in evidence_by_section.items():
        evidence_lines = [
            build_evidence_line(item.id, item.claim_type, item.quote)
            for item in section_evidence
        ]
        raw_rule_list = call_llm(
            system_prompt=RULES_SYSTEM_PROMPT,
            user_prompt=build_rules_user_prompt(evidence_lines),
            response_model=RawRuleList,
            source_wrapped=True,
        )
        if raw_rule_list is None:
            print(f"Warning: rule extraction failed for section {section_id}; continuing.")
            continue

        evidence_by_id = {item.id: item for item in section_evidence}
        valid_evidence_ids = set(evidence_by_id)
        for raw_rule in raw_rule_list.rules:
            rule_evidence_ids: list[str] = []
            for evidence_id in raw_rule.evidence_ids:
                if evidence_id not in valid_evidence_ids:
                    print(
                        f"Warning: removed unknown evidence ID {evidence_id!r} "
                        f"from rule {raw_rule.statement!r} in section {section_id}."
                    )
                    continue
                rule_evidence_ids.append(evidence_id)

            if not rule_evidence_ids:
                print(
                    f"Rejected rule {raw_rule.statement!r} from section {section_id}: "
                    "it has no valid supporting evidence IDs."
                )
                continue

            rule_id = f"{project_id}-BR-{len(rules) + 1:03d}"
            statement = raw_rule.statement
            condition = _clean_optional_field(
                raw_rule.condition,
                raw_rule.statement,
                valid_evidence_ids,
            )
            action = _clean_optional_field(
                raw_rule.action,
                raw_rule.statement,
                valid_evidence_ids,
            )
            scope = _clean_optional_field(
                raw_rule.scope,
                raw_rule.statement,
                valid_evidence_ids,
            )
            effective_context = _clean_optional_field(
                raw_rule.effective_context,
                raw_rule.statement,
                valid_evidence_ids,
            )

            if len(rule_evidence_ids) == 1:
                # Small models sometimes split a sentence across statement and condition or
                # alter its wording; a rule statement must always be the exact source sentence.
                statement = evidence_by_id[rule_evidence_ids[0]].quote.strip()

            normalized_statement = _normalize_for_containment(statement)
            if condition is not None and _normalize_for_containment(condition) in normalized_statement:
                condition = None
            if action is not None and _normalize_for_containment(action) in normalized_statement:
                action = None

            rules.append(
                RuleRecord(
                    rule_id=rule_id,
                    statement=statement,
                    condition=condition,
                    action=action,
                    scope=scope,
                    effective_context=effective_context,
                    evidence_ids=rule_evidence_ids,
                    status="needs_review",
                )
            )

    return rules
