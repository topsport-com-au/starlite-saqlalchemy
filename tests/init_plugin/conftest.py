import pytest
from starlite.app import DEFAULT_CACHE_CONFIG
from starlite.config.app import AppConfig


@pytest.fixture()
def app_config() -> AppConfig:
    return AppConfig(
        after_exception=[],
        after_request=None,
        after_response=None,
        after_shutdown=[],
        after_startup=[],
        allowed_hosts=[],
        before_request=None,
        before_send=[],
        before_shutdown=[],
        before_startup=[],
        cache_config=DEFAULT_CACHE_CONFIG,
        compression_config=None,
        cors_config=None,
        csrf_config=None,
        debug=False,
        dependencies={},
        exception_handlers={},
        guards=[],
        middleware=[],
        on_shutdown=[],
        on_startup=[],
        openapi_config=None,
        parameters={},
        plugins=[],
        response_class=None,
        response_cookies=[],
        response_headers={},
        route_handlers=[],
        security=[],
        static_files_config=[],
        tags=[],
        template_config=None,
    )
