"""Async HTTP request client implementation built on `httpx`."""
from __future__ import annotations

from typing import Any

import httpx


class ClientException(Exception):
    """Base client exception."""


class Client:
    """Base class for HTTP clients.

    ```python
    client = Client()
    response = await client.request("GET", "/some/resource")
    assert response.status_code == 200
    ```
    """

    _client = httpx.AsyncClient()

    async def request(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Make a HTTP request.

        Passes `*args`, `**kwargs` straight through to `httpx.AsyncClient.request`, we call
        `raise_for_status()` on the response and wrap any `HTTPX` error in a `ClientException`.

        Args:
            *args: Unpacked into `httpx.AsyncClient.request()`.
            **kwargs: Unpacked into `httpx.AsyncClient.request()`.

        Returns:
            Return value of `httpx.AsyncClient.request()` after calling
            `httpx.Response.raise_for_status()`

        Raises:
            ClientException: Wraps any `httpx.HTTPError` arising from the request or response status
                check.
        """
        try:
            req = await self._client.request(*args, **kwargs)
            req.raise_for_status()
        except httpx.HTTPError as exc:
            url = exc.request.url
            raise ClientException(f"Client Error for '{url}'") from exc
        return req

    def json(self, response: httpx.Response) -> Any:
        """Parse response as JSON.

        Abstracts deserializing to allow for optional unwrapping of server response, e.g.,
        `{"data": []}`.

        Args:
            response: Response object, we call `.json()` on it.

        Returns:
            The result of `httpx.Response.json()` after passing through `self.unwrap_json()`.
        """
        return self.unwrap_json(response.json())

    @staticmethod
    def unwrap_json(data: Any) -> Any:
        """Receive parsed JSON.

        Override this method for pre-processing response data, for example unwrapping enveloped
        data.

        Args:
            data: Value returned from `response.json()`.

        Returns:
            Pre-processed data, default is pass-through/no-op.
        """
        return data

    @classmethod
    async def close(cls) -> None:
        """Close underlying client transport and proxies."""
        await cls._client.aclose()
