"""Tests for snapshot persistence of the library and chunk repositories."""
import os
import pickle
from pathlib import Path

import pytest

from app.domain.models import ChunkCreate, LibraryCreate
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.index_repository import IndexRepository
from app.repositories.library_repository import LibraryRepository
from app.repositories import persistence
from app.services.chunk_service import ChunkService
from app.services.library_service import LibraryService


def build_services(persistence_path):
    library_repo = LibraryRepository(persistence_path=persistence_path)
    chunk_repo = ChunkRepository(persistence_path=persistence_path)
    index_repo = IndexRepository()
    library_service = LibraryService(library_repo, index_repo, chunk_repo)
    chunk_service = ChunkService(chunk_repo, library_service, index_repo)
    return library_service, chunk_service


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path / "vectordb.pkl")


def data_dir(store_path):
    return Path(store_path).with_suffix("")


class TestPersistenceRoundTrip:

    def test_libraries_and_chunks_survive_reload(self, store_path):
        library_service, chunk_service = build_services(store_path)
        library = library_service.create_library(LibraryCreate(name="lib", index_type="ivf"))
        created = [
            chunk_service.create_chunk(library.id, ChunkCreate(text=f"t{i}", embedding=[float(i), 1.0]))
            for i in range(5)
        ]

        library_service2, chunk_service2 = build_services(store_path)
        loaded = library_service2.get_library(library.id)

        assert loaded is not None
        assert loaded.name == "lib"
        assert loaded.index_type == "ivf"
        assert {c.id for c in chunk_service2.list_chunks(library.id)} == {c.id for c in created}
        assert not list(data_dir(store_path).glob("*.tmp"))

    def test_libraries_pkl_does_not_duplicate_chunks(self, store_path):
        library_service, chunk_service = build_services(store_path)
        library = library_service.create_library(LibraryCreate(name="lib"))
        chunk_service.create_chunk(library.id, ChunkCreate(text="hello", embedding=[1.0, 2.0]))

        # Reading hydrates the returned library with documents...
        assert library_service.get_library(library.id).documents
        # ...and a later write must not store those documents in libraries.pkl
        library_service.create_library(LibraryCreate(name="other"))

        with open(data_dir(store_path) / "libraries.pkl", "rb") as f:
            stored = pickle.load(f)
        assert all(lib.documents == [] for lib in stored.values())

    def test_delete_library_removes_its_chunks_from_disk(self, store_path):
        library_service, chunk_service = build_services(store_path)
        keep = library_service.create_library(LibraryCreate(name="keep"))
        drop = library_service.create_library(LibraryCreate(name="drop"))
        for i in range(3):
            chunk_service.create_chunk(keep.id, ChunkCreate(text="k", embedding=[1.0, float(i)]))
            chunk_service.create_chunk(drop.id, ChunkCreate(text="d", embedding=[1.0, float(i)]))

        assert library_service.delete_library(drop.id)

        with open(data_dir(store_path) / "chunks.pkl", "rb") as f:
            data = pickle.load(f)
        assert drop.id not in data["chunks"]
        assert drop.id not in data["documents"]
        assert len(data["chunks"][keep.id]) == 3


class TestAtomicWrite:

    def test_fsyncs_file_and_directory(self, tmp_path, monkeypatch):
        synced = []
        real_fsync = os.fsync

        def recording_fsync(fd):
            synced.append(fd)
            real_fsync(fd)

        monkeypatch.setattr(persistence.os, "fsync", recording_fsync)
        target = tmp_path / "data.pkl"
        persistence.atomic_pickle_dump({"a": 1}, target)

        expected = 2 if os.name == "posix" else 1
        assert len(synced) == expected
        with open(target, "rb") as f:
            assert pickle.load(f) == {"a": 1}
        assert not (tmp_path / "data.tmp").exists()

    def test_failed_write_keeps_previous_snapshot(self, tmp_path):
        target = tmp_path / "data.pkl"
        persistence.atomic_pickle_dump({"version": 1}, target)

        class Unpicklable:
            def __reduce__(self):
                raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            persistence.atomic_pickle_dump({"version": 2, "bad": Unpicklable()}, target)

        with open(target, "rb") as f:
            assert pickle.load(f) == {"version": 1}
