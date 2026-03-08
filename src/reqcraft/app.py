"""ReqCraft — Main Textual Application."""

from __future__ import annotations

import asyncio
import copy
from pathlib import Path

from rich.markup import escape as markup_escape

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, LoadingIndicator, Static

from reqcraft import __app_name__, __version__
from reqcraft.config import AppConfig
from reqcraft.curl_parser import parse_curl, to_curl
from reqcraft.http_client import send_request
from reqcraft.models import (
    BodyType,
    Collection,
    Environment,
    HistoryEntry,
    HttpMethod,
    KeyValuePair,
    RequestModel,
    ResponseModel,
)
from reqcraft.storage import Storage
from reqcraft.widgets.environment_modal import (
    CurlExportModal,
    CurlImportModal,
    EnvironmentModal,
    SaveRequestModal,
)
from reqcraft.widgets.request_panel import RequestPanel
from reqcraft.widgets.response_panel import ResponsePanel
from reqcraft.widgets.sidebar import Sidebar
from reqcraft.widgets.url_bar import UrlBar


class ReqCraftApp(App):
    """The ReqCraft terminal API testing client."""

    TITLE = f"{__app_name__} v{__version__}"
    SUB_TITLE = "Interactive API Testing Client"

    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("ctrl+enter", "send_request", "Send Request", show=True, priority=True),
        Binding("ctrl+s", "save_request", "Save Request", show=True),
        Binding("ctrl+i", "import_curl", "Import cURL", show=True),
        Binding("ctrl+x", "export_curl", "Export cURL", show=True),
        Binding("ctrl+e", "manage_environments", "Environments", show=True),
        Binding("ctrl+l", "clear_response", "Clear Response", show=False),
        Binding("ctrl+n", "new_request", "New Request", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self, config: AppConfig | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config or AppConfig.load()
        self.storage = Storage()
        self._current_request = RequestModel()
        self._is_sending = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Environment badge (shown when an env is active)
        active_env = self.storage.get_active_environment()
        env_label = f"🌍 {active_env.name}" if active_env else "No Environment"
        yield Label(env_label, id="env-badge")

        # Main layout
        with Horizontal(id="app-layout"):
            yield Sidebar(id="sidebar")
            with Vertical(id="main-content"):
                yield UrlBar(id="url-bar-widget")
                # Loading indicator
                yield LoadingIndicator(id="loading")
                # Request and response side by side
                with Horizontal(id="panels-container"):
                    yield RequestPanel(id="request-panel")
                    yield ResponsePanel(id="response-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize data on mount."""
        # Load collections and history into sidebar
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_collections(self.storage.load_collections())
        sidebar.update_history(self.storage.load_history())

        # Hide loading indicator initially
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = False

        # Focus the URL input
        try:
            url_bar = self.query_one("#url-bar-widget", UrlBar)
            url_input = url_bar.query_one("#url-input")
            if url_input:
                url_input.focus()
        except Exception:
            pass

    # ── Request Sending ──

    @on(UrlBar.SendRequested)
    def on_url_bar_send(self) -> None:
        """Handle send from URL bar."""
        self.action_send_request()

    @on(UrlBar.MethodChanged)
    def on_method_changed(self, event: UrlBar.MethodChanged) -> None:
        """Update the current request method."""
        self._current_request.method = event.method

    @on(UrlBar.UrlChanged)
    def on_url_changed(self, event: UrlBar.UrlChanged) -> None:
        """Update the current request URL."""
        self._current_request.url = event.url

    def action_send_request(self) -> None:
        """Send the current request."""
        if self._is_sending:
            return

        # Gather data from widgets
        url_bar = self.query_one("#url-bar-widget", UrlBar)
        request_panel = self.query_one("#request-panel", RequestPanel)

        request = request_panel.get_request_data()
        request.method = url_bar.method
        request.url = url_bar.url
        self._current_request = request

        if not request.url.strip():
            self.notify("Please enter a URL", severity="warning", title="Missing URL")
            return

        # Ensure URL has a scheme
        url = request.url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            request.url = url
            url_bar.url = url

        self._do_send(request)

    @work(exclusive=True)
    async def _do_send(self, request: RequestModel) -> None:
        """Actually send the request (in background worker)."""
        self._is_sending = True

        # Show loading
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = True
        response_panel = self.query_one("#response-panel", ResponsePanel)

        # Get environment variables
        active_env = self.storage.get_active_environment()
        variables = active_env.variables if active_env else {}

        try:
            response = await send_request(
                request,
                variables=variables,
                timeout=self.config.timeout,
                verify_ssl=self.config.verify_ssl,
            )

            # Show response
            response_panel.show_response(response)

            # Add to history
            entry = HistoryEntry(request=copy.deepcopy(request), response=response)
            self.storage.append_history(entry)

            self.notify(
                f"{response.status_code} {markup_escape(response.reason)} — {response.elapsed_ms:.0f}ms",
                title="Response Received",
                severity="information",
            )

        except Exception as e:
            error_msg = str(e)
            response_panel.show_error(error_msg)

            # Add error to history
            entry = HistoryEntry(request=copy.deepcopy(request), error=error_msg)
            self.storage.append_history(entry)

            self.notify(
                markup_escape(error_msg[:200]),
                title="Request Failed",
                severity="error",
            )

        finally:
            loading.display = False
            self._is_sending = False

            # Refresh sidebar history
            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.update_history(self.storage.load_history())

    # ── Save Request ──

    def action_save_request(self) -> None:
        """Open save request dialog."""
        url_bar = self.query_one("#url-bar-widget", UrlBar)
        request_panel = self.query_one("#request-panel", RequestPanel)

        request = request_panel.get_request_data()
        request.method = url_bar.method
        request.url = url_bar.url

        modal = SaveRequestModal(request_name=request.display_name())
        self.push_screen(modal, callback=self._on_save_result)

    def _on_save_result(self, result: tuple[str, str] | None) -> None:
        """Handle save modal result."""
        if result is None:
            return

        collection_name, request_name = result

        url_bar = self.query_one("#url-bar-widget", UrlBar)
        request_panel = self.query_one("#request-panel", RequestPanel)

        request = request_panel.get_request_data()
        request.method = url_bar.method
        request.url = url_bar.url
        request.name = request_name or request.display_name()

        saved_request = copy.deepcopy(request)
        self.storage.add_to_collection(collection_name, saved_request)

        # Refresh sidebar
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_collections(self.storage.load_collections())

        self.notify(
            f"Saved to '{collection_name}'",
            title="Request Saved",
            severity="information",
        )

    # ── cURL Import/Export ──

    def action_import_curl(self) -> None:
        """Open cURL import dialog."""
        self.push_screen(CurlImportModal(), callback=self._on_curl_import)

    def _on_curl_import(self, curl_text: str | None) -> None:
        """Handle cURL import result."""
        if not curl_text:
            return

        try:
            request = parse_curl(curl_text)

            # Load into the UI
            url_bar = self.query_one("#url-bar-widget", UrlBar)
            url_bar.method = request.method
            url_bar.url = request.url

            # Rebuild request panel with new data
            request_panel = self.query_one("#request-panel", RequestPanel)
            request_panel.request = request
            request_panel._rebuild()

            self._current_request = request

            self.notify(
                f"Imported {request.method.value} {request.url}",
                title="cURL Imported",
                severity="information",
            )

        except Exception as e:
            self.notify(
                f"Failed to parse cURL: {e}",
                title="Import Error",
                severity="error",
            )

    def action_export_curl(self) -> None:
        """Export current request as cURL."""
        url_bar = self.query_one("#url-bar-widget", UrlBar)
        request_panel = self.query_one("#request-panel", RequestPanel)

        request = request_panel.get_request_data()
        request.method = url_bar.method
        request.url = url_bar.url

        if not request.url.strip():
            self.notify("Enter a URL first", severity="warning", title="No URL")
            return

        active_env = self.storage.get_active_environment()
        variables = active_env.variables if active_env else {}

        curl_cmd = to_curl(request, variables)
        self.push_screen(CurlExportModal(curl_cmd))

    # ── Environments ──

    def action_manage_environments(self) -> None:
        """Open environment management dialog."""
        environments = self.storage.load_environments()
        modal = EnvironmentModal(environments)
        self.push_screen(modal, callback=self._on_env_result)

    def _on_env_result(self, environments: list[Environment] | None) -> None:
        """Handle environment modal close."""
        if environments is not None:
            self.storage.save_environments(environments)
        self._refresh_env_badge()

    def _refresh_env_badge(self) -> None:
        """Update the environment badge display."""
        active_env = self.storage.get_active_environment()
        try:
            badge = self.query_one("#env-badge", Label)
            if active_env:
                badge.update(f"🌍 {active_env.name}")
            else:
                badge.update("No Environment")
        except Exception:
            pass

    # ── Other Actions ──

    def action_clear_response(self) -> None:
        """Clear the response panel."""
        response_panel = self.query_one("#response-panel", ResponsePanel)
        response_panel.clear()

    def action_new_request(self) -> None:
        """Reset to a new empty request."""
        self._current_request = RequestModel()

        url_bar = self.query_one("#url-bar-widget", UrlBar)
        url_bar.method = HttpMethod.GET
        url_bar.url = ""

        request_panel = self.query_one("#request-panel", RequestPanel)
        request_panel.request = RequestModel()
        request_panel._rebuild()

        response_panel = self.query_one("#response-panel", ResponsePanel)
        response_panel.clear()

        self.notify("New request", severity="information")

    # ── Sidebar Events ──

    @on(Sidebar.RequestSelected)
    def on_sidebar_request_selected(self, event: Sidebar.RequestSelected) -> None:
        """Load a request from sidebar selection."""
        request = copy.deepcopy(event.request)
        self._current_request = request

        url_bar = self.query_one("#url-bar-widget", UrlBar)
        url_bar.method = request.method
        url_bar.url = request.url

        request_panel = self.query_one("#request-panel", RequestPanel)
        request_panel.request = request
        request_panel._rebuild()

        response_panel = self.query_one("#response-panel", ResponsePanel)
        response_panel.clear()

        self.notify(
            f"Loaded: {request.display_name()}",
            severity="information",
        )

    @on(Sidebar.HistoryClearRequested)
    def on_history_clear(self) -> None:
        """Clear request history."""
        self.storage.clear_history()
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_history([])
        self.notify("History cleared", severity="information")
