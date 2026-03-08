"""Sidebar widget with collections tree and history list."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    Button,
    Label,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

from reqcraft.models import (
    Collection,
    HistoryEntry,
    HttpMethod,
    RequestModel,
)


class HistoryItem(Static):
    """A clickable history item."""

    def __init__(self, label: str, request: RequestModel, **kwargs) -> None:
        super().__init__(label, markup=True, **kwargs)
        self.request = request

    def on_click(self) -> None:
        """Handle click on this history item."""
        self.post_message(Sidebar.RequestSelected(self.request))


class Sidebar(Widget):
    """Application sidebar with collections and history."""

    class RequestSelected(Message):
        """Fired when a request is selected from collections or history."""
        def __init__(self, request: RequestModel) -> None:
            super().__init__()
            self.request = request

    class HistoryClearRequested(Message):
        """Fired when user wants to clear history."""

    DEFAULT_CSS = """
    Sidebar {
        width: 34;
        dock: left;
        background: $surface-darken-1;
        border-right: thick $primary-background;
    }
    Sidebar #sidebar-header {
        text-style: bold;
        color: $text;
        padding: 1 1;
        background: $primary-background;
        text-align: center;
        width: 100%;
    }
    Sidebar .sidebar-tab-content {
        height: 1fr;
    }
    Sidebar #collection-tree {
        height: 1fr;
        padding: 0 1;
    }
    Sidebar #history-scroll {
        height: 1fr;
        padding: 0 1;
    }
    Sidebar .history-item {
        padding: 0 1;
        height: 2;
        margin: 0 0 1 0;
    }
    Sidebar .history-item:hover {
        background: $surface;
    }
    Sidebar .empty-sidebar {
        text-align: center;
        color: $text-muted;
        padding: 2;
    }
    Sidebar .method-badge {
        text-style: bold;
    }
    Sidebar #clear-history-btn {
        dock: bottom;
        margin: 1;
        width: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._collections: list[Collection] = []
        self._history: list[HistoryEntry] = []
        self._request_map: dict[str, RequestModel] = {}

    def compose(self) -> ComposeResult:
        yield Label("⚡ ReqCraft", id="sidebar-header")
        with TabbedContent("Collections", "History", id="sidebar-tabs"):
            with TabPane("Collections", id="sidebar-collections"):
                yield self._build_collection_tree()
            with TabPane("History", id="sidebar-history"):
                with VerticalScroll(id="history-scroll"):
                    if not self._history:
                        yield Static(
                            "No history yet.\nSend a request to get started!",
                            classes="empty-sidebar",
                        )
                    else:
                        for entry in self._history[:50]:
                            yield self._build_history_item(entry)
                yield Button(
                    "Clear History",
                    variant="error",
                    id="clear-history-btn",
                )

    def _build_collection_tree(self) -> Tree:
        """Build the collections tree widget."""
        tree: Tree[str] = Tree("📁 Collections", id="collection-tree")
        tree.root.expand()
        self._request_map.clear()

        if not self._collections:
            tree.root.add_leaf("(empty — save a request with Ctrl+S)")
        else:
            for collection in self._collections:
                branch = tree.root.add(
                    f"📁 {collection.name} ({len(collection.requests)})",
                    data=f"col:{collection.id}",
                )
                for req in collection.requests:
                    method_color = HttpMethod.color(req.method)
                    label = f"[{method_color}]{req.method.value}[/] {req.display_name()}"
                    branch.add_leaf(label, data=f"req:{req.id}")
                    self._request_map[req.id] = req
                branch.expand()

        return tree

    def _build_history_item(self, entry: HistoryEntry) -> HistoryItem:
        """Build a history list item."""
        req = entry.request
        method_color = HttpMethod.color(req.method)
        status = ""
        if entry.response:
            sc = entry.response.status_code
            status_color = (
                "#22c55e" if 200 <= sc < 300
                else "#f59e0b" if 400 <= sc < 500
                else "#ef4444" if sc >= 500
                else "#60a5fa"
            )
            status = f" [{status_color}]{sc}[/]"
        elif entry.error:
            status = " [#ef4444]ERR[/]"

        ts = datetime.fromtimestamp(entry.timestamp)
        time_str = ts.strftime("%H:%M:%S")

        url = req.url
        if len(url) > 28:
            url = url[:25] + "..."

        label = f"[{method_color} bold]{req.method.value:<7}[/]{status} {url}\n[dim]{time_str}[/]"

        return HistoryItem(label, req, classes="history-item")

    def update_collections(self, collections: list[Collection]) -> None:
        """Refresh the collections tree."""
        self._collections = collections
        try:
            tree_container = self.query_one("#sidebar-collections", TabPane)
            for old_tree in tree_container.query("#collection-tree"):
                old_tree.remove()
            new_tree = self._build_collection_tree()
            tree_container.mount(new_tree)
        except Exception:
            pass

    def update_history(self, history: list[HistoryEntry]) -> None:
        """Refresh the history list."""
        self._history = history
        try:
            scroll = self.query_one("#history-scroll", VerticalScroll)
            scroll.remove_children()
            if not self._history:
                scroll.mount(
                    Static(
                        "No history yet.\nSend a request to get started!",
                        classes="empty-sidebar",
                    )
                )
            else:
                for entry in self._history[:50]:
                    scroll.mount(self._build_history_item(entry))
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        if event.node.data and str(event.node.data).startswith("req:"):
            req_id = str(event.node.data)[4:]
            if req_id in self._request_map:
                self.post_message(self.RequestSelected(self._request_map[req_id]))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear-history-btn":
            self.post_message(self.HistoryClearRequested())
