import importlib
import sys
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


class _MappingResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeStatement:
    def bindparams(self, *args, **kwargs):
        return self


@pytest.fixture
def embeddings_module():
    with patch.dict(sys.modules, {"ollama": MagicMock()}):
        module = importlib.import_module("app.services.embeddings")
        module = importlib.reload(module)
        yield module


def test_build_candidate_embedding_text(embeddings_module):
    profile_json = {
        "summary": "Builds reliable backend services.",
        "skills": [{"name": "Python"}, {"name": "SQL"}],
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Acme",
                "start_date": "2021-01",
                "end_date": "2023-12",
            }
        ],
    }

    text_value = embeddings_module.build_candidate_embedding_text(
        profile_json=profile_json,
        name="Ada Lovelace",
        title="Staff Engineer",
    )

    assert "Name: Ada Lovelace" in text_value
    assert "Title: Staff Engineer" in text_value
    assert "Summary: Builds reliable backend services." in text_value
    assert "Skills: python, sql" in text_value
    assert "Experience: Senior Engineer at Acme (2021-01 - 2023-12)" in text_value


def test_build_candidate_embedding_text_handles_missing_fields(embeddings_module):
    text_value = embeddings_module.build_candidate_embedding_text(profile_json={"skills": [None, {}]})
    assert text_value == ""


def test_build_candidate_embedding_text_truncates_long_text(embeddings_module):
    very_long_summary = "x" * 9000
    text_value = embeddings_module.build_candidate_embedding_text(
        profile_json={"summary": very_long_summary},
        name="Long Candidate",
    )
    assert len(text_value) == 8000


def test_build_position_embedding_text(embeddings_module):
    position = SimpleNamespace(
        title="Backend Engineer",
        department="Engineering",
        summary="Work on APIs",
        requirements=["Python", "FastAPI"],
        responsibilities=["Build APIs"],
        nice_to_have=["pgvector"],
    )

    text_value = embeddings_module.build_position_embedding_text(position)

    assert "Title: Backend Engineer" in text_value
    assert "Department: Engineering" in text_value
    assert "Summary: Work on APIs" in text_value
    assert "Requirements:\n- Python\n- FastAPI" in text_value
    assert "Responsibilities:\n- Build APIs" in text_value
    assert "Nice to Have:\n- pgvector" in text_value


def test_build_position_embedding_text_handles_missing_fields(embeddings_module):
    position = SimpleNamespace(
        title="  ",
        department=None,
        summary="",
        requirements=[],
        responsibilities=None,
        nice_to_have=[""],
    )
    assert embeddings_module.build_position_embedding_text(position) == ""


@pytest.mark.asyncio
async def test_generate_embedding(embeddings_module):
    expected = [0.1] * 768
    with patch.object(embeddings_module, "Client") as mock_client:
        mock_client.return_value.embeddings.return_value = {"embedding": expected}
        result = await embeddings_module.generate_embedding("python engineer")

    assert len(result) == 768
    assert result == expected

    with patch.object(embeddings_module, "Client") as mock_client:
        mock_client.return_value.embeddings.side_effect = RuntimeError("down")
        with pytest.raises(RuntimeError, match="Ollama API error"):
            await embeddings_module.generate_embedding("python engineer")

    with patch.object(embeddings_module, "Client") as mock_client:
        mock_client.return_value.embeddings.return_value = {"embedding": [0.2] * 10}
        with pytest.raises(RuntimeError, match="expected embedding dimension"):
            await embeddings_module.generate_embedding("python engineer")


@pytest.mark.asyncio
async def test_generate_match_explanation(embeddings_module):
    with patch.object(embeddings_module, "load_prompt", return_value="C={candidate_text} P={position_text} S={score}"), patch.object(
        embeddings_module, "Client"
    ) as mock_client:
        mock_client.return_value.chat.return_value = {"message": {"content": "Strong backend fit."}}

        explanation = await embeddings_module.generate_match_explanation(
            "Candidate has Python and FastAPI.",
            "Position requires Python APIs.",
            8.5,
        )

    assert explanation == "Strong backend fit."
    call_kwargs = mock_client.return_value.chat.call_args.kwargs
    assert call_kwargs["messages"][1]["content"].find("Candidate has Python and FastAPI.") >= 0
    assert call_kwargs["messages"][1]["content"].find("Position requires Python APIs.") >= 0


