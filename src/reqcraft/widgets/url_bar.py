"""URL bar widget with method selector, URL input, and send button."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Select

from reqcraft.models import HttpMethod


# Method options with color indicators
METHOD_OPTIONS = [
    (method.value, method)
    for method in HttpMethod
]


class UrlBar(Widget):
    """Horizontal bar with: [Method ▼] [URL input] [Send]."""

    class SendRequested(Message):
        """Fired when the user presses Send or Ctrl+Enter."""

    class MethodChanged(Message):
        """Fired when the HTTP method changes."""
        def __init__(self, method: HttpMethod) -> None:
            super().__init__()
            self.method = method

    class UrlChanged(Message):
        """Fired when the URL text changes."""
        def __init__(self, url: str) -> None:
            super().__init__()
            self.url = url

    def __init__(
        self,
        method: HttpMethod = HttpMethod.GET,
        url: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._method = method
        self._url = url

    def compose(self) -> ComposeResult:
        with Horizontal(id="url-bar"):
            yield Select(
                METHOD_OPTIONS,
                value=self._method,
                id="method-select",
                allow_blank=False,
            )
            yield Input(
                value=self._url,
                placeholder="Enter URL (e.g., https://api.example.com/users)",
                id="url-input",
            )
            yield Button("Send", variant="success", id="send-button")

    @property
    def method(self) -> HttpMethod:
        return self._method

    @method.setter
    def method(self, value: HttpMethod) -> None:
        self._method = value
        try:
            self.query_one("#method-select", Select).value = value
        except Exception:
            pass

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = value
        try:
            self.query_one("#url-input", Input).value = value
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-button":
            self.post_message(self.SendRequested())

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "method-select" and event.value is not Select.BLANK:
            self._method = event.value
            self.post_message(self.MethodChanged(self._method))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "url-input":
            self._url = event.value
            self.post_message(self.UrlChanged(self._url))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "url-input":
            self.post_message(self.SendRequested())
