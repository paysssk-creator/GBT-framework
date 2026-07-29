"""
GBT Python SDK — gbtxiaotudou.com API client.

Usage:
    from gbt_sdk import GBT

    client = GBT(api_key="gbt_xxxxx")

    # Checkout
    checkout = client.checkout_configurations.create(
        plan={"initial_price": 10.0, "plan_type": "one_time"},
        metadata={"order_id": "order_123"},
    )
    print(checkout.id)  # ch_xxx

    # Projects
    for p in client.projects.list():
        print(p.name, p.price)

    # Deploy
    deploy = client.deployments.create(
        repo_url="https://github.com/user/repo",
        plan="basic",
    )
    print(deploy.status)
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Optional

import requests

__version__ = "1.0.0"
__all__ = ["GBT", "GBTError", "Resource", "CheckoutConfigurations", "Payments", "Projects", "Deployments"]


# ── Exceptions ──────────────────────────────────────────────────────────────────

class GBTError(Exception):
    """Base exception for all GBT SDK errors."""

    def __init__(self, message: str, *, status_code: int = 0, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def __str__(self) -> str:
        return f"[{self.status_code}] {super().__str__()}"


class APIConnectionError(GBTError):
    """Failed to reach the GBT API (DNS, TLS, timeout, etc.)."""


class AuthenticationError(GBTError):
    """Invalid or missing API key (401)."""


class NotFoundError(GBTError):
    """Resource not found (404)."""


class RateLimitError(GBTError):
    """Rate limited; back off and retry (429)."""


class ServerError(GBTError):
    """GBT server-side error (5xx)."""


def _build_error(status_code: int, message: str, body: Any = None) -> GBTError:
    if status_code == 401:
        return AuthenticationError(message, status_code=status_code, body=body)
    if status_code == 404:
        return NotFoundError(message, status_code=status_code, body=body)
    if status_code == 429:
        return RateLimitError(message, status_code=status_code, body=body)
    if 500 <= status_code < 600:
        return ServerError(message, status_code=status_code, body=body)
    return GBTError(message, status_code=status_code, body=body)


# ── Resource base ───────────────────────────────────────────────────────────────

class Resource:
    """Dict-like wrapper for API response objects with attribute access."""

    _data: dict[str, Any]

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name == "_data":
            raise AttributeError(name)
        try:
            val = self._data[name]
        except KeyError:
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}") from None
        if isinstance(val, dict) and not isinstance(val, Resource):
            return Resource(val)
        if isinstance(val, list):
            return [Resource(v) if isinstance(v, dict) else v for v in val]
        return val

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._data!r})"

    def to_dict(self) -> dict[str, Any]:
        return self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    @classmethod
    def from_list(cls, items: list[dict[str, Any]]) -> list[Resource]:
        return [cls(item) for item in items]


# ── Paginated list ──────────────────────────────────────────────────────────────

class PaginatedList:
    """Iterable wrapper for paginated API list responses."""

    def __init__(self, client: "GBTClient", path: str, params: dict[str, Any] | None = None):
        self._client = client
        self._path = path
        self._params = params or {}

    def __iter__(self):
        return self._iter_pages()

    def _iter_pages(self):
        params = dict(self._params)
        while True:
            resp = self._client._request("GET", self._path, params=params)
            data = resp["data"] if isinstance(resp, dict) and "data" in resp else resp
            if isinstance(data, list):
                yield from Resource.from_list(data)
                return
            if isinstance(data, dict):
                items = data.get("items") or data.get("data") or []
                for item in items:
                    yield Resource(item) if isinstance(item, dict) else item
                cursor = data.get("cursor") or data.get("next_cursor")
                if not cursor:
                    return
                params["cursor"] = cursor
            else:
                return

    def first(self) -> Resource | None:
        params = dict(self._params)
        resp = self._client._request("GET", self._path, params=params)
        data = resp["data"] if isinstance(resp, dict) and "data" in resp else resp
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("data") or []
        else:
            return None
        return Resource(items[0]) if items else None


# ── API client core ─────────────────────────────────────────────────────────────

class GBTClient:
    """Low-level HTTP client shared by all resource namespaces."""

    API_BASE = "https://gbtxiaotudou.com/api"

    def __init__(self, api_key: str, base_url: str | None = None):
        if not api_key:
            raise GBTError("api_key is required")
        self._api_key = api_key
        self._base_url = (base_url or self.API_BASE).rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"gbt-python-sdk/{__version__}",
        })

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        idempotency_key: str | None = None,
    ) -> Any:
        headers: dict[str, str] = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        try:
            response = self._session.request(
                method=method,
                url=self._url(path),
                params=params,
                json=json_body,
                headers=headers,
                timeout=30,
            )
        except requests.exceptions.Timeout:
            raise APIConnectionError("Request timed out") from None
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Connection failed: {e}") from e
        except requests.RequestException as e:
            raise APIConnectionError(f"Request error: {e}") from e

        status = response.status_code
        if status not in (200, 201, 204):
            try:
                body = response.json()
                msg = body.get("error", body.get("message", response.text))
            except Exception:
                msg = response.text
            raise _build_error(status, msg, body)

        if status == 204:
            return None
        return response.json()


# ── Resource namespaces ─────────────────────────────────────────────────────────

class CheckoutConfigurations:
    """Manage checkout configurations (Whop-style checkout sessions).

    Create a checkout session, pass the session ID to the frontend embedded
    checkout component, and listen for the `checkout.completed` webhook.
    """

    def __init__(self, client: GBTClient):
        self._client = client

    def create(
        self,
        plan: dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
        success_url: str | None = None,
        cancel_url: str | None = None,
        idempotency_key: str | None = None,
    ) -> Resource:
        """Create a checkout configuration and return a session.

        Args:
            plan: dict with ``initial_price`` (float), ``plan_type``
                  ("one_time" | "subscription"), and optional ``currency``.
            metadata: arbitrary key/value pairs attached to the checkout.
            success_url: redirect after successful payment.
            cancel_url: redirect if the user cancels.
            idempotency_key: optional idempotency key (auto-generated if omitted).
        """
        if idempotency_key is None:
            idempotency_key = f"gbt_{uuid.uuid4().hex}"
        body: dict[str, Any] = {"plan": plan}
        if metadata:
            body["metadata"] = metadata
        if success_url:
            body["success_url"] = success_url
        if cancel_url:
            body["cancel_url"] = cancel_url
        data = self._client._request(
            "POST",
            "/checkout/configurations",
            json_body=body,
            idempotency_key=idempotency_key,
        )
        return Resource(data)

    def retrieve(self, checkout_id: str) -> Resource:
        """Retrieve a checkout configuration by ID."""
        data = self._client._request("GET", f"/checkout/configurations/{checkout_id}")
        return Resource(data)


class Payments:
    """List and retrieve payments."""

    def __init__(self, client: GBTClient):
        self._client = client

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        status: str | None = None,
    ) -> PaginatedList:
        """List payments, optionally filtered by status.

        Args:
            limit: max items per page.
            cursor: pagination cursor from a previous response.
            status: filter by payment status ("completed", "pending", "failed", etc.).
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if status is not None:
            params["status"] = status
        return PaginatedList(self._client, "/payments", params)

    def retrieve(self, payment_id: str) -> Resource:
        """Retrieve a single payment by ID."""
        data = self._client._request("GET", f"/payments/{payment_id}")
        return Resource(data)


