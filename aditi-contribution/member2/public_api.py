"""These are the functions the graph calls; this module imports nothing from Member 1's or Member 3's code."""

from __future__ import annotations

from member2 import as_is_node, evidence_node, rules_node
from member2.schemas import DiscoveredStep, EvidenceRecord, RuleRecord


def extract_evidence(document_sections: list[dict], project_id: str) -> list[EvidenceRecord]:
    evidence_items: list[EvidenceRecord] = []
    counter = 1
    for section in document_sections:
        section_evidence = evidence_node.extract_evidence(
            section,
            project_id=project_id,
            counter_start=counter,
        )
        evidence_items.extend(section_evidence)
        counter += len(section_evidence)
    return evidence_items


def build_as_is(evidence_items: list[EvidenceRecord], project_id: str) -> list[DiscoveredStep]:
    return as_is_node.build_as_is(evidence_items, project_id)


def extract_business_rules(
    evidence_items: list[EvidenceRecord],
    as_is_process: list[DiscoveredStep] | None,
    project_id: str,
) -> list[RuleRecord]:
    # as_is_process is accepted to match the spec signature, but it is currently unused.
    return rules_node.extract_rules(evidence_items, project_id)
