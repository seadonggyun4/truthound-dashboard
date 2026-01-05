"""CLI entry point for truthound-dashboard.

This module provides the command-line interface using Typer.
It supports both standalone usage and integration with the
truthound CLI plugin system.

Example:
    # Standalone usage
    truthound-dashboard serve --port 8765

    # Via truthound CLI plugin
    truthound serve --port 8765
"""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from truthound_dashboard import __version__

app = typer.Typer(
    name="truthound-dashboard",
    help="Open-source data quality dashboard - GX Cloud alternative",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"truthound-dashboard version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Truthound Dashboard - Open-source data quality monitoring."""
    pass


@app.command()
def serve(
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port to run server on", min=1, max=65535),
    ] = 8765,
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Host to bind server to"),
    ] = "127.0.0.1",
    data_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--data-dir",
            "-d",
            help="Data directory for database and cache",
            exists=False,
            file_okay=False,
            resolve_path=True,
        ),
    ] = None,
    no_browser: Annotated[
        bool,
        typer.Option("--no-browser", help="Don't open browser automatically"),
    ] = False,
    reload: Annotated[
        bool,
        typer.Option("--reload", help="Enable hot reload for development"),
    ] = False,
    log_level: Annotated[
        str,
        typer.Option(
            "--log-level",
            "-l",
            help="Logging level",
            case_sensitive=False,
        ),
    ] = "warning",
) -> None:
    """Start the truthound dashboard server.

    This command starts the FastAPI server and optionally opens
    the dashboard in your default browser.

    Examples:
        truthound serve
        truthound serve --port 9000
        truthound serve --reload --log-level debug
    """
    import uvicorn

    from truthound_dashboard.config import get_settings, reset_settings

    # Reset settings cache to pick up any CLI overrides
    reset_settings()
    settings = get_settings()

    # Override settings from CLI arguments
    if data_dir:
        settings.data_dir = data_dir

    # Ensure directories exist
    settings.ensure_directories()

    # Display startup info
    url = f"http://{host}:{port}"
    console.print(
        Panel(
            f"[bold]Truthound Dashboard v{__version__}[/bold]\n\n"
            f"[green]✓[/green] Database: {settings.database_path}\n"
            f"[green]✓[/green] Server: {url}\n"
            f"[green]✓[/green] API Docs: {url}/docs",
            title="Starting Dashboard",
            border_style="bright_blue",
        )
    )

    # Open browser
    if not no_browser:
        webbrowser.open(url)
        console.print("[dim]Opening browser...[/dim]")

    # Configure and run server
    uvicorn.run(
        "truthound_dashboard.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
        access_log=log_level.lower() == "debug",
    )


@app.command()
def info() -> None:
    """Show dashboard configuration and status."""
    from truthound_dashboard.config import get_settings

    settings = get_settings()
    settings.ensure_directories()

    console.print(
        Panel(
            f"[bold]Configuration[/bold]\n\n"
            f"Data Directory: {settings.data_dir}\n"
            f"Database: {settings.database_path}\n"
            f"Cache: {settings.cache_dir}\n"
            f"Schemas: {settings.schema_dir}\n\n"
            f"[bold]Server Defaults[/bold]\n\n"
            f"Host: {settings.host}\n"
            f"Port: {settings.port}\n"
            f"Auth Enabled: {settings.auth_enabled}\n\n"
            f"[bold]Validation Defaults[/bold]\n\n"
            f"Sample Size: {settings.sample_size:,}\n"
            f"Max Failed Rows: {settings.max_failed_rows:,}\n"
            f"Timeout: {settings.default_timeout}s",
            title=f"Truthound Dashboard v{__version__}",
            border_style="bright_blue",
        )
    )


def register_commands(typer_app: typer.Typer) -> None:
    """Register commands with truthound CLI plugin system.

    This function is called by the truthound CLI when the
    dashboard plugin is discovered via entry points.

    Args:
        typer_app: The parent typer application to register commands with.
    """

    @typer_app.command(name="serve")
    def serve_dashboard(
        port: Annotated[
            int,
            typer.Option("--port", "-p", help="Port to run on"),
        ] = 8765,
        host: Annotated[
            str,
            typer.Option("--host", help="Host to bind"),
        ] = "127.0.0.1",
        data_dir: Annotated[
            Optional[Path],
            typer.Option("--data-dir", "-d", help="Data directory path"),
        ] = None,
        no_browser: Annotated[
            bool,
            typer.Option("--no-browser", help="Don't open browser automatically"),
        ] = False,
        reload: Annotated[
            bool,
            typer.Option("--reload", help="Enable hot reload for development"),
        ] = False,
    ) -> None:
        """Start the truthound dashboard server."""
        serve(
            port=port,
            host=host,
            data_dir=data_dir,
            no_browser=no_browser,
            reload=reload,
        )


if __name__ == "__main__":
    app()
