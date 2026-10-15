"""FastAPI routes for clarification questions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.clarification_item import ClarificationItemRead
from processfoundry_ai.repositories.clarification_item_repository import ClarificationItemRepository
from processfoundry_ai.repositories.project_repository import ProjectRepository

# Router for project questions: GET /api/projects/{project_id}/questions
project_questions_router = APIRouter()

# Router for questions answer: POST /api/questions/{question_id}/answer
questions_router = APIRouter()


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig.from_env()


class QuestionAnswerRequest(BaseModel):
    """Payload for answering a clarification question."""

    answer: str = Field(..., min_length=1, description="Answer text")
    answered_by: str = Field(..., min_length=1, description="Identity of reviewer or approver")


@project_questions_router.get("", response_model=list[ClarificationItemRead])
def list_project_questions(
    project_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
):
    """List clarification items/questions for a project."""
    config = get_db_config()
    if ProjectRepository(config).get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    items = ClarificationItemRepository(config).list_by_project(project_id)
    if status_filter:
        items = [item for item in items if item.status.lower() == status_filter.lower()]
    return items[offset : offset + limit]


@questions_router.post(
    "/{question_id}/answer",
    response_model=ClarificationItemRead,
    status_code=status.HTTP_200_OK,
)
def answer_question(question_id: str, payload: QuestionAnswerRequest):
    """Save a human answer for a clarification question."""
    config = get_db_config()
    repo = ClarificationItemRepository(config)
    question = repo.get_by_id(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Clarification question not found.")

    updates = {
        "answer": payload.answer.strip(),
        "answered_by": payload.answered_by.strip(),
        "status": "answered",
    }
    updated = repo.update(question_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Clarification question not found.")
    return updated
