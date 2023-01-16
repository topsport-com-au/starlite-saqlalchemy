"""Test suite for pytest plugin."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest import Pytester


def test_pytest_addoption(pytester: Pytester) -> None:
    """Test ini options added."""
    pytester.makepyfile(
        """
        from pytest import Parser
        from pytest_starlite_saqlalchemy import pytest_addoption

        def test_pytest_addoption() -> None:
            parser = Parser()
            pytest_addoption(parser)
            assert parser._ininames == ["test_app", "unit_test_pattern"]
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_is_unit_test_true(pytester: Pytester) -> None:
    """Test is_unit_test fixture True conditions."""
    pytester.makepyprojecttoml(
        f"""
        [tool.pytest.ini_options]
        unit_test_pattern = "^{pytester.path}/test_is_unit_test_true.py$"
        """
    )
    pytester.makepyfile(
        """
        from unittest.mock import MagicMock
        from starlite_saqlalchemy.sqlalchemy_plugin import SQLAlchemyConfig
        from starlite_saqlalchemy.worker import Worker

        def test_is_unit_test_true(is_unit_test: bool) -> None:
            assert is_unit_test is True

        def test_patch_sqlalchemy_plugin() -> None:
            assert isinstance(SQLAlchemyConfig.on_shutdown, MagicMock)

        def test_patch_worker() -> None:
            assert isinstance(Worker.on_app_startup, MagicMock)
            assert isinstance(Worker.stop, MagicMock)
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=3)


def test_is_unit_test_false(pytester: Pytester) -> None:
    """Unit is_unit_test fixture False conditions."""
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        unit_test_pattern = "^definitely/not/the/path/to/test_is_unit_test_false.py$"
        """
    )
    pytester.makepyfile(
        """
        from unittest.mock import MagicMock
        from starlite_saqlalchemy.sqlalchemy_plugin import SQLAlchemyConfig
        from starlite_saqlalchemy.worker import Worker

        def test_is_unit_test_false(is_unit_test: bool) -> None:
            assert is_unit_test is False

        def test_patch_sqlalchemy_plugin() -> None:
            assert not isinstance(SQLAlchemyConfig.on_shutdown, MagicMock)

        def test_patch_worker() -> None:
            assert not isinstance(Worker.on_app_startup, MagicMock)
            assert not isinstance(Worker.stop, MagicMock)
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=3)


def test_patch_http_close(pytester: Pytester) -> None:
    """Test that http clients won't be closed in-between tests."""
    pytester.makepyfile(
        """
        import starlite_saqlalchemy

        client = starlite_saqlalchemy.http.Client("https://somewhere.com")
        assert starlite_saqlalchemy.http.clients

        def test_patch_http_close(is_unit_test: bool) -> None:
            assert not starlite_saqlalchemy.http.clients
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_app_fixture_if_app_factory(pytester: Pytester) -> None:
    """Test that the app fixture returns an instance retrieved from a
    factory."""
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        test_app = "tests.utils.app:create_app"
        """
    )
    pytester.makepyfile(
        """
        from starlite import Starlite

        def test_app(app):
            assert isinstance(app, Starlite)
            assert "/authors" in app.route_handler_method_map
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_app_fixture_if_app_instance(pytester: Pytester) -> None:
    """Test that the app fixture returns the an instance if the path points to
    one."""
    pytester.syspathinsert()
    pytester.makepyfile(
        test_app="""
            from tests.utils.app import create_app

            app = create_app()
            """
    )
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        test_app = "test_app:app"
        """
    )
    pytester.makepyfile(
        """
        from starlite import Starlite

        def test_app(app):
            assert isinstance(app, Starlite)
            assert "/authors" in app.route_handler_method_map
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_app_fixture_if_test_app_path_does_not_exist(pytester: Pytester) -> None:
    """Tests that the app fixture falls back to a new app instance if the
    configured path is not found."""
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        test_app = "definitely.not.the.path.to.app:app"
        """
    )
    pytester.makepyfile(
        """
        from starlite import Starlite

        def test_app(app):
            assert isinstance(app, Starlite)
            # the app that is created should not have any handlers attached.
            assert app.route_handler_method_map.keys() == {"/health"}
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
