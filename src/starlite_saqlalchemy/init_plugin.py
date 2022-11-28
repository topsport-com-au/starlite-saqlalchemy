"""The application configuration plugin and config object.

Example:
    ```python
    from starlite import Starlite, get

    from starlite_saqlalchemy import ConfigureApp


    @get("/example")
    def example_handler() -> dict:
        return {"hello": "world"}


    app = Starlite(route_handlers=[example_handler], on_app_init=[ConfigureApp()])
    ```

The plugin can be configured by passing an instance of `PluginConfig` to `ConfigureApp` on
instantiation:

    ```python
    app = Starlite(
        route_handlers=[example_handler],
        on_app_init[ConfigureApp(PluginConfig(do_openapi=False))],
    )
    ```

The `PluginConfig` has switches to disable every aspect of the plugin behavior.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel
from starlite.app import DEFAULT_CACHE_CONFIG, DEFAULT_OPENAPI_CONFIG
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin
from starlite.response import Response

from starlite_saqlalchemy import (
    cache,
    compression,
    dependencies,
    exceptions,
    http,
    log,
    openapi,
    redis,
    sentry,
    settings,
    sqlalchemy_plugin,
)
from starlite_saqlalchemy.health import health_check
from starlite_saqlalchemy.repository.exceptions import RepositoryException
from starlite_saqlalchemy.serializer import default_serializer
from starlite_saqlalchemy.service import ServiceException, make_service_callback
from starlite_saqlalchemy.worker import create_worker_instance

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any

    from starlite.config.app import AppConfig
    from structlog.types import Processor

T = TypeVar("T")


class PluginConfig(BaseModel):
    """Configure behavior of the `ConfigureApp` object.

    Each feature that the plugin enables can be toggled with the
    `do_<behavior>` switch, e.g.,
    `PluginConfig(do_after_exception=False)` will tell `ConfigureApp`
    not to add the after exception logging hook handler to the
    application.
    """

    worker_functions: list[Callable[..., Any] | tuple[str, Callable[..., Any]]] = [
        (make_service_callback.__qualname__, make_service_callback)
    ]
    """
    Queue worker functions.
    """
    do_after_exception: bool = True
    """
    Add the hook handler to
    [`AppConfig.after_exception`][starlite.config.app.AppConfig.after_exception].
    """
    do_cache: bool = True
    """
    Add configuration for the redis-backed cache to
    [`AppConfig.cache_config`][starlite.config.app.AppConfig.cache_config].
    """
    do_compression: bool = True
    """
    Add configuration for gzip compression to
    [`AppConfig.compression_config`][starlite.config.app.AppConfig.compression_config].
    """
    do_collection_dependencies = True
    """
    Add the [`Provide`][starlite.datastructures.Provide]'s for collection route dependencies to
    [`AppConfig.dependencies`][starlite.config.app.AppConfig.dependencies].
    """
    do_exception_handlers: bool = True
    """
    Add the repository/service exception http translation handlers to
    [`AppConfig.exception_handlers`][starlite.config.app.AppConfig.exception_handlers].
    """
    do_health_check: bool = True
    """
    Add the health check controller to
    [`AppConfig.route_handlers`][starlite.config.app.AppConfig.route_handlers].
    """
    do_logging: bool = True
    """
    Set the logging configuration object to
    [`AppConfig.logging_config`][starlite.config.app.AppConfig.logging_config].
    """
    do_openapi: bool = True
    """
    Set the OpenAPI config object to
    [`AppConfig.openapi_config`][starlite.config.app.AppConfig.openapi_config].
    """
    do_response_class: bool = True
    """
    Set the custom response class to
    [`AppConfig.response_class`][starlite.config.app.AppConfig.response_class].
    """
    do_sentry: bool = True
    """
    Configure the application to initialize Sentry on startup. Adds a handler to
    [`AppConfig.on_startup`][starlite.config.app.AppConfig.on_startup].
    """
    do_set_debug: bool = True
    """
    Allow the plugin to set the starlite `debug` parameter. Parameter set to value of
    [`AppConfig.debug`][starlite_saqlalchemy.settings.AppSettings.DEBUG].
    """
    do_sqlalchemy_plugin: bool = True
    """
    Set the SQLAlchemy plugin on the application. Adds the plugin to
    [`AppConfig.plugins`][starlite.config.app.AppConfig.plugins].
    """
    do_worker: bool = True
    """
    Configure the async worker on the application. This action instantiates a worker instance and
    sets handlers for [`AppConfig.on_startup`][starlite.config.app.AppConfig.on_startup] and
    [`AppConfig.on_shutdown`][starlite.config.app.AppConfig.on_shutdown] that manage the lifecycle
    of the `SAQ` worker.
    """
    serializer: Callable[[Any], Any] = default_serializer
    """
    The serializer callable that is used by the custom [`Response`][starlite.response.Response]
    class that is created.
    If [`AppConfig.response_class`][starlite.config.app.AppConfig.response_class] is not `None`,
    this is ignored.
    If
    [`PluginConfig.do_response_class`][starlite_saqlalchemy.init_plugin.PluginConfig.do_response_class]
    is `False`, this is ignored.
    """
    # the addition of the health check filter processor makes mypy think `log.default_processors` is
    # list[object].. seems typed correctly to me :/
    log_processors: Sequence[Processor] = log.default_processors  # type:ignore[assignment]
    """Chain of structlog log processors."""


class ConfigureApp:
    """Starlite application configuration."""

    __slots__ = ("config",)

    def __init__(self, config: PluginConfig = PluginConfig()) -> None:
        """
        Args:
            config: Plugin configuration object.
        """
        self.config = config

    def __call__(self, app_config: AppConfig) -> AppConfig:
        """Entrypoint to the app config plugin.

        Receives the [`AppConfig`][starlite.config.app.AppConfig] object and modifies it.

        Args:
            app_config: Passed to the plugin from the Starlite instance on instantiation.

        Returns:
            The modified [`AppConfig`][starlite.config.app.AppConfig] object.
        """
        self.configure_after_exception(app_config)
        self.configure_cache(app_config)
        self.configure_collection_dependencies(app_config)
        self.configure_compression(app_config)
        self.configure_debug(app_config)
        self.configure_exception_handlers(app_config)
        self.configure_health_check(app_config)
        self.configure_logging(app_config)
        self.configure_openapi(app_config)
        self.configure_response_class(app_config)
        self.configure_sentry(app_config)
        self.configure_sqlalchemy_plugin(app_config)
        self.configure_worker(app_config)

        app_config.on_shutdown.extend([http.Client.close, redis.client.close])
        return app_config

    def configure_after_exception(self, app_config: AppConfig) -> None:
        """Add the logging after exception hook handler.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_after_exception:
            app_config.after_exception = self._ensure_list(app_config.after_exception)
            app_config.after_exception.append(exceptions.after_exception_hook_handler)

    def configure_cache(self, app_config: AppConfig) -> None:
        """Configure the application cache.

        We only overwrite if [`DEFAULT_CACHE_CONFIG`][starlite.app.DEFAULT_CACHE_CONFIG] is the
        standing configuration object.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_cache and app_config.cache_config == DEFAULT_CACHE_CONFIG:
            app_config.cache_config = cache.config

    def configure_collection_dependencies(self, app_config: AppConfig) -> None:
        """Add the required [`Provide`][starlite.datastructures.Provide]
        instances to the app dependency mapping.

        If a dependency has already been provided with the same key we do not overwrite it.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_collection_dependencies:
            for key, value in dependencies.create_collection_dependencies().items():
                app_config.dependencies.setdefault(key, value)

    def configure_compression(self, app_config: AppConfig) -> None:
        """Configure application compression.

        No-op if [`AppConfig.compression_config`][starlite.config.app.AppConfig.compression_config]
        has already been set.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_compression and app_config.compression_config is None:
            app_config.compression_config = compression.config

    def configure_debug(self, app_config: AppConfig) -> None:
        """Set Starlite's `debug` parameter.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_set_debug:
            app_config.debug = settings.app.DEBUG

    def configure_exception_handlers(self, app_config: AppConfig) -> None:
        """Add the handlers that translate service and repository exceptions
        into HTTP exceptions.

        Does not overwrite handlers that may already exist for the exception types.

        Args:
            app_config: The Starlite application config object.
        """
        if not self.config.do_exception_handlers:
            return

        app_config.exception_handlers.setdefault(
            RepositoryException, exceptions.repository_exception_to_http_response
        )
        app_config.exception_handlers.setdefault(
            ServiceException, exceptions.service_exception_to_http_response
        )

    def configure_health_check(self, app_config: AppConfig) -> None:
        """Add health check controller.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_health_check:
            app_config.route_handlers.append(health_check)

    def configure_logging(self, app_config: AppConfig) -> None:
        """Configure application logging.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_logging and app_config.logging_config is None:
            app_config.on_startup.append(lambda: log.configure(self.config.log_processors))
            app_config.logging_config = log.config
            app_config.middleware.append(log.controller.middleware_factory)
            app_config.before_send = self._ensure_list(app_config.before_send)
            app_config.before_send.append(log.controller.BeforeSendHandler())

    def configure_openapi(self, app_config: AppConfig) -> None:
        """Configure the OpenAPI docs.

        We only overwrite if `DEFAULT_OPENAPI_CONFIG` is the standing configuration.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_openapi and app_config.openapi_config == DEFAULT_OPENAPI_CONFIG:
            app_config.openapi_config = openapi.config

    def configure_response_class(self, app_config: AppConfig) -> None:
        """Add the custom response class.

        No-op if the [`AppConfig.response_class`][starlite.config.app.AppConfig.response_class]
        is not `None`.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_response_class and app_config.response_class is None:
            app_config.response_class = type(
                "Response", (Response,), {"serializer": staticmethod(self.config.serializer)}
            )

    def configure_sentry(self, app_config: AppConfig) -> None:
        """Add handler to configure Sentry integration.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_sentry:
            app_config.on_startup.append(sentry.configure)

    def configure_sqlalchemy_plugin(self, app_config: AppConfig) -> None:
        """Configure `SQLAlchemy` for the application.

        Adds a configured [`SQLAlchemyPlugin`][starlite.plugins.sql_alchemy.SQLAlchemyPlugin] to
        [`AppConfig.plugins`][starlite.config.app.AppConfig.plugins].

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_sqlalchemy_plugin:
            app_config.plugins.append(SQLAlchemyPlugin(config=sqlalchemy_plugin.config))

    def configure_worker(self, app_config: AppConfig) -> None:
        """Configure the `SAQ` async worker.

        No-op if there are no worker functions set on
        [`PluginConfig`][starlite_saqlalchemy.PluginConfig].

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_worker:
            worker_kwargs: dict[str, Any] = {"functions": self.config.worker_functions}
            if self.config.do_logging:
                worker_kwargs["before_process"] = log.worker.before_process
                worker_kwargs["after_process"] = log.worker.after_process
            worker_instance = create_worker_instance(**worker_kwargs)
            app_config.on_startup.append(worker_instance.on_app_startup)
            app_config.on_shutdown.append(worker_instance.stop)

    @staticmethod
    def _ensure_list(item: list[T] | T) -> list[T]:
        if isinstance(item, list):
            return item
        return [] if item is None else [item]
