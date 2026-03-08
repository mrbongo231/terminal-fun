"""JSON-based persistence for collections, environments, and history."""

from __future__ import annotations

import json
import os
from pathlib import Path

from reqcraft.models import Collection, Environment, HistoryEntry


def _get_data_dir() -> Path:
    """Get the application data directory, cross-platform."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.environ.get("XDG_DATA_HOME"):
        base = Path(os.environ["XDG_DATA_HOME"])
    else:
        base = Path.home() / ".local" / "share"

    data_dir = base / "reqcraft"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class Storage:
    """Manages persistence for ReqCraft data."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _get_data_dir()
        self.collections_file = self.data_dir / "collections.json"
        self.environments_file = self.data_dir / "environments.json"
        self.history_file = self.data_dir / "history.json"
        self._max_history = 500

    # ── Collections ──

    def load_collections(self) -> list[Collection]:
        """Load all collections from disk."""
        if not self.collections_file.exists():
            return []
        try:
            with open(self.collections_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Collection.from_dict(c) for c in data]
        except (json.JSONDecodeError, KeyError):
            return []

    def save_collections(self, collections: list[Collection]) -> None:
        """Save all collections to disk."""
        data = [c.to_dict() for c in collections]
        with open(self.collections_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_to_collection(
        self, collection_name: str, request: "RequestModel"
    ) -> Collection:
        """Add a request to a collection, creating it if needed."""
        from reqcraft.models import RequestModel

        collections = self.load_collections()

        # Find or create collection
        target = None
        for c in collections:
            if c.name == collection_name:
                target = c
                break

        if target is None:
            target = Collection(name=collection_name)
            collections.append(target)

        target.requests.append(request)
        self.save_collections(collections)
        return target

    def delete_collection(self, collection_id: str) -> None:
        """Delete a collection by ID."""
        collections = self.load_collections()
        collections = [c for c in collections if c.id != collection_id]
        self.save_collections(collections)

    def remove_from_collection(
        self, collection_id: str, request_id: str
    ) -> None:
        """Remove a request from a collection."""
        collections = self.load_collections()
        for c in collections:
            if c.id == collection_id:
                c.requests = [r for r in c.requests if r.id != request_id]
                break
        self.save_collections(collections)

    # ── Environments ──

    def load_environments(self) -> list[Environment]:
        """Load all environments from disk."""
        if not self.environments_file.exists():
            return []
        try:
            with open(self.environments_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Environment.from_dict(e) for e in data]
        except (json.JSONDecodeError, KeyError):
            return []

    def save_environments(self, environments: list[Environment]) -> None:
        """Save all environments to disk."""
        data = [e.to_dict() for e in environments]
        with open(self.environments_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_active_environment(self) -> Environment | None:
        """Get the currently active environment, if any."""
        for env in self.load_environments():
            if env.is_active:
                return env
        return None

    def set_active_environment(self, env_id: str | None) -> None:
        """Set the active environment by ID, or deactivate all if None."""
        environments = self.load_environments()
        for env in environments:
            env.is_active = env.id == env_id
        self.save_environments(environments)

    # ── History ──

    def load_history(self) -> list[HistoryEntry]:
        """Load request history from disk."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [HistoryEntry.from_dict(h) for h in data]
        except (json.JSONDecodeError, KeyError):
            return []

    def append_history(self, entry: HistoryEntry) -> None:
        """Add an entry to the history, trimming old entries if needed."""
        history = self.load_history()
        history.insert(0, entry)  # Newest first
        if len(history) > self._max_history:
            history = history[: self._max_history]
        self._save_history(history)

    def clear_history(self) -> None:
        """Clear all history."""
        self._save_history([])

    def _save_history(self, history: list[HistoryEntry]) -> None:
        """Save history to disk."""
        data = [h.to_dict() for h in history]
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
