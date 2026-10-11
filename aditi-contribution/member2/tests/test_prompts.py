import re

from member2 import prompts


def test_system_prompt_constants_are_non_empty_and_generic():
    constants = (
        prompts.EVIDENCE_SYSTEM_PROMPT,
        prompts.AS_IS_SYSTEM_PROMPT,
        prompts.RULES_SYSTEM_PROMPT,
    )

    assert all(isinstance(prompt, str) and prompt.strip() for prompt in constants)
    assert all(
        not re.search(r"\b(scholarship|student|CGPA)\b", prompt, re.IGNORECASE)
        for prompt in constants
    )


def test_user_prompt_builders_wrap_content_in_source_tags():
    section_text = "Section text."
    evidence_lines = ["EVD-001 | step | Evidence quote."]

    assert prompts.build_evidence_user_prompt(section_text) == (
        "<source>\nSection text.\n</source>"
    )
    expected = "<source>\nEVD-001 | step | Evidence quote.\n</source>"
    assert prompts.build_as_is_user_prompt(evidence_lines) == expected
    assert prompts.build_rules_user_prompt(evidence_lines) == expected
