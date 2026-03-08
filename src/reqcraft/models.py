"""Data models for ReqCraft."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HttpMethod(str, Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

    @classmethod
    def color(cls, method: HttpMethod) -> str:
        """Return the display color for a method."""
        return {
            cls.GET: "green",
            cls.POST: "#3b82f6",
            cls.PUT: "#e59400",
            cls.DELETE: "red",
            cls.PATCH: "#a855f7",
            cls.HEAD: "#06b6d4",
            cls.OPTIONS: "#6b7280",
        }.get(method, "white")


class AuthType(str, Enum):
    """Supported authentication types."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"


class BodyType(str, Enum):
    """Supported request body types."""

    NONE = "none"
    JSON = "json"
    FORM = "form"
    RAW = "raw"


@dataclass
class KeyValuePair:
    """A key-value pair with an enabled flag."""

    key: str = ""
    value: str = ""
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "enabled": self.enabled}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KeyValuePair:
        return cls(
            key=data.get("key", ""),
            value=data.get("value", ""),
            enabled=data.get("enabled", True),
        )


@dataclass
class AuthConfig:
    """Authentication configuration."""

    auth_type: AuthType = AuthType.NONE
    username: str = ""
    password: str = ""
    token: str = ""
    api_key_name: str = ""
    api_key_value: str = ""
    api_key_in: str = "header"  # "header" or "query"

    def to_dict(self) -> dict[str, Any]:
        return {
            "auth_type": self.auth_type.value,
            "username": self.username,
            "password": self.password,
            "token": self.token,
            "api_key_name": self.api_key_name,
            "api_key_value": self.api_key_value,
            "api_key_in": self.api_key_in,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthConfig:
        return cls(
            auth_type=AuthType(data.get("auth_type", "none")),
            username=data.get("username", ""),
            password=data.get("password", ""),
            token=data.get("token", ""),
            api_key_name=data.get("api_key_name", ""),
            api_key_value=data.get("api_key_value", ""),
            api_key_in=data.get("api_key_in", "header"),
        )


@dataclass
class RequestModel:
    """Represents an HTTP request."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    method: HttpMethod = HttpMethod.GET
    url: str = ""
    headers: list[KeyValuePair] = field(default_factory=list)
    params: list[KeyValuePair] = field(default_factory=list)
    body_type: BodyType = BodyType.NONE
    body: str = ""
    auth: AuthConfig = field(default_factory=AuthConfig)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "method": self.method.value,
            "url": self.url,
            "headers": [h.to_dict() for h in self.headers],
            "params": [p.to_dict() for p in self.params],
            "body_type": self.body_type.value,
            "body": self.body,
            "auth": self.auth.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RequestModel:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            method=HttpMethod(data.get("method", "GET")),
            url=data.get("url", ""),
            headers=[KeyValuePair.from_dict(h) for h in data.get("headers", [])],
            params=[KeyValuePair.from_dict(p) for p in data.get("params", [])],
            body_type=BodyType(data.get("body_type", "none")),
            body=data.get("body", ""),
            auth=AuthConfig.from_dict(data.get("auth", {})),
        )

    def display_name(self) -> str:
        """Return a display name for the request."""
        if self.name:
            return self.name
        if self.url:
            # Extract path from URL
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            path = parsed.path or "/"
            return f"{self.method.value} {path}"
        return f"{self.method.value} (untitled)"


@dataclass
class ResponseModel:
    """Represents an HTTP response."""

    status_code: int = 0
    reason: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    content_type: str = ""
    elapsed_ms: float = 0.0
    size_bytes: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "reason": self.reason,
            "headers": self.headers,
            "body": self.body,
            "content_type": self.content_type,
            "elapsed_ms": self.elapsed_ms,
            "size_bytes": self.size_bytes,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResponseModel:
        return cls(
            status_code=data.get("status_code", 0),
            reason=data.get("reason", ""),
            headers=data.get("headers", {}),
            body=data.get("body", ""),
            content_type=data.get("content_type", ""),
            elapsed_ms=data.get("elapsed_ms", 0.0),
            size_bytes=data.get("size_bytes", 0),
            timestamp=data.get("timestamp", time.time()),
        )

    @property
    def status_class(self) -> str:
        """Return CSS class for status code coloring."""
        if 200 <= self.status_code < 300:
            return "status-2xx"
        elif 300 <= self.status_code < 400:
            return "status-3xx"
        elif 400 <= self.status_code < 500:
            return "status-4xx"
        else:
            return "status-5xx"

    @property
    def formatted_size(self) -> str:
        """Return human-readable size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"


@dataclass
class HistoryEntry:
    """A record in the request history."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request: RequestModel = field(default_factory=RequestModel)
    response: ResponseModel | None = None
    timestamp: float = field(default_factory=time.time)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "request": self.request.to_dict(),
            "response": self.response.to_dict() if self.response else None,
            "timestamp": self.timestamp,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        resp = data.get("response")
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            request=RequestModel.from_dict(data.get("request", {})),
            response=ResponseModel.from_dict(resp) if resp else None,
            timestamp=data.get("timestamp", time.time()),
            error=data.get("error"),
        )


@dataclass
class Collection:
    """A named collection of saved requests."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Collection"
    requests: list[RequestModel] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "requests": [r.to_dict() for r in self.requests],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Collection:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "New Collection"),
            requests=[RequestModel.from_dict(r) for r in data.get("requests", [])],
        )


@dataclass
class Environment:
    """A named set of variables for request templating."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Environment"
    variables: dict[str, str] = field(default_factory=dict)
    is_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "variables": self.variables,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Environment:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "New Environment"),
            variables=data.get("variables", {}),
            is_active=data.get("is_active", False),
        )
