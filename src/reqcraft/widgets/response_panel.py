"""Response panel widget with syntax-highlighted body, headers, and timing."""

from __future__ import annotations

import json
from datetime import datetime

from rich.markup import escape as markup_escape
from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import (
    Label,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from reqcraft.models import ResponseModel


class ResponsePanel(Widget):
    """Displays HTTP response with tabs for body, headers, and timing.
    
    Strategy: compose the full UI once, then update widget values in-place.
    """

    DEFAULT_CSS = """
    ResponsePanel {
        height: 1fr;
    }
    ResponsePanel #response-status-bar {
        height: 1;
        layout: horizontal;
        padding: 0 1;
        background: $surface-darken-1;
    }
    ResponsePanel .status-badge {
        text-style: bold;
        margin: 0 1 0 0;
    }
    ResponsePanel .status-2xx {
        color: #22c55e;
    }
    ResponsePanel .status-3xx {
        color: #60a5fa;
    }
    ResponsePanel .status-4xx {
        color: #f59e0b;
    }
    ResponsePanel .status-5xx {
        color: #ef4444;
    }
    ResponsePanel .response-meta {
        color: $text-muted;
        margin: 0 1;
    }
    ResponsePanel .empty-response {
        text-align: center;
        color: $text-muted;
        padding: 4 2;
        height: 1fr;
    }
    ResponsePanel #response-body-area {
        height: 1fr;
    }
    ResponsePanel .headers-scroll {
        padding: 1;
        height: 1fr;
    }
    ResponsePanel .info-scroll {
        padding: 1;
        height: 1fr;
    }
    ResponsePanel .error-display {
        color: #ef4444;
        text-style: bold;
        padding: 2;
        text-align: center;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.response: ResponseModel | None = None
        self._error: str | None = None

    def compose(self) -> ComposeResult:
        # Empty state shown by default
        yield Static(
            "✨ Send a request to see the response here\n\n"
            "Press Ctrl+Enter or click Send",
            id="empty-msg",
            classes="empty-response",
        )
        # Error display, hidden initially — markup=False so raw error text is safe
        yield Static("", id="error-msg", classes="error-display", markup=False)
        # Status bar, hidden initially
        with Horizontal(id="response-status-bar"):
            yield Label("", id="status-badge", classes="status-badge")
            yield Label("", id="timing-label", classes="response-meta")
            yield Label("", id="size-label", classes="response-meta")
        # Tabs, hidden initially
        with TabbedContent("Body", "Headers", "Info", id="response-tabs"):
            with TabPane("Body", id="resp-tab-body"):
                yield TextArea(
                    "",
                    read_only=True,
                    id="response-body-area",
                )
            with TabPane("Headers", id="resp-tab-headers"):
                # markup=False so header values with [ ] don't break
                with VerticalScroll(classes="headers-scroll"):
                    yield Static("No headers", id="headers-content", markup=False)
            with TabPane("Info", id="resp-tab-info"):
                with VerticalScroll(classes="info-scroll"):
                    yield Static("No info", id="info-content", markup=False)

    def on_mount(self) -> None:
        """Hide the response UI initially, show empty state."""
        self._show_empty_state()

    def _show_empty_state(self) -> None:
        """Show empty state, hide everything else."""
        self.query_one("#empty-msg").display = True
        self.query_one("#error-msg").display = False
        self.query_one("#response-status-bar").display = False
        self.query_one("#response-tabs").display = False

    def show_response(self, response: ResponseModel) -> None:
        """Display a response by updating widget values in-place."""
        self.response = response
        self._error = None

        # Hide empty + error, show status bar and tabs
        self.query_one("#empty-msg").display = False
        self.query_one("#error-msg").display = False
        self.query_one("#response-status-bar").display = True
        self.query_one("#response-tabs").display = True

        resp = response

        # Update status bar — use plain text, no markup
        badge = self.query_one("#status-badge", Label)
        badge.update(f" {resp.status_code} {resp.reason} ")
        badge.set_classes(f"status-badge {resp.status_class}")

        self.query_one("#timing-label", Label).update(
            f"⏱ {resp.elapsed_ms:.0f}ms"
        )
        self.query_one("#size-label", Label).update(
            f"📦 {resp.formatted_size}"
        )

        # Update body — TextArea doesn't use markup, so this is safe
        body_text = self._format_body(resp.body, resp.content_type)
        body_area = self.query_one("#response-body-area", TextArea)
        body_area.load_text(body_text)

        lang = self._detect_language(resp.content_type)
        if lang:
            try:
                body_area.language = lang
            except Exception:
                pass

        # Update headers — plain text, no markup
        headers_widget = self.query_one("#headers-content", Static)
        if resp.headers:
            header_lines = []
            for key, value in resp.headers.items():
                header_lines.append(f"{key}: {value}")
            headers_widget.update("\n".join(header_lines))
        else:
            headers_widget.update("No headers")

        # Update info — plain text, no markup
        ts = datetime.fromtimestamp(resp.timestamp)
        info_lines = [
            f"Status:       {resp.status_code} {resp.reason}",
            f"Time:         {resp.elapsed_ms:.2f}ms",
            f"Size:         {resp.formatted_size}",
            f"Content-Type: {resp.content_type}",
            f"Timestamp:    {ts.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        info_widget = self.query_one("#info-content", Static)
        info_widget.update("\n".join(info_lines))

    def show_error(self, error: str) -> None:
        """Display an error message."""
        self._error = error
        self.response = None

        self.query_one("#empty-msg").display = False
        self.query_one("#error-msg").display = True
        self.query_one("#response-status-bar").display = False
        self.query_one("#response-tabs").display = False

        # Static has markup=False, so raw error text is safe
        self.query_one("#error-msg", Static).update(f"❌ Error: {error}")

    def clear(self) -> None:
        """Clear the response panel."""
        self.response = None
        self._error = None
        self._show_empty_state()
        try:
            self.query_one("#response-body-area", TextArea).load_text("")
        except Exception:
            pass

    def _format_body(self, body: str, content_type: str) -> str:
        """Pretty-format the response body based on content type."""
        if not body:
            return "(empty response body)"

        if "json" in content_type.lower():
            try:
                parsed = json.loads(body)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                return body

        return body

    def _detect_language(self, content_type: str) -> str | None:
        """Detect TextArea language from content type."""
        ct = content_type.lower()
        if "json" in ct:
            return "json"
        elif "html" in ct:
            return "html"
        elif "xml" in ct:
            return "xml"
        elif "css" in ct:
            return "css"
        elif "javascript" in ct or "ecmascript" in ct:
            return "javascript"
        elif "yaml" in ct or "yml" in ct:
            return "yaml"
        return None
