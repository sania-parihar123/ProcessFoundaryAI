"""All prompts live here; they stay generic and instruct the model to extract only what the source states."""

# Bump this whenever any prompt changes, so results can be traced to the prompt that produced them.
PROMPT_VERSION = "1"

EVIDENCE_SYSTEM_PROMPT = (
    "Extract relevant evidence from the provided source text. "
    "Quote exactly, word for word; do not paraphrase; do not invent. "
    "Classify each quote using the allowed claim types and confidence labels. "
    "Do not provide or invent IDs; IDs are assigned by the calling code. "
    "If nothing relevant, return an empty list. "
    "Return only the requested structured data."
)

AS_IS_SYSTEM_PROMPT = (
    "A step is an ACTION that someone performs as part of the process, in sequence. "
    "Facts about amounts, dates, eligibility conditions, contact details, and notifications "
    "are NOT steps. Step names must be short imperative phrases, not copies of full sentences. "
    "Build process steps only from the evidence given; do not invent steps. "
    "Return steps in the order they happen. Use the actor wording found in the quotes; "
    "if no actor is stated, use null. Each step must cite its evidence IDs. "
    "Cite only evidence IDs included in the supplied evidence list. "
    "Return only the requested structured data."
)

RULES_SYSTEM_PROMPT = (
    "A rule is a requirement, restriction, condition, deadline or consequence that governs the process. "
    "Descriptions of purpose, process steps, notifications, contact details and amounts that are not "
    "conditions are NOT rules. Condition means when or under what circumstance the rule applies; "
    "action means what must or must not happen. Use only the evidence given. Do not invent rules. "
    "Use the wording from the quotes. Never copy the labels in the evidence list into any field. "
    "Use null when the evidence does not state a value. "
    "If conflicting values are present, output them as separate rules; never choose or merge them. "
    "Return only the requested structured data."
)


def build_evidence_line(evidence_id: str, claim_type: str, quote: str) -> str:
    return f"{evidence_id} | {claim_type} | {quote}"


def _wrap_source(text: str) -> str:
    return f"<source>\n{text}\n</source>"


def build_evidence_user_prompt(section_text: str) -> str:
    return _wrap_source(section_text)


def build_as_is_user_prompt(evidence_lines: list[str]) -> str:
    return _wrap_source("\n".join(evidence_lines))


def build_rules_user_prompt(evidence_lines: list[str]) -> str:
    return _wrap_source("\n".join(evidence_lines))
