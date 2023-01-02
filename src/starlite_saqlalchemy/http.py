"""Async HTTP request client implementation built on `httpx`."""
from __future__ import annotations

from typing import Any

import httpx
import tenacity

from . import settings

clients = set[httpx.AsyncClient]()
"""For bookkeeping of clients.

We close them on app shutdown.
"""


class ClientException(Exception):
    """Base client exception."""


class Client:
    """A simple HTTP client class with retrying and exponential backoff.

    This class uses the `tenacity` library to retry failed HTTP httpx
    with exponential backoff and jitter. It also uses a `httpx.Session`
    instance to manage HTTP connections and cookies.
    """

    def __init__(self, base_url: str, headers: dict[str, str] | None = None) -> None:
        """
        Args:
            base_url: e.g., http://localhost
            headers: Headers that are applied to every request
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        clients.add(self.client)
        self.client.headers.update({"Content-Type": "application/json"})
        if headers is not None:
            self.client.headers.update(headers)

    @tenacity.retry(
        wait=tenacity.wait_random_exponential(  # type:ignore[attr-defined]
            multiplier=settings.http.EXPONENTIAL_BACKOFF_MULTIPLIER,
            exp_base=settings.http.EXPONENTIAL_BACKOFF_BASE,
            min=settings.http.BACKOFF_MIN,
            max=settings.http.BACKOFF_MAX,
        ),
        retry=tenacity.retry_if_exception_type(httpx.TransportError),  # type:ignore[attr-defined]
    )
    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make an HTTP request with retrying and exponential backoff.

        This method uses the `httpx` library to make an HTTP request and
        the `tenacity` library to retry the request if it fails. It uses
        exponential backoff with jitter to wait between retries.

        Args:
            method: The HTTP method (e.g. "GET", "POST")
            path: The URL path (e.g. "/users/123")
            params: Query parameters (optional)
            content: Data to send in the request body (optional)
            headers: HTTP headers to send with the request (optional)

        Returns:
            The `httpx.Response` object.

        Raises:
            httpx.RequestException: If the request fails and cannot be retried.
        """
        try:
            response = await self.client.request(
                method, path, params=params, content=content, headers=headers
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ClientException from exc
        return response

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make an HTTP GET request with retrying and exponential backoff.

        This method is a convenience wrapper around the `request` method that
        sends an HTTP GET request.

        Args:
            path: The URL path (e.g. "/users/123")
            params: Query parameters (optional)
            headers: HTTP headers to send with the request (optional)

        Returns:
            The `httpx.Response` object.

        Raises:
            httpx.RequestException: If the request fails and cannot be retried.
        """
        return await self.request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make an HTTP POST request with retrying and exponential backoff.

        This method is a convenience wrapper around the `request` method that
        sends an HTTP POST request.

        Args:
            path: The URL path (e.g. "/users/123")
            content: Data to send in the request body (optional)
            headers: HTTP headers to send with the request (optional)

        Returns:
            The `httpx.Response` object.

        Raises:
            httpx.RequestException: If the request fails and cannot be retried.
        """
        return await self.request("POST", path, content=content, headers=headers)

    async def put(
        self,
        path: str,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make an HTTP PUT request with retrying and exponential backoff.

        This method is a convenience wrapper around the `request` method that
        sends an HTTP PUT request.

        Args:
            path: The URL path (e.g. "/users/123")
            content: Data to send in the request body (optional)
            headers: HTTP headers to send with the request (optional)

        Returns:
            The `httpx.Response` object.

        Raises:
            httpx.RequestException: If the request fails and cannot be retried.
        """
        return await self.request("PUT", path, content=content, headers=headers)

    async def delete(self, path: str, headers: dict[str, str] | None = None) -> httpx.Response:
        """Make an HTTP DELETE request with retrying and exponential backoff.

        This method is a convenience wrapper around the `request` method that
        sends an HTTP DELETE request.

        Args:
            path: The URL path (e.g. "/users/123")
            headers: HTTP headers to send with the request (optional)

        Returns:
            The `httpx.Response` object.

        Raises:
            httpx.RequestException: If the request fails and cannot be retried.
        """
        return await self.request("DELETE", path, headers=headers)


async def on_shutdown() -> None:
    """Close any clients that have been created."""
    for client in clients:
        await client.aclose()
