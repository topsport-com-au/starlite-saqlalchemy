"""Application startup script."""
import uvicorn

from starlite_saqlalchemy import settings


def determine_should_reload() -> bool:
    """Evaluate whether reloading should be enabled."""
    return (
        settings.server.RELOAD
        if settings.server.RELOAD is not None
        else settings.app.ENVIRONMENT == "local"
    )


def determine_reload_dirs(should_reload: bool) -> list[str] | None:
    """

    Args:
        should_reload: is reloading enabled?

    Returns:
        List of directories to watch, or `None` if reloading disabled.
    """
    return settings.server.RELOAD_DIRS if should_reload else None


def run_app() -> None:
    """Run the application with config via environment."""
    should_reload = determine_should_reload()
    reload_dirs = determine_reload_dirs(should_reload)
    uvicorn.run(
        app=settings.server.APP_LOC,
        factory=settings.server.APP_LOC_IS_FACTORY,
        host=settings.server.HOST,
        loop="auto",
        port=settings.server.PORT,
        reload=should_reload,
        reload_dirs=reload_dirs,
        timeout_keep_alive=settings.server.KEEPALIVE,
    )
