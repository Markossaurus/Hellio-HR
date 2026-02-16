import importlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


class _ScalarOneResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _ScalarsResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


@pytest.fixture
def authenticated_client(client):
    app = importlib.import_module("app.main").app
    get_current_user = importlib.import_module("app.auth").get_current_user
    user = SimpleNamespace(id=uuid.uuid4(), email="test@example.com", roles=[SimpleNamespace(name="admin")])
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_position_suggestions_success(authenticated_client, test_db):
    position_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    position = SimpleNamespace(id=position_id, embedding=[0.1] * 768, embedding_text="Backend role text")

    original_execute = test_db.execute

    def execute_with_position(statement, *args, **kwargs):
        sql = str(statement)
        if "FROM positions" in sql and "WHERE positions.id =" in sql:
            return _ScalarOneResult(position)
        if "FROM candidate_positions" in sql:
            return _ScalarsResult([])
        return original_execute(statement, *args, **kwargs)

    with patch.object(test_db, "execute", side_effect=execute_with_position), patch(
        "app.routes.suggestions.find_similar_candidates"
    ) as mock_find, patch(
        "app.routes.suggestions.rerank_candidates", new=AsyncMock()
    ) as mock_rerank:
        mock_find.return_value = [SimpleNamespace(id=candidate_id, name="Ada", title="Engineer", distance=0.1)]
        mock_rerank.return_value = [
            SimpleNamespace(
                id=candidate_id,
                name="Ada",
                title="Engineer",
                llm_score=8,
                llm_reason="Strong Python and API experience",
            )
        ]

        response = authenticated_client.get(f"/positions/{position_id}/suggestions")

    assert response.status_code == 200
    data = response.json()
    assert data["positionId"] == str(position_id)
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["candidateId"] == str(candidate_id)
    assert data["suggestions"][0]["name"] == "Ada"
    assert data["suggestions"][0]["title"] == "Engineer"
    assert data["suggestions"][0]["similarityScore"] == 8.0
    assert data["suggestions"][0]["explanation"]


def test_candidate_suggestions_success(authenticated_client, test_db):
    candidate_id = uuid.uuid4()
    position_id = uuid.uuid4()
    candidate = SimpleNamespace(id=candidate_id, embedding=[0.2] * 768, embedding_text="Candidate profile text")
    position = SimpleNamespace(id=position_id, title="Backend Engineer", department="Engineering", embedding_text="Role text")

    original_execute = test_db.execute

    def execute_with_candidate(statement, *args, **kwargs):
        sql = str(statement)
        if "FROM candidates" in sql and "WHERE candidates.id =" in sql:
            return _ScalarOneResult(candidate)
        if "FROM positions" in sql and " IN " in sql:
            return _ScalarsResult([position])
        return original_execute(statement, *args, **kwargs)

    with patch.object(test_db, "execute", side_effect=execute_with_candidate), patch(
        "app.routes.suggestions.find_similar_positions"
    ) as mock_find, patch(
        "app.routes.suggestions.rerank_positions", new=AsyncMock()
    ) as mock_rerank:
        mock_find.return_value = [SimpleNamespace(id=position_id, name="Backend Engineer", title="Backend Engineer", distance=0.1)]
        mock_rerank.return_value = [
            SimpleNamespace(
                id=position_id,
                name="Backend Engineer",
                title="Backend Engineer",
                llm_score=9,
                llm_reason="Excellent match for backend APIs",
            )
        ]

        response = authenticated_client.get(f"/candidates/{candidate_id}/suggestions")

    assert response.status_code == 200
    data = response.json()
    assert data["candidateId"] == str(candidate_id)
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["positionId"] == str(position_id)
    assert data["suggestions"][0]["title"] == "Backend Engineer"
    assert data["suggestions"][0]["department"] == "Engineering"
    assert data["suggestions"][0]["similarityScore"] == 9.0
    assert data["suggestions"][0]["explanation"]


def test_suggestions_requires_auth(client):
    response = client.get(f"/positions/{uuid.uuid4()}/suggestions")
    assert response.status_code == 401


def test_suggestions_404_not_found(authenticated_client, test_db):
    position_id = uuid.uuid4()
    original_execute = test_db.execute

    def execute_not_found(statement, *args, **kwargs):
        sql = str(statement)
        if "FROM positions" in sql and "WHERE positions.id =" in sql:
            return _ScalarOneResult(None)
        return original_execute(statement, *args, **kwargs)

    with patch.object(test_db, "execute", side_effect=execute_not_found):
        response = authenticated_client.get(f"/positions/{position_id}/suggestions")

    assert response.status_code == 404
    assert response.json()["detail"] == "Position not found"


def test_suggestions_empty_when_no_embeddings(authenticated_client, test_db):
    position_id = uuid.uuid4()
    position = SimpleNamespace(id=position_id, embedding=None, embedding_text=None)
    original_execute = test_db.execute

    def execute_no_embedding(statement, *args, **kwargs):
        sql = str(statement)
        if "FROM positions" in sql and "WHERE positions.id =" in sql:
            return _ScalarOneResult(position)
        return original_execute(statement, *args, **kwargs)

    with patch.object(test_db, "execute", side_effect=execute_no_embedding):
        response = authenticated_client.get(f"/positions/{position_id}/suggestions")

    assert response.status_code == 200
    data = response.json()
    assert data["positionId"] == str(position_id)
    assert data["suggestions"] == []


def test_exclude_already_applied_candidates(authenticated_client, test_db):
    position_id = uuid.uuid4()
    applied_candidate_id = uuid.uuid4()
    position = SimpleNamespace(id=position_id, embedding=[0.3] * 768, embedding_text="Role embedding text")

    original_execute = test_db.execute

    def execute_with_applied(statement, *args, **kwargs):
        sql = str(statement)
        if "FROM positions" in sql and "WHERE positions.id =" in sql:
            return _ScalarOneResult(position)
        if "FROM candidate_positions" in sql:
            return _ScalarsResult([applied_candidate_id])
        return original_execute(statement, *args, **kwargs)

    with patch.object(test_db, "execute", side_effect=execute_with_applied), patch(
        "app.routes.suggestions.find_similar_candidates"
    ) as mock_find, patch(
        "app.routes.suggestions.rerank_candidates", new=AsyncMock(return_value=[])
    ):
        mock_find.return_value = []

        response = authenticated_client.get(f"/positions/{position_id}/suggestions")

    assert response.status_code == 200
    assert response.json()["suggestions"] == []
    assert mock_find.call_args.kwargs["exclude_ids"] == [applied_candidate_id]


def test_candidate_suggestions_limit_cannot_exceed_three(authenticated_client):
    response = authenticated_client.get(f"/candidates/{uuid.uuid4()}/suggestions?limit=4")
    assert response.status_code == 422