def test_find_similar_candidates(embeddings_module):
    position_id = uuid.uuid4()
    excluded_id = uuid.uuid4()
    row1_id = uuid.uuid4()
    row2_id = uuid.uuid4()

    db = Mock()
    db.get.return_value = SimpleNamespace(embedding=[0.1] * 768)
    db.execute.return_value = _MappingResult(
        [
            {"id": excluded_id, "name": "Excluded", "title": "Eng", "distance": 0.05},
            {"id": row1_id, "name": "Top", "title": "Senior", "distance": 0.10},
            {"id": row2_id, "name": "Second", "title": "Mid", "distance": 0.20},
            {"id": uuid.uuid4(), "name": "Far", "title": "Junior", "distance": 0.90},
        ]
    )

    with patch.object(embeddings_module, "text", return_value=_FakeStatement()):
        results = embeddings_module.find_similar_candidates(
            position_id,
            db,
            limit=5,
            exclude_ids=[excluded_id],
        )

    assert [item.id for item in results] == [excluded_id, row1_id, row2_id]
    assert all(item.distance < embeddings_module.settings.similarity_threshold for item in results)
    execute_params = db.execute.call_args.args[1]
    assert execute_params["exclude_ids"] == [excluded_id]


def test_find_similar_positions(embeddings_module):
    candidate_id = uuid.uuid4()
    row1_id = uuid.uuid4()
    row2_id = uuid.uuid4()

    db = Mock()
    db.get.return_value = SimpleNamespace(embedding=[0.2] * 768)
    db.execute.return_value = _MappingResult(
        [
            {"id": row1_id, "name": "Backend Engineer", "title": "Backend Engineer", "distance": 0.05},
            {"id": row2_id, "name": "Data Engineer", "title": "Data Engineer", "distance": 0.25},
            {"id": uuid.uuid4(), "name": "Far", "title": "Far", "distance": 0.45},
        ]
    )

    results = embeddings_module.find_similar_positions(candidate_id, db, limit=3)

    assert [item.id for item in results] == [row1_id, row2_id]
    assert all(item.distance < embeddings_module.settings.similarity_threshold for item in results)


@pytest.mark.asyncio
async def test_rerank_candidates(embeddings_module):
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    candidates = [
        SimpleNamespace(id=first_id, name="Alpha", title="Engineer", distance=0.20, embedding_text="alpha text"),
        SimpleNamespace(id=second_id, name="Beta", title="Engineer", distance=0.15, embedding_text="beta text"),
    ]

    with patch.object(
        embeddings_module,
        "_rerank_pair",
        new=AsyncMock(
            side_effect=[
                embeddings_module.RerankResponse(score=6, reason="good"),
                embeddings_module.RerankResponse(score=9, reason="best"),
            ]
        ),
    ):
        results = await embeddings_module.rerank_candidates(candidates, "position text")

    assert [item.id for item in results] == [second_id, first_id]
    assert [item.llm_score for item in results] == [9, 6]


@pytest.mark.asyncio
async def test_rerank_positions(embeddings_module):
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    positions = [
        SimpleNamespace(id=first_id, name="Platform Engineer", title="Platform Engineer", distance=0.20, embedding_text="platform"),
        SimpleNamespace(id=second_id, name="Backend Engineer", title="Backend Engineer", distance=0.10, embedding_text="backend"),
    ]

    with patch.object(
        embeddings_module,
        "_rerank_pair",
        new=AsyncMock(
            side_effect=[
                embeddings_module.RerankResponse(score=5, reason="ok"),
                embeddings_module.RerankResponse(score=8, reason="strong"),
            ]
        ),
    ):
        results = await embeddings_module.rerank_positions(positions, "candidate text")

    assert [item.id for item in results] == [second_id, first_id]
    assert [item.llm_score for item in results] == [8, 5]


@pytest.mark.asyncio
async def test_rerank_error_handling(embeddings_module):
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    candidates = [
        SimpleNamespace(id=first_id, name="Alpha", title="Engineer", distance=0.12, embedding_text="alpha"),
        SimpleNamespace(id=second_id, name="Beta", title="Engineer", distance=0.14, embedding_text="beta"),
    ]

    with patch.object(
        embeddings_module,
        "_rerank_pair",
        new=AsyncMock(side_effect=[embeddings_module.RerankResponse(score=7, reason="good"), RuntimeError("llm down")]),
    ):
        results = await embeddings_module.rerank_candidates(candidates, "position text")

    results_by_id = {item.id: item for item in results}
    assert results_by_id[first_id].llm_score == 7
    assert results_by_id[second_id].llm_score == 0
    assert results_by_id[second_id].llm_reason == "Reranking unavailable"


@pytest.mark.asyncio
async def test_deterministic_embeddings(embeddings_module):
    def _fake_embeddings(model, prompt):
        base = float(len(prompt) % 10)
        return {"embedding": [base] * 768}

    with patch.object(embeddings_module, "Client") as mock_client:
        mock_client.return_value.embeddings.side_effect = _fake_embeddings
        first = await embeddings_module.generate_embedding("same input")
        second = await embeddings_module.generate_embedding("same input")

    assert first == second
