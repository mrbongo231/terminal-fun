"""Modal dialogs for environment management, save, and cURL import."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, TextArea

from reqcraft.models import Environment


class SaveRequestModal(ModalScreen[tuple[str, str] | None]):
    """Modal to save a request to a collection.
    
    Dismisses with (collection_name, request_name) or None if cancelled.
    """

    DEFAULT_CSS = """
    SaveRequestModal {
        align: center middle;
    }
    SaveRequestModal #save-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    SaveRequestModal .modal-title {
        text-style: bold;
        text-align: center;
        padding: 1;
        color: $primary;
    }
    SaveRequestModal Input {
        margin: 1 0;
    }
    SaveRequestModal .btn-row {
        layout: horizontal;
        align: center middle;
        height: 3;
        margin: 1 0 0 0;
    }
    SaveRequestModal .btn-row Button {
        margin: 0 1;
    }
    """

    def __init__(self, request_name: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._request_name = request_name

    def compose(self) -> ComposeResult:
        with Vertical(id="save-dialog"):
            yield Label("💾 Save Request", classes="modal-title")
            yield Label("Request name:")
            yield Input(
                value=self._request_name,
                placeholder="My Request",
                id="save-req-name",
            )
            yield Label("Collection:")
            yield Input(
                placeholder="Default Collection",
                id="save-collection-name",
            )
            with Horizontal(classes="btn-row"):
                yield Button("Save", variant="primary", id="save-confirm")
                yield Button("Cancel", variant="default", id="save-cancel")

    def _do_save(self) -> None:
        col_input = self.query_one("#save-collection-name", Input)
        name_input = self.query_one("#save-req-name", Input)
        col_name = col_input.value.strip() or "Default Collection"
        req_name = name_input.value.strip()
        self.dismiss((col_name, req_name))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-confirm":
            self._do_save()
        elif event.button.id == "save-cancel":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_save()


class CurlImportModal(ModalScreen[str | None]):
    """Modal to import a cURL command."""

    DEFAULT_CSS = """
    CurlImportModal {
        align: center middle;
    }
    CurlImportModal #curl-dialog {
        width: 70;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    CurlImportModal .modal-title {
        text-style: bold;
        text-align: center;
        padding: 1;
        color: $primary;
    }
    CurlImportModal #curl-input {
        height: 10;
        margin: 1 0;
    }
    CurlImportModal .btn-row {
        layout: horizontal;
        align: center middle;
        height: 3;
        margin: 1 0 0 0;
    }
    CurlImportModal .btn-row Button {
        margin: 0 1;
    }
    CurlImportModal .hint-text {
        color: $text-muted;
        padding: 0 0 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="curl-dialog"):
            yield Label("📋 Import cURL Command", classes="modal-title")
            yield Static(
                "Paste a cURL command below to import it as a request:",
                classes="hint-text",
            )
            yield TextArea(
                "",
                id="curl-input",
            )
            with Horizontal(classes="btn-row"):
                yield Button("Import", variant="primary", id="curl-confirm")
                yield Button("Cancel", variant="default", id="curl-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "curl-confirm":
            text_area = self.query_one("#curl-input", TextArea)
            curl_text = text_area.text.strip()
            self.dismiss(curl_text if curl_text else None)
        elif event.button.id == "curl-cancel":
            self.dismiss(None)


class CurlExportModal(ModalScreen[None]):
    """Modal to display the exported cURL command."""

    DEFAULT_CSS = """
    CurlExportModal {
        align: center middle;
    }
    CurlExportModal #curl-export-dialog {
        width: 70;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    CurlExportModal .modal-title {
        text-style: bold;
        text-align: center;
        padding: 1;
        color: $primary;
    }
    CurlExportModal #curl-export-text {
        height: 10;
        margin: 1 0;
    }
    CurlExportModal .btn-row {
        layout: horizontal;
        align: center middle;
        height: 3;
        margin: 1 0 0 0;
    }
    CurlExportModal .btn-row Button {
        margin: 0 1;
    }
    CurlExportModal .hint-text {
        color: $text-muted;
        padding: 0 0 1 0;
    }
    """

    def __init__(self, curl_command: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._curl_command = curl_command

    def compose(self) -> ComposeResult:
        with Vertical(id="curl-export-dialog"):
            yield Label("📤 Export as cURL", classes="modal-title")
            yield Static(
                "Copy the cURL command below:",
                classes="hint-text",
            )
            yield TextArea(
                self._curl_command,
                read_only=True,
                id="curl-export-text",
            )
            with Horizontal(classes="btn-row"):
                yield Button("Close", variant="primary", id="curl-export-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "curl-export-close":
            self.dismiss(None)


class EnvironmentModal(ModalScreen[list[Environment] | None]):
    """Modal for managing environments and their variables.
    
    Dismisses with the updated list of environments, or None if cancelled.
    """

    DEFAULT_CSS = """
    EnvironmentModal {
        align: center middle;
    }
    EnvironmentModal #env-dialog {
        width: 70;
        height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    EnvironmentModal .modal-title {
        text-style: bold;
        text-align: center;
        padding: 1;
        color: $primary;
    }
    EnvironmentModal .env-list {
        height: 1fr;
        padding: 1;
    }
    EnvironmentModal .env-item {
        layout: horizontal;
        height: 3;
        margin: 0 0 1 0;
    }
    EnvironmentModal .env-name {
        width: 1fr;
        margin: 0 1 0 0;
    }
    EnvironmentModal .env-btn {
        width: auto;
        min-width: 8;
        margin: 0 0 0 1;
    }
    EnvironmentModal .btn-row {
        layout: horizontal;
        align: center middle;
        height: 3;
        margin: 1 0 0 0;
        dock: bottom;
    }
    EnvironmentModal .btn-row Button {
        margin: 0 1;
    }
    EnvironmentModal .hint-text {
        color: $text-muted;
        padding: 0 0 1 0;
    }
    EnvironmentModal #env-vars-area {
        height: 1fr;
    }
    """

    def __init__(self, environments: list[Environment], **kwargs) -> None:
        super().__init__(**kwargs)
        self.environments = list(environments)
        self._editing: Environment | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="env-dialog"):
            yield Label("🌍 Environments", classes="modal-title")
            yield Static(
                'Use {{variable}} syntax in URLs, headers, and body.',
                classes="hint-text",
            )
            with VerticalScroll(classes="env-list", id="env-list-scroll"):
                yield Static("No environments yet. Create one!", id="env-empty-msg")
            with Horizontal(classes="btn-row"):
                yield Button("+ New", variant="primary", id="env-new")
                yield Button("Done", variant="success", id="env-close")

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh the environment list in place."""
        try:
            scroll = self.query_one("#env-list-scroll", VerticalScroll)
            scroll.remove_children()

            if not self.environments:
                scroll.mount(Static("No environments yet. Create one!", id="env-empty-msg"))
            else:
                for env in self.environments:
                    active_marker = "✅ " if env.is_active else "   "
                    row = Horizontal(classes="env-item")
                    row.compose_add_child(
                        Static(
                            f"{active_marker}[bold]{env.name}[/] ({len(env.variables)} vars)",
                            markup=True,
                            classes="env-name",
                        )
                    )
                    row.compose_add_child(
                        Button(
                            "Use" if not env.is_active else "Active",
                            variant="success" if not env.is_active else "default",
                            id=f"env-activate-{env.id}",
                            classes="env-btn",
                        )
                    )
                    row.compose_add_child(
                        Button("Edit", variant="primary", id=f"env-edit-{env.id}", classes="env-btn")
                    )
                    row.compose_add_child(
                        Button("✕", variant="error", id=f"env-del-{env.id}", classes="env-btn")
                    )
                    scroll.mount(row)
        except Exception:
            pass

    def _show_editor(self, env: Environment) -> None:
        """Switch to editor view for an environment."""
        self._editing = env
        try:
            scroll = self.query_one("#env-list-scroll", VerticalScroll)
            scroll.remove_children()

            scroll.mount(Label(f"Editing: {env.name}"))
            scroll.mount(Input(value=env.name, placeholder="Environment name", id="env-edit-name"))
            scroll.mount(Static("Variables (KEY=VALUE, one per line):", classes="hint-text"))

            vars_text = "\n".join(f"{k}={v}" for k, v in env.variables.items())
            scroll.mount(TextArea(vars_text, id="env-vars-area"))

            # Replace bottom buttons
            btn_row = self.query_one(".btn-row", Horizontal)
            btn_row.remove_children()
            btn_row.mount(Button("Save", variant="primary", id="env-save"))
            btn_row.mount(Button("Back", variant="default", id="env-back"))
        except Exception:
            pass

    def _show_list(self) -> None:
        """Switch to list view."""
        self._editing = None
        try:
            btn_row = self.query_one(".btn-row", Horizontal)
            btn_row.remove_children()
            btn_row.mount(Button("+ New", variant="primary", id="env-new"))
            btn_row.mount(Button("Done", variant="success", id="env-close"))
        except Exception:
            pass
        self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        if btn_id == "env-close":
            self.dismiss(self.environments)

        elif btn_id == "env-new":
            new_env = Environment(name="New Environment")
            self.environments.append(new_env)
            self._show_editor(new_env)

        elif btn_id.startswith("env-activate-"):
            env_id = btn_id.replace("env-activate-", "")
            for env in self.environments:
                env.is_active = (env.id == env_id)
            self._refresh_list()

        elif btn_id.startswith("env-edit-"):
            env_id = btn_id.replace("env-edit-", "")
            for env in self.environments:
                if env.id == env_id:
                    self._show_editor(env)
                    break

        elif btn_id.startswith("env-del-"):
            env_id = btn_id.replace("env-del-", "")
            self.environments = [e for e in self.environments if e.id != env_id]
            self._refresh_list()

        elif btn_id == "env-save":
            if self._editing:
                try:
                    name_input = self.query_one("#env-edit-name", Input)
                    self._editing.name = name_input.value.strip() or "Unnamed"
                except Exception:
                    pass
                try:
                    vars_area = self.query_one("#env-vars-area", TextArea)
                    variables: dict[str, str] = {}
                    for line in vars_area.text.strip().split("\n"):
                        line = line.strip()
                        if "=" in line:
                            k, _, v = line.partition("=")
                            k = k.strip()
                            if k:
                                variables[k] = v.strip()
                    self._editing.variables = variables
                except Exception:
                    pass
            self._show_list()

        elif btn_id == "env-back":
            self._show_list()
