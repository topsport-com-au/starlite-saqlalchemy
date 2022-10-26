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
from typing import TYPE_CHECKING

from pydantic import BaseModel
from starlite.app import DEFAULT_CACHE_CONFIG, DEFAULT_OPENAPI_CONFIG
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin

from . import (
    cache,
    compression,
    dependencies,
    exceptions,
    http,
    logging,
    openapi,
    redis,
    response,
    sentry,
    sqlalchemy_plugin,
    static_files,
)
from .health import health_check
from .repository.exceptions import RepositoryException
from .service import ServiceException, make_service_callback
from .worker import create_worker_instance

if TYPE_CHECKING:

    from starlite.config.app import AppConfig

    from starlite_saqlalchemy.worker import WorkerFunction


class PluginConfig(BaseModel):
    """Configure behavior of the `ConfigureApp` object.

    Each feature that the plugin enables can be toggled with the
    `do_<behavior>` switch, e.g.,
    `PluginConfig(do_after_exception=False)` will tell `ConfigureApp`
    not to add the after exception logging hook handler to the
    application.
    """

    worker_functions: "list[WorkerFunction | tuple[str, WorkerFunction]]" = []
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
    do_sqlalchemy_plugin: bool = True
    """
    Set the SQLAlchemy plugin on the application. Adds the plugin to
    [`AppConfig.plugins`][starlite.config.app.AppConfig.plugins].
    """
    do_static_files: bool = True
    """
    Set the static files config object to
    [`AppConfig.static_files_config`][starlite.config.app.AppConfig.static_files_config].
    """
    do_worker: bool = True
    """
    Configure the async worker on the application. This action instantiates a worker instance and
    sets handlers for [`AppConfig.on_startup`][starlite.config.app.AppConfig.on_startup] and
    [`AppConfig.on_shutdown`][starlite.config.app.AppConfig.on_shutdown] that manage the lifecycle
    of the `SAQ` worker.
    """


class ConfigureApp:
    """Starlite application configuration.

    Args:
        config: Provide a config object to customize the behavior of the plugin.
    """

    def __init__(self, config: PluginConfig = PluginConfig()) -> None:
        self.config = config

    def __call__(self, app_config: "AppConfig") -> "AppConfig":
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
        self.configure_exception_handlers(app_config)
        self.configure_health_check(app_config)
        self.configure_logging(app_config)
        self.configure_response_class(app_config)
        self.configure_sentry(app_config)
        self.configure_sqlalchemy_plugin(app_config)
        self.configure_static_files(app_config)
        self.configure_worker(app_config)

        app_config.on_shutdown.extend([http.Client.close, redis.client.close])
        return app_config

    def configure_after_exception(self, app_config: "AppConfig") -> None:
        """Add the logging after exception hook handler.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_after_exception:
            if not isinstance(app_config.after_exception, list):
                app_config.after_exception = [app_config.after_exception]
            app_config.after_exception.append(exceptions.after_exception_hook_handler)

    def configure_cache(self, app_config: "AppConfig") -> None:
        """Configure the application cache.

        We only overwrite if [`DEFAULT_CACHE_CONFIG`][starlite.app.DEFAULT_CACHE_CONFIG] is the
        standing configuration object.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_cache and app_config.cache_config is DEFAULT_CACHE_CONFIG:
            app_config.cache_config = cache.config

    def configure_collection_dependencies(self, app_config: "AppConfig") -> None:
        """Add the required [`Provide`][starlite.datastructures.Provide]
        instances to the app dependency mapping.

        If a dependency has already been provided with the same key we do not overwrite it.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_collection_dependencies:
            for key, value in dependencies.create_collection_dependencies().items():
                app_config.dependencies.setdefault(key, value)

    def configure_compression(self, app_config: "AppConfig") -> None:
        """Configure application compression.

        No-op if [`AppConfig.compression_config`][starlite.config.app.AppConfig.compression_config]
        has already been set.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_compression and app_config.compression_config is None:
            app_config.compression_config = compression.config

    def configure_exception_handlers(self, app_config: "AppConfig") -> None:
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

    def configure_health_check(self, app_config: "AppConfig") -> None:
        """Adds the health check controller.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_health_check:
            app_config.route_handlers.append(health_check)

    def configure_logging(self, app_config: "AppConfig") -> None:
        """Configures application logging if it has not already been
        configured.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_logging and app_config.logging_config is None:
            app_config.logging_config = logging.config

    def configure_openapi(self, app_config: "AppConfig") -> None:
        """Configures the OpenAPI docs if they have not already been
        configured.

        We only overwrite if `DEFAULT_OPENAPI_CONFIG` is the standing configuration.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_openapi and app_config.openapi_config is DEFAULT_OPENAPI_CONFIG:
            app_config.openapi_config = openapi.config

    def configure_response_class(self, app_config: "AppConfig") -> None:
        """Add the custom response class.

        No-op if the [`AppConfig.response_class`][starlite.config.app.AppConfig.response_class]
        is not `None`.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_response_class and app_config.response_class is None:
            app_config.response_class = response.Response

    def configure_sentry(self, app_config: "AppConfig") -> None:
        """Add handler to configure Sentry integration.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_sentry:
            app_config.on_startup.append(sentry.configure)

    def configure_sqlalchemy_plugin(self, app_config: "AppConfig") -> None:
        """Configure `SQLAlchemy` for the application.

        Adds a configured [`SQLAlchemyPlugin`][starlite.plugins.sql_alchemy.SQLAlchemyPlugin] to
        [`AppConfig.plugins`][starlite.config.app.AppConfig.plugins].

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_sqlalchemy_plugin:
            app_config.plugins.append(SQLAlchemyPlugin(config=sqlalchemy_plugin.config))

    def configure_static_files(self, app_config: "AppConfig") -> None:
        """Configure static files for the application.

        No-op if
        [`AppConfig.static_files_config`][starlite.config.app.AppConfig.static_files_config] is not
        `None`.

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_static_files and app_config.static_files_config is not None:
            app_config.static_files_config = static_files.config

    def configure_worker(self, app_config: "AppConfig") -> None:
        """Configure the `SAQ` async worker.

        No-op if there are no worker functions set on
        [`PluginConfig`][starlite_saqlalchemy.PluginConfig].

        Args:
            app_config: The Starlite application config object.
        """
        if self.config.do_worker and self.config.worker_functions:
            self.config.worker_functions.append(
                (make_service_callback.__qualname__, make_service_callback)
            )
            worker_instance = create_worker_instance(self.config.worker_functions)
            app_config.on_shutdown.append(worker_instance.stop)
            app_config.on_startup.append(worker_instance.on_app_startup)
