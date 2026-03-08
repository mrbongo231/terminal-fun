"""Async HTTP client for sending requests."""

from __future__ import annotations

import re
import time

import httpx

from reqcraft.models import (
    AuthConfig,
    AuthType,
    BodyType,
    HttpMethod,
    KeyValuePair,
    RequestModel,
    ResponseModel,
)


def substitute_variables(text: str, variables: dict[str, str]) -> str:
    """Replace {{variable}} placeholders with values from the environment."""
    if not variables or not text:
        return text

    def replacer(match: re.Match) -> str:
        var_name = match.group(1).strip()
        return variables.get(var_name, match.group(0))

    return re.sub(r"\{\{(.+?)\}\}", replacer, text)


def _build_headers(
    request: RequestModel, variables: dict[str, str]
) -> dict[str, str]:
    """Build the headers dict from KeyValuePairs + auth."""
    headers: dict[str, str] = {}

    for kv in request.headers:
        if kv.enabled and kv.key:
            key = substitute_variables(kv.key, variables)
            value = substitute_variables(kv.value, variables)
            headers[key] = value

    # Apply auth headers
    auth = request.auth
    if auth.auth_type == AuthType.BEARER:
        token = substitute_variables(auth.token, variables)
        headers["Authorization"] = f"Bearer {token}"
    elif auth.auth_type == AuthType.API_KEY and auth.api_key_in == "header":
        name = substitute_variables(auth.api_key_name, variables)
        value = substitute_variables(auth.api_key_value, variables)
        if name:
            headers[name] = value

    return headers


def _build_params(
    request: RequestModel, variables: dict[str, str]
) -> dict[str, str]:
    """Build query parameters dict."""
    params: dict[str, str] = {}

    for kv in request.params:
        if kv.enabled and kv.key:
            key = substitute_variables(kv.key, variables)
            value = substitute_variables(kv.value, variables)
            params[key] = value

    # API key as query param
    auth = request.auth
    if auth.auth_type == AuthType.API_KEY and auth.api_key_in == "query":
        name = substitute_variables(auth.api_key_name, variables)
        value = substitute_variables(auth.api_key_value, variables)
        if name:
            params[name] = value

    return params


def _build_auth(
    request: RequestModel, variables: dict[str, str]
) -> httpx.BasicAuth | None:
    """Build httpx auth object for Basic auth."""
    if request.auth.auth_type == AuthType.BASIC:
        username = substitute_variables(request.auth.username, variables)
        password = substitute_variables(request.auth.password, variables)
        return httpx.BasicAuth(username, password)
    return None


def _build_content(
    request: RequestModel, variables: dict[str, str]
) -> tuple[str | None, dict[str, str] | None, dict[str, str]]:
    """Build request body content. Returns (content, data, extra_headers)."""
    extra_headers: dict[str, str] = {}

    if request.body_type == BodyType.NONE or not request.body:
        return None, None, extra_headers

    body_text = substitute_variables(request.body, variables)

    if request.body_type == BodyType.JSON:
        extra_headers["Content-Type"] = "application/json"
        return body_text, None, extra_headers
    elif request.body_type == BodyType.FORM:
        # Parse key=value pairs from body text
        data: dict[str, str] = {}
        for line in body_text.strip().split("\n"):
            line = line.strip()
            if "=" in line:
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip()
        return None, data, extra_headers
    else:  # RAW
        return body_text, None, extra_headers


async def send_request(
    request: RequestModel,
    variables: dict[str, str] | None = None,
    timeout: float = 30.0,
    verify_ssl: bool = True,
) -> ResponseModel:
    """Send an HTTP request and return the response."""
    variables = variables or {}

    url = substitute_variables(request.url, variables)
    headers = _build_headers(request, variables)
    params = _build_params(request, variables)
    auth = _build_auth(request, variables)
    content, data, extra_headers = _build_content(request, variables)

    # Merge extra headers (like Content-Type for JSON)
    for k, v in extra_headers.items():
        if k not in headers:  # Don't override user-set headers
            headers[k] = v

    start_time = time.monotonic()

    async with httpx.AsyncClient(
        verify=verify_ssl,
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        response = await client.request(
            method=request.method.value,
            url=url,
            headers=headers,
            params=params,
            auth=auth,
            content=content,
            data=data,
        )

    elapsed_ms = (time.monotonic() - start_time) * 1000

    # Build response model
    response_headers = dict(response.headers)
    body_text = response.text
    content_type = response.headers.get("content-type", "")

    return ResponseModel(
        status_code=response.status_code,
        reason=response.reason_phrase,
        headers=response_headers,
        body=body_text,
        content_type=content_type,
        elapsed_ms=elapsed_ms,
        size_bytes=len(response.content),
    )
