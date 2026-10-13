"""Process-neutral, provenance-preserving evidence contracts."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
ExactQuote = Annotated[str, StringConstraints(min_length=1)]


class EvidenceKind(StrEnum):
    """Generic categories of information extracted from process sources."""

    ACTIVITY = "activity"
    ACTOR = "actor"
    REQUIREMENT = "requirement"
    CONDITION = "condition"
    DECISION = "decision"
    EXCEPTION = "exception"
    DEADLINE = "deadline"
    RESPONSIBILITY = "responsibility"
    DATA = "data"
    RELATIONSHIP = "relationship"
    UNKNOWN = "unknown"
    STATEMENT = "statement"


class EvidenceStatus(StrEnum):
    """Interpretation status for an evidence item."""

    EXTRACTED = "extracted"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class SourceLocator(BaseModel):
    """A source location without assuming unavailable pagination or layout."""

    model_config = ConfigDict(extra="forbid")

    document_id: NonEmptyString
    section_id: NonEmptyString | None = None
    filename: NonEmptyString | None = None
    page: int | None = Field(default=None, ge=1)
    paragraph: int | None = Field(default=None, ge=1)
    section: int | None = Field(default=None, ge=1)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    newline_convention: Literal["LF", "CRLF", "CR", "none"] | None = None
    heading: NonEmptyString | None = None
    table_id: NonEmptyString | None = None
    worksheet_name: NonEmptyString | None = None
    row_number: int | None = Field(default=None, ge=1)
    cell_coordinates: list[NonEmptyString] = Field(default_factory=list)


class Assertion(BaseModel):
    """A normalized, domain-neutral claim supported by evidence."""

    model_config = ConfigDict(extra="forbid")

    subject: NonEmptyString | None = None
    predicate: NonEmptyString | None = None
    operator: NonEmptyString | None = None
    value: Any = None
    unit: NonEmptyString | None = None
    comparison: NonEmptyString | None = None
    exception: str | None = None


class ActorReference(BaseModel):
    """A reference to an actor without imposing a role vocabulary."""

    model_config = ConfigDict(extra="forbid")

    actor_id: NonEmptyString | None = None
    label: NonEmptyString
    actor_type: NonEmptyString | None = None
    role: NonEmptyString | None = None


class Condition(BaseModel):
    """A condition attached to an activity, requirement, or decision."""

    model_config = ConfigDict(extra="forbid")

    expression: str | None = None
    operator: NonEmptyString | None = None
    operands: list[Any] = Field(default_factory=list)
    evidence_refs: list[NonEmptyString] = Field(default_factory=list)


class ExceptionInfo(BaseModel):
    """An exception or alternate path stated by a source."""

    model_config = ConfigDict(extra="forbid")

    description: NonEmptyString
    condition: str | None = None
    evidence_refs: list[NonEmptyString] = Field(default_factory=list)


class TemporalInformation(BaseModel):
    """Effective dates, deadlines, and recurrence information."""

    model_config = ConfigDict(extra="forbid")

    effective_from: str | date | datetime | None = None
    effective_until: str | date | datetime | None = None
    deadline: str | date | datetime | None = None
    recurrence: NonEmptyString | None = None


class Responsibility(BaseModel):
    """An actor's responsibility for an activity or decision."""

    model_config = ConfigDict(extra="forbid")

    actor_refs: list[NonEmptyString] = Field(default_factory=list)
    action: NonEmptyString | None = None
    authority_level: NonEmptyString | None = None


class UnknownInformation(BaseModel):
    """A field or interpretation that remains explicitly unknown."""

    model_config = ConfigDict(extra="forbid")

    field: NonEmptyString
    question: NonEmptyString
    reason: str | None = None


class Ambiguity(BaseModel):
    """Alternative interpretations retained without selecting one."""

    model_config = ConfigDict(extra="forbid")

    is_ambiguous: bool = False
    alternatives: list[Any] = Field(default_factory=list)
    reason: str | None = None


class EvidenceItem(BaseModel):
    """A generic evidence record with legacy ingestion compatibility fields."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: NonEmptyString
    kind: EvidenceKind
    status: EvidenceStatus = EvidenceStatus.EXTRACTED
    quote: ExactQuote
    quote_char_start: int | None = Field(default=None, ge=0)
    quote_char_end: int | None = Field(default=None, ge=0)
    normalized_interpretation: str | None = None
    source_refs: list[NonEmptyString] = Field(default_factory=list)
    source_locations: list[SourceLocator] = Field(default_factory=list)

    subject: NonEmptyString | None = None
    predicate: NonEmptyString | None = None
    operator: NonEmptyString | None = None
    value: Any = None
    unit: NonEmptyString | None = None
    assertion: Assertion | None = None

    actors: list[ActorReference] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)
    exceptions: list[ExceptionInfo] = Field(default_factory=list)
    temporal: TemporalInformation | None = None
    responsibilities: list[Responsibility] = Field(default_factory=list)

    confidence: float | None = Field(default=None, ge=0, le=1)
    ambiguity: Ambiguity | None = None
    related_evidence_refs: list[NonEmptyString] = Field(default_factory=list)
    unknowns: list[UnknownInformation] = Field(default_factory=list)

    # Legacy fields retained for current extraction, analysis, UI, and tests.
    source_id: NonEmptyString | None = None
    document_id: NonEmptyString | None = None
    filename: NonEmptyString | None = None
    section_id: NonEmptyString | None = None
    page: int | None = Field(default=None, ge=1)
    section: int | None = Field(default=None, ge=1)
    worksheet_name: NonEmptyString | None = None
    row_number: int | None = Field(default=None, ge=1)
    headers: list[str] | None = None
    cells: list[dict[str, Any]] | None = None
    cell_references: list[NonEmptyString] | None = None
