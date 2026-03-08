"""Tests for storage layer."""

import json
import tempfile
from pathlib import Path

import pytest

from reqcraft.models import (
    Collection,
    Environment,
    HistoryEntry,
    HttpMethod,
    RequestModel,
    ResponseModel,
)
from reqcraft.storage import Storage


@pytest.fixture
def tmp_storage(tmp_path: Path) -> Storage:
    """Create a storage instance using a temp directory."""
    return Storage(data_dir=tmp_path)


class TestCollections:
    def test_save_and_load(self, tmp_storage: Storage):
        col = Collection(
            name="Test API",
            requests=[
                RequestModel(method=HttpMethod.GET, url="https://example.com"),
                RequestModel(method=HttpMethod.POST, url="https://example.com/data"),
            ],
        )
        tmp_storage.save_collections([col])
        loaded = tmp_storage.load_collections()
        assert len(loaded) == 1
        assert loaded[0].name == "Test API"
        assert len(loaded[0].requests) == 2

    def test_add_to_new_collection(self, tmp_storage: Storage):
        req = RequestModel(method=HttpMethod.GET, url="https://example.com")
        col = tmp_storage.add_to_collection("New Collection", req)
        assert col.name == "New Collection"
        assert len(col.requests) == 1

        # Add another request to same collection
        req2 = RequestModel(method=HttpMethod.POST, url="https://example.com/post")
        tmp_storage.add_to_collection("New Collection", req2)
        loaded = tmp_storage.load_collections()
        assert len(loaded) == 1
        assert len(loaded[0].requests) == 2

    def test_delete_collection(self, tmp_storage: Storage):
        col = Collection(name="To Delete")
        tmp_storage.save_collections([col])
        tmp_storage.delete_collection(col.id)
        loaded = tmp_storage.load_collections()
        assert len(loaded) == 0

    def test_load_empty(self, tmp_storage: Storage):
        loaded = tmp_storage.load_collections()
        assert loaded == []

    def test_load_corrupted(self, tmp_storage: Storage):
        tmp_storage.collections_file.write_text("not json", encoding="utf-8")
        loaded = tmp_storage.load_collections()
        assert loaded == []


class TestEnvironments:
    def test_save_and_load(self, tmp_storage: Storage):
        env = Environment(
            name="Dev",
            variables={"base_url": "http://localhost:8000"},
            is_active=True,
        )
        tmp_storage.save_environments([env])
        loaded = tmp_storage.load_environments()
        assert len(loaded) == 1
        assert loaded[0].name == "Dev"
        assert loaded[0].variables["base_url"] == "http://localhost:8000"

    def test_get_active_environment(self, tmp_storage: Storage):
        envs = [
            Environment(name="Dev", is_active=False),
            Environment(name="Prod", is_active=True),
        ]
        tmp_storage.save_environments(envs)
        active = tmp_storage.get_active_environment()
        assert active is not None
        assert active.name == "Prod"

    def test_no_active_environment(self, tmp_storage: Storage):
        envs = [
            Environment(name="Dev", is_active=False),
        ]
        tmp_storage.save_environments(envs)
        active = tmp_storage.get_active_environment()
        assert active is None

    def test_set_active_environment(self, tmp_storage: Storage):
        envs = [
            Environment(name="Dev"),
            Environment(name="Prod"),
        ]
        tmp_storage.save_environments(envs)

        tmp_storage.set_active_environment(envs[1].id)
        loaded = tmp_storage.load_environments()
        assert loaded[1].is_active is True
        assert loaded[0].is_active is False


class TestHistory:
    def test_append_and_load(self, tmp_storage: Storage):
        entry = HistoryEntry(
            request=RequestModel(url="https://example.com"),
            response=ResponseModel(status_code=200),
        )
        tmp_storage.append_history(entry)
        loaded = tmp_storage.load_history()
        assert len(loaded) == 1
        assert loaded[0].request.url == "https://example.com"

    def test_history_order(self, tmp_storage: Storage):
        for i in range(5):
            entry = HistoryEntry(
                request=RequestModel(url=f"https://example.com/{i}"),
            )
            tmp_storage.append_history(entry)

        loaded = tmp_storage.load_history()
        assert len(loaded) == 5
        # Newest should be first
        assert loaded[0].request.url == "https://example.com/4"

    def test_clear_history(self, tmp_storage: Storage):
        entry = HistoryEntry(request=RequestModel(url="https://example.com"))
        tmp_storage.append_history(entry)
        tmp_storage.clear_history()
        loaded = tmp_storage.load_history()
        assert len(loaded) == 0

    def test_load_empty(self, tmp_storage: Storage):
        loaded = tmp_storage.load_history()
        assert loaded == []
