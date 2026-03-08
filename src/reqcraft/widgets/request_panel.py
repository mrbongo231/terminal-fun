"""Request panel widget with tabs for params, headers, body, and auth."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import (
    Button,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from reqcraft.models import (
    AuthConfig,
    AuthType,
    BodyType,
    KeyValuePair,
    RequestModel,
)


class KeyValueRow(Widget):
    """A single key-value pair row with enable toggle and delete button."""

    DEFAULT_CSS = """
    KeyValueRow {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }
    KeyValueRow .kv-key {
        width: 1fr;
        margin: 0 1 0 0;
    }
    KeyValueRow .kv-value {
        width: 1fr;
        margin: 0 1 0 0;
    }
    KeyValueRow .kv-delete-btn {
        width: 5;
        min-width: 5;
    }
    """

    def __init__(self, kv: KeyValuePair, index: int, prefix: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.kv = kv
        self.index = index
        self.prefix = prefix

    def compose(self) -> ComposeResult:
        yield Input(
            value=self.kv.key,
            placeholder="Key",
            classes="kv-key",
            id=f"{self.prefix}-key-{self.index}",
        )
        yield Input(
            value=self.kv.value,
            placeholder="Value",
            classes="kv-value",
            id=f"{self.prefix}-val-{self.index}",
        )
        yield Button("✕", variant="error", classes="kv-delete-btn",
                      id=f"{self.prefix}-del-{self.index}")


class KeyValueEditor(Widget):
    """A list of key-value pair rows with add/delete."""

    DEFAULT_CSS = """
    KeyValueEditor {
        height: 1fr;
        padding: 1;
    }
    KeyValueEditor #kv-scroll {
        height: 1fr;
    }
    KeyValueEditor #kv-add-btn {
        dock: bottom;
        margin: 1 0 0 0;
        width: 100%;
    }
    """

    def __init__(self, pairs: list[KeyValuePair], prefix: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.pairs = list(pairs)
        self.prefix = prefix

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="kv-scroll"):
            if not self.pairs:
                yield Static("No entries. Click + to add one.", classes="empty-state")
            for i, kv in enumerate(self.pairs):
                yield KeyValueRow(kv, i, self.prefix)
        yield Button("+ Add", variant="primary", id="kv-add-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "kv-add-btn":
            new_kv = KeyValuePair()
            self.pairs.append(new_kv)
            scroll = self.query_one("#kv-scroll", VerticalScroll)
            # Remove empty state if present
            for empty in scroll.query(".empty-state"):
                empty.remove()
            new_row = KeyValueRow(new_kv, len(self.pairs) - 1, self.prefix)
            scroll.mount(new_row)
        elif event.button.id and event.button.id.startswith(f"{self.prefix}-del-"):
            idx = int(event.button.id.split("-")[-1])
            if 0 <= idx < len(self.pairs):
                self.pairs.pop(idx)
                self._rebuild()

    def on_input_changed(self, event: Input.Changed) -> None:
        input_id = event.input.id or ""
        if input_id.startswith(f"{self.prefix}-key-"):
            idx = int(input_id.split("-")[-1])
            if 0 <= idx < len(self.pairs):
                self.pairs[idx].key = event.value
        elif input_id.startswith(f"{self.prefix}-val-"):
            idx = int(input_id.split("-")[-1])
            if 0 <= idx < len(self.pairs):
                self.pairs[idx].value = event.value

    def _rebuild(self) -> None:
        """Rebuild all rows after a deletion."""
        scroll = self.query_one("#kv-scroll", VerticalScroll)
        scroll.remove_children()
        if not self.pairs:
            scroll.mount(Static("No entries. Click + to add one.", classes="empty-state"))
        else:
            for i, kv in enumerate(self.pairs):
                scroll.mount(KeyValueRow(kv, i, self.prefix))

    def get_pairs(self) -> list[KeyValuePair]:
        """Get current key-value pairs."""
        return list(self.pairs)


class RequestPanel(Widget):
    """Tabbed request configuration panel."""

    DEFAULT_CSS = """
    RequestPanel {
        height: 1fr;
    }
    RequestPanel .auth-form {
        padding: 1;
        height: auto;
    }
    RequestPanel .auth-form Label {
        margin: 1 0 0 0;
    }
    RequestPanel .auth-form Input {
        margin: 0 0 1 0;
    }
    RequestPanel .body-type-bar {
        height: 3;
        dock: top;
        padding: 0 1;
    }
    RequestPanel #body-editor {
        height: 1fr;
    }
    """

    def __init__(self, request: RequestModel | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.request = request or RequestModel()

    def compose(self) -> ComposeResult:
        with TabbedContent("Params", "Headers", "Body", "Auth", id="request-tabs"):
            with TabPane("Params", id="tab-params"):
                yield KeyValueEditor(
                    self.request.params, prefix="param"
                )
            with TabPane("Headers", id="tab-headers"):
                yield KeyValueEditor(
                    self.request.headers, prefix="header"
                )
            with TabPane("Body", id="tab-body"):
                with Vertical():
                    with Horizontal(classes="body-type-bar"):
                        yield Select(
                            [
                                ("None", BodyType.NONE),
                                ("JSON", BodyType.JSON),
                                ("Form", BodyType.FORM),
                                ("Raw", BodyType.RAW),
                            ],
                            value=self.request.body_type,
                            id="body-type-select",
                            allow_blank=False,
                        )
                    yield TextArea(
                        self.request.body,
                        language="json",
                        id="body-editor",
                    )
            with TabPane("Auth", id="tab-auth"):
                with VerticalScroll(classes="auth-form"):
                    yield Select(
                        [
                            ("No Auth", AuthType.NONE),
                            ("Basic Auth", AuthType.BASIC),
                            ("Bearer Token", AuthType.BEARER),
                            ("API Key", AuthType.API_KEY),
                        ],
                        value=self.request.auth.auth_type,
                        id="auth-type-select",
                        allow_blank=False,
                    )
                    # Basic auth fields
                    yield Label("Username", id="basic-user-label")
                    yield Input(
                        value=self.request.auth.username,
                        placeholder="Username",
                        id="auth-username",
                    )
                    yield Label("Password", id="basic-pass-label")
                    yield Input(
                        value=self.request.auth.password,
                        placeholder="Password",
                        id="auth-password",
                        password=True,
                    )
                    # Bearer token
                    yield Label("Token", id="bearer-label")
                    yield Input(
                        value=self.request.auth.token,
                        placeholder="Bearer token",
                        id="auth-token",
                    )
                    # API Key
                    yield Label("Key Name", id="apikey-name-label")
                    yield Input(
                        value=self.request.auth.api_key_name,
                        placeholder="e.g., X-API-Key",
                        id="auth-apikey-name",
                    )
                    yield Label("Key Value", id="apikey-value-label")
                    yield Input(
                        value=self.request.auth.api_key_value,
                        placeholder="Your API key",
                        id="auth-apikey-value",
                    )
                    yield Label("Add to", id="apikey-in-label")
                    yield Select(
                        [("Header", "header"), ("Query Param", "query")],
                        value=self.request.auth.api_key_in,
                        id="auth-apikey-in",
                        allow_blank=False,
                    )

    def get_request_data(self) -> RequestModel:
        """Collect all current form data into a RequestModel."""
        # Params
        try:
            param_editor = self.query_one("#tab-params KeyValueEditor", KeyValueEditor)
            params = param_editor.get_pairs()
        except Exception:
            params = []

        # Headers
        try:
            header_editor = self.query_one("#tab-headers KeyValueEditor", KeyValueEditor)
            headers = header_editor.get_pairs()
        except Exception:
            headers = []

        # Body
        try:
            body_type_sel = self.query_one("#body-type-select", Select)
            body_type = body_type_sel.value if body_type_sel.value is not Select.BLANK else BodyType.NONE
        except Exception:
            body_type = BodyType.NONE

        try:
            body_editor = self.query_one("#body-editor", TextArea)
            body = body_editor.text
        except Exception:
            body = ""

        # Auth
        try:
            auth_type_sel = self.query_one("#auth-type-select", Select)
            auth_type = auth_type_sel.value if auth_type_sel.value is not Select.BLANK else AuthType.NONE
        except Exception:
            auth_type = AuthType.NONE

        auth = AuthConfig(auth_type=auth_type)

        try:
            auth.username = self.query_one("#auth-username", Input).value
            auth.password = self.query_one("#auth-password", Input).value
            auth.token = self.query_one("#auth-token", Input).value
            auth.api_key_name = self.query_one("#auth-apikey-name", Input).value
            auth.api_key_value = self.query_one("#auth-apikey-value", Input).value
            apikey_in_sel = self.query_one("#auth-apikey-in", Select)
            auth.api_key_in = apikey_in_sel.value if apikey_in_sel.value is not Select.BLANK else "header"
        except Exception:
            pass

        self.request.params = params
        self.request.headers = headers
        self.request.body_type = body_type
        self.request.body = body
        self.request.auth = auth

        return self.request

    def load_request(self, request: RequestModel) -> None:
        """Load a request model into the panel fields."""
        self.request = request
        self._rebuild()

    def _rebuild(self) -> None:
        """Schedule a full rebuild of this widget."""
        self.recompose()
