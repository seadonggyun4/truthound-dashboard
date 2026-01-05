"""FastAPI application entry point.

This module defines the main FastAPI application with all middleware,
routers, and lifecycle management.

The application serves both the API and the React SPA static files.

Example:
    # Run with uvicorn
    uvicorn truthound_dashboard.main:app --reload

    # Or via CLI
    truthound serve --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from truthound_dashboard import __version__
from truthound_dashboard.api.router import api_router
from truthound_dashboard.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database tables
    - Shutdown: Cleanup resources

    Args:
        app: FastAPI application instance.

    Yields:
        None during application runtime.
    """
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    This factory function creates a fully configured FastAPI app
    with all middleware, routes, and static file handling.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Truthound Dashboard",
        description="Open-source data quality dashboard - GX Cloud alternative",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/openapi.json",
    )

    # Configure CORS
    configure_cors(app)

    # Register exception handlers
    register_exception_handlers(app)

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Mount static files for React SPA
    mount_static_files(app)

    return app


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware.

    Allows requests from the Vite dev server during development.

    Args:
        app: FastAPI application.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:8765",  # Dashboard server
            "http://127.0.0.1:8765",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers.

    Args:
        app: FastAPI application.
    """

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError as 400 Bad Request."""
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(
        request: Request, exc: FileNotFoundError
    ) -> JSONResponse:
        """Handle FileNotFoundError as 404 Not Found."""
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )


def mount_static_files(app: FastAPI) -> None:
    """Mount static files for React SPA.

    Serves the built React application from the static directory.
    Falls back to index.html for SPA routing.

    Args:
        app: FastAPI application.
    """
    static_dir = Path(__file__).parent / "static"

    if not static_dir.exists():
        return

    index_file = static_dir / "index.html"
    if not index_file.exists():
        return

    # Mount assets directory
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="assets",
        )

    # SPA fallback route - must be last
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve SPA for all non-API routes.

        Args:
            full_path: Requested path.

        Returns:
            Static file or index.html for SPA routing.
        """
        # Check if it's a static file
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Fall back to index.html for SPA routing
        return FileResponse(index_file)


# Create app instance
app = create_app()
