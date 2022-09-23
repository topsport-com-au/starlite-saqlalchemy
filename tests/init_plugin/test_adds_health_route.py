from starlite.config.app import AppConfig
from starlite_saqpg import ConfigureApp, init_plugin


def test_plugin_adds_health_route(app_config: AppConfig) -> None:
    config = ConfigureApp()(app_config)
    assert init_plugin.health.health_check in config.route_handlers