class Projects:
    """List and retrieve AI project templates."""

    def __init__(self, client: GBTClient):
        self._client = client

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        category: str | None = None,
    ) -> PaginatedList:
        """List available project templates.

        Args:
            limit: max items per page.
            cursor: pagination cursor.
            category: filter by category ("ai", "ecommerce", "saas", etc.).
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if category is not None:
            params["category"] = category
        return PaginatedList(self._client, "/projects", params)

    def retrieve(self, project_id: str) -> Resource:
        """Retrieve a single project template by ID."""
        data = self._client._request("GET", f"/projects/{project_id}")
        return Resource(data)


class Deployments:
    """Create, retrieve, and monitor deployments."""

    def __init__(self, client: GBTClient):
        self._client = client

    def create(
        self,
        repo_url: str,
        *,
        plan: str = "basic",
        env_vars: dict[str, str] | None = None,
        branch: str | None = None,
        build_command: str | None = None,
        idempotency_key: str | None = None,
    ) -> Resource:
        """Create a new deployment.

        Args:
            repo_url: GitHub / GitLab repository URL.
            plan: deployment tier ("basic", "pro", "enterprise").
            env_vars: environment variables for the deployment.
            branch: git branch to deploy (default: "main").
            build_command: custom build command override.
            idempotency_key: optional idempotency key.
        """
        if idempotency_key is None:
            idempotency_key = f"gbt_{uuid.uuid4().hex}"
        body: dict[str, Any] = {
            "repo_url": repo_url,
            "plan": plan,
        }
        if env_vars:
            body["env_vars"] = env_vars
        if branch:
            body["branch"] = branch
        if build_command:
            body["build_command"] = build_command
        data = self._client._request(
            "POST",
            "/deployments",
            json_body=body,
            idempotency_key=idempotency_key,
        )
        return Resource(data)

    def retrieve(self, deployment_id: str) -> Resource:
        """Retrieve a deployment by ID."""
        data = self._client._request("GET", f"/deployments/{deployment_id}")
        return Resource(data)

    def status(self, deployment_id: str) -> Resource:
        """Get the current status of a deployment (shorthand)."""
        data = self._client._request("GET", f"/deployments/{deployment_id}/status")
        return Resource(data)


# ── Public entry point ──────────────────────────────────────────────────────────

class GBT:
    """GBT API client — top-level entry point.

    Args:
        api_key: GBT API key (starts with ``gbt_``).
        base_url: override the base API URL (default: https://gbtxiaotudou.com/api).
    """

    def __init__(self, api_key: str | None = None, *, base_url: str | None = None):
        if api_key is None:
            api_key = os.environ.get("GBT_API_KEY", "")
        if not api_key:
            raise GBTError(
                "API key is required. Pass api_key= or set GBT_API_KEY environment variable."
            )
        self._client = GBTClient(api_key, base_url=base_url)
        self.checkout_configurations = CheckoutConfigurations(self._client)
        self.payments = Payments(self._client)
        self.projects = Projects(self._client)
        self.deployments = Deployments(self._client)
