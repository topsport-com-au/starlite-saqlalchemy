"""Automated controller testing."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from starlite.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_405_METHOD_NOT_ALLOWED,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from pytest import MonkeyPatch
    from starlite.testing import TestClient

    from starlite_saqlalchemy.service import Service


class ControllerTest:
    """Standard controller testing utility."""

    def __init__(
        self,
        client: TestClient,
        base_path: str,
        collection: Sequence[Any],
        raw_collection: Sequence[dict[str, Any]],
        service_type: type[Service],
        monkeypatch: MonkeyPatch,
        collection_filters: dict[str, Any] | None = None,
    ) -> None:
        """Perform standard tests of controllers.

        Args:
            client: Test client instance.
            base_path: Path for POST and collection GET requests.
            collection: Collection of domain objects.
            raw_collection: Collection of raw representations of domain objects.
            service_type: The domain Service object type.
            monkeypatch: Pytest's monkeypatch.
            collection_filters: Collection filters for GET collection request.
        """
        self.client = client
        self.base_path = base_path
        self.collection = collection
        self.raw_collection = raw_collection
        self.service_type = service_type
        self.monkeypatch = monkeypatch
        self.collection_filters = collection_filters

    def _get_random_member(self) -> Any:
        return random.choice(self.collection)

    def _get_raw_for_member(self, member: Any) -> dict[str, Any]:
        return [item for item in self.raw_collection if item["id"] == str(member.id)][0]

    def test_get_collection(self, with_filters: bool = False) -> None:
        """Test collection endpoint get request."""

        async def _list(*_: Any, **__: Any) -> list[Any]:
            return list(self.collection)

        self.monkeypatch.setattr(self.service_type, "list", _list)

        resp = self.client.get(
            self.base_path, params=self.collection_filters if with_filters else None
        )

        if resp.status_code == HTTP_405_METHOD_NOT_ALLOWED:
            return

        assert resp.status_code == HTTP_200_OK
        assert resp.json() == self.raw_collection

    def test_member_request(self, method: str, service_method: str, exp_status: int) -> None:
        """Test member endpoint request."""
        member = self._get_random_member()
        raw = self._get_raw_for_member(member)

        async def _method(*_: Any, **__: Any) -> Any:
            return member

        self.monkeypatch.setattr(self.service_type, service_method, _method)

        if method.lower() == "post":
            url = self.base_path
        else:
            url = f"{self.base_path}/{member.id}"

        request_kw: dict[str, Any] = {}
        if method.lower() in ("put", "post"):
            request_kw["json"] = raw

        resp = self.client.request(method, url, **request_kw)

        if resp.status_code == HTTP_405_METHOD_NOT_ALLOWED:
            return

        assert resp.status_code == exp_status
        assert resp.json() == raw

    def run(self) -> None:
        """Run the tests."""
        # test the collection route with and without filters for branch coverage.
        self.test_get_collection()
        if self.collection_filters:
            self.test_get_collection(with_filters=True)
        for method, service_method, status in [
            ("GET", "get", HTTP_200_OK),
            ("PUT", "update", HTTP_200_OK),
            ("POST", "create", HTTP_201_CREATED),
            ("DELETE", "delete", HTTP_200_OK),
        ]:
            self.test_member_request(method, service_method, status)
