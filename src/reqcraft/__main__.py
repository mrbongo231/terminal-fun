"""ReqCraft — CLI entry point."""

from __future__ import annotations

import sys

import click

from reqcraft import __app_name__, __version__


@click.command()
@click.version_option(version=__version__, prog_name=__app_name__)
@click.option(
    "--theme",
    type=click.Choice(["dark", "light"]),
    default=None,
    help="Color theme (default: from config or 'dark').",
)
@click.option(
    "--timeout",
    type=float,
    default=None,
    help="Default request timeout in seconds (default: 30).",
)
def main(theme: str | None, timeout: float | None) -> None:
    """ReqCraft — Interactive API Testing Client for the Terminal.

    A full-featured, keyboard-driven HTTP client with collections,
    environments, cURL import/export, and a beautiful TUI.

    \b
    Keyboard shortcuts:
      Ctrl+Enter  Send request
      Ctrl+S      Save to collection
      Ctrl+I      Import cURL
      Ctrl+X      Export as cURL
      Ctrl+E      Manage environments
      Ctrl+N      New request
      Ctrl+Q      Quit
    """
    from reqcraft.app import ReqCraftApp
    from reqcraft.config import AppConfig

    config = AppConfig.load()

    if theme:
        config.theme = theme
    if timeout:
        config.timeout = timeout

    app = ReqCraftApp(config=config)

    if config.theme == "light":
        app.theme = "textual-light"
    else:
        app.theme = "textual-dark"

    app.run()


if __name__ == "__main__":
    main()
