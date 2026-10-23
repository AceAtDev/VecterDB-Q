"""Tests for POST /api/v1/embed and embedding provider selection."""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.api import dependencies
from app.services.embedding_service import EmbeddingService, EmbeddingUnavailable


class FakeEmbedding(EmbeddingService):
    def __init__(self, fail=False):
        super().__init__(provider="local")
        self.fail = fail
        self.calls = []

    def _embed_local(self, texts):
        if self.fail:
            raise EmbeddingUnavailable("no provider")
        self.calls.append(texts)
        return [[0.1] * 384 for _ in texts]


@pytest.fixture
def make_client():
    def _make(service):
        main.app.dependency_overrides[dependencies.get_embedding_service] = lambda: service
        return TestClient(main.app)
    yield _make
    main.app.dependency_overrides.clear()


def test_embed_returns_vectors_and_provider(make_client):
    service = FakeEmbedding()
    response = make_client(service).post("/api/v1/embed", json={"texts": ["a", "b"], "input_type": "search_query"})
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["dimension"] == 384
    assert len(body["embeddings"]) == 2
    assert service.calls == [["a", "b"]]


def test_embed_rejects_bad_input(make_client):
    client = make_client(FakeEmbedding())
    assert client.post("/api/v1/embed", json={"texts": []}).status_code == 422
    assert client.post("/api/v1/embed", json={"texts": ["a"], "input_type": "other"}).status_code == 422


def test_embed_unavailable_is_503(make_client):
    response = make_client(FakeEmbedding(fail=True)).post("/api/v1/embed", json={"texts": ["a"]})
    assert response.status_code == 503
    assert "no provider" in response.json()["detail"]


def test_auto_provider_picks_cohere_only_with_key():
    assert EmbeddingService(provider="auto", cohere_api_key="").provider == "local"
    assert EmbeddingService(provider="auto", cohere_api_key="k").provider == "cohere"
    with pytest.raises(ValueError):
        EmbeddingService(provider="openai")
