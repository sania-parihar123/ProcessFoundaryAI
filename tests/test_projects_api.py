
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from processfoundry_ai.main import app
from processfoundry_ai.api.routes import projects


client = TestClient(app)


class FakeProjectRepository:
    """A temporary in-memory repository for API tests."""

    def __init__(self):
        self.data = {}

    def create(self, project):
        from processfoundry_ai.models.project import ProjectRead

        saved_project = ProjectRead.model_validate(project)
        self.data[saved_project.id] = saved_project
        return saved_project

    def list_projects(self):
        return list(self.data.values())

    def get_by_id(self, project_id):
        return self.data.get(project_id)


@pytest.fixture
def fake_repository(monkeypatch):
    repository = FakeProjectRepository()

    monkeypatch.setattr(
        projects,
        "get_project_repository",
        lambda: repository,
    )

    return repository


def test_create_project(fake_repository):
    response = client.post(
        "/api/projects",
        json={
            "name": "Scholarship Process",
            "process_type": "Scholarship",
            "description": "Improve the scholarship workflow.",
            "status": "draft",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Scholarship Process"
    assert data["process_type"] == "Scholarship"
    assert data["status"] == "draft"
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]


def test_list_projects(fake_repository):
    client.post(
        "/api/projects",
        json={
            "name": "Scholarship Process",
            "process_type": "Scholarship",
            "description": "Improve the scholarship workflow.",
            "status": "draft",
        },
    )

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Scholarship Process"


def test_get_project_by_id(fake_repository):
    create_response = client.post(
        "/api/projects",
        json={
            "name": "Scholarship Process",
            "process_type": "Scholarship",
            "description": "Improve the scholarship workflow.",
            "status": "draft",
        },
    )

    project_id = create_response.json()["id"]

    response = client.get(f"/api/projects/{project_id}")

    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_get_missing_project_returns_404(fake_repository):
    response = client.get("/api/projects/nonexistent-project")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found."


def test_empty_project_name_returns_422(fake_repository):
    response = client.post(
        "/api/projects",
        json={
            "name": "   ",
            "process_type": "Scholarship",
            "description": "Improve the scholarship workflow.",
            "status": "draft",
        },
    )

    assert response.status_code == 422
