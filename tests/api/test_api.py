"""HTTP-level tests against the FastAPI app with fresh in-memory repositories."""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.api import dependencies
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.index_repository import IndexRepository
from app.repositories.library_repository import LibraryRepository
from app.services.chunk_service import ChunkService
from app.services.library_service import LibraryService
from app.services.search_service import SearchService


@pytest.fixture
def client(monkeypatch):
    """Client whose services use fresh, non-persistent repositories."""
    library_repo = LibraryRepository()
    chunk_repo = ChunkRepository()
    index_repo = IndexRepository()

    def library_service():
        return LibraryService(library_repo, index_repo, chunk_repo)

    def chunk_service():
        return ChunkService(chunk_repo, library_service(), index_repo)

    def search_service():
        return SearchService(library_service(), chunk_repo, index_repo)

    main.app.dependency_overrides[dependencies.get_library_service] = library_service
    main.app.dependency_overrides[dependencies.get_chunk_service] = chunk_service
    main.app.dependency_overrides[dependencies.get_search_service] = search_service
    # /debug/indexes reads the repositories directly
    monkeypatch.setattr(dependencies, "get_library_repository", lambda: library_repo)
    monkeypatch.setattr(dependencies, "get_chunk_repository", lambda: chunk_repo)
    monkeypatch.setattr(dependencies, "get_index_repository", lambda: index_repo)

    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def create_library(client, index_type="flat"):
    response = client.post("/api/v1/libraries", json={"name": "lib", "index_type": index_type})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def add_chunk(client, library_id, embedding, **metadata):
    body = {"text": "text", "embedding": embedding, "metadata": metadata or {"source": "test"}}
    return client.post(f"/api/v1/libraries/{library_id}/chunks", json=body)


class TestDimensionValidation:

    @pytest.mark.parametrize("index_type", ["flat", "ivf"])
    def test_wrong_dimension_chunk_is_rejected_and_not_stored(self, client, index_type):
        library_id = create_library(client, index_type)
        assert add_chunk(client, library_id, [1.0, 0.0, 0.0, 0.0]).status_code == 201

        response = add_chunk(client, library_id, [1.0, 0.0, 0.0])

        assert response.status_code == 400
        assert "dimension" in response.json()["detail"]
        chunks = client.get(f"/api/v1/libraries/{library_id}/chunks").json()
        assert len(chunks) == 1
        library = client.get(f"/api/v1/libraries/{library_id}").json()
        assert sum(len(doc["chunks"]) for doc in library["documents"]) == 1

        search = client.post(f"/api/v1/libraries/{library_id}/search",
                             json={"embedding": [1.0, 0.0, 0.0, 0.0], "k": 5})
        assert search.status_code == 200
        assert len(search.json()) == 1

    def test_wrong_dimension_query_is_400(self, client):
        library_id = create_library(client)
        add_chunk(client, library_id, [1.0, 0.0])

        response = client.post(f"/api/v1/libraries/{library_id}/search",
                               json={"embedding": [1.0, 0.0, 0.0], "k": 5})

        assert response.status_code == 400

    def test_wrong_dimension_update_leaves_chunk_unchanged(self, client):
        library_id = create_library(client)
        chunk_id = add_chunk(client, library_id, [1.0, 0.0]).json()["id"]
        add_chunk(client, library_id, [0.0, 1.0])

        response = client.put(f"/api/v1/libraries/{library_id}/chunks/{chunk_id}",
                              json={"text": "changed", "embedding": [1.0, 0.0, 0.0]})

        assert response.status_code == 400
        chunk = client.get(f"/api/v1/libraries/{library_id}/chunks/{chunk_id}").json()
        assert chunk["text"] == "text"
        assert chunk["embedding"] == [1.0, 0.0]


class TestFilteredSearch:

    def test_filter_applies_before_top_k(self, client):
        library_id = create_library(client)
        # 30 "common" chunks close to the query, 5 "rare" chunks far from it
        for i in range(30):
            add_chunk(client, library_id, [1.0, i / 100], source="common")
        for i in range(5):
            add_chunk(client, library_id, [-1.0, i / 100], source="rare")

        response = client.post(f"/api/v1/libraries/{library_id}/search", json={
            "embedding": [1.0, 0.0], "k": 5, "filters": {"source": "rare"}
        })

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 5
        assert all(r["chunk"]["metadata"]["source"] == "rare" for r in results)

    def test_filter_with_no_matches_returns_empty(self, client):
        library_id = create_library(client)
        add_chunk(client, library_id, [1.0, 0.0], source="common")

        response = client.post(f"/api/v1/libraries/{library_id}/search", json={
            "embedding": [1.0, 0.0], "k": 5, "filters": {"source": "missing"}
        })

        assert response.status_code == 200
        assert response.json() == []


class TestIndexTypes:

    def test_hnsw_is_rejected_on_create(self, client):
        response = client.post("/api/v1/libraries", json={"name": "lib", "index_type": "hnsw"})
        assert response.status_code == 422

    def test_hnsw_is_rejected_on_update(self, client):
        library_id = create_library(client)
        response = client.put(f"/api/v1/libraries/{library_id}", json={"index_type": "hnsw"})
        assert response.status_code == 422

    def test_index_repository_rejects_unknown_type(self):
        from uuid import uuid4
        with pytest.raises(ValueError):
            IndexRepository().create_index(uuid4(), "hnsw")

    def test_changing_index_type_keeps_chunks_searchable(self, client):
        library_id = create_library(client, "flat")
        for i in range(3):
            add_chunk(client, library_id, [1.0, float(i)])

        response = client.put(f"/api/v1/libraries/{library_id}", json={"index_type": "ivf"})
        assert response.status_code == 200

        search = client.post(f"/api/v1/libraries/{library_id}/search",
                             json={"embedding": [1.0, 0.0], "k": 5})
        assert len(search.json()) == 3


class TestDebugEndpoint:

    def test_empty_index_reports_its_class(self, client):
        library_id = create_library(client, "ivf")

        info = client.get("/debug/indexes").json()["libraries"][library_id]

        assert info["index_exists"] is True
        assert info["index_class"] == "IVFIndex"
        assert info["index_size"] == 0
