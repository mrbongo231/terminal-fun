"""cURL command import/export for ReqCraft."""

from __future__ import annotations

import re
import shlex
from urllib.parse import parse_qs, urlparse, urlencode, urlunparse

from reqcraft.models import (
    AuthConfig,
    AuthType,
    BodyType,
    HttpMethod,
    KeyValuePair,
    RequestModel,
)


def parse_curl(curl_command: str) -> RequestModel:
    """Parse a cURL command string into a RequestModel.

    Handles common curl flags:
        -X / --request: HTTP method
        -H / --header: Headers
        -d / --data / --data-raw / --data-binary: Request body
        -u / --user: Basic auth
        -A / --user-agent: User agent
        --compressed: Accept-Encoding
        -b / --cookie: Cookies
        -L / --location: (ignored, we always follow redirects)
    """
    # Normalize the command — join continuation lines
    command = curl_command.strip()
    command = command.replace("\\\n", " ").replace("\\\r\n", " ")

    # Remove 'curl' prefix if present
    if command.lower().startswith("curl "):
        command = command[5:]
    elif command.lower() == "curl":
        return RequestModel()

    # Tokenise using shlex for proper quote handling
    try:
        tokens = shlex.split(command)
    except ValueError:
        # If shlex can't parse (unbalanced quotes, etc.), try basic split
        tokens = command.split()

    method = HttpMethod.GET
    url = ""
    headers: list[KeyValuePair] = []
    body = ""
    body_type = BodyType.NONE
    auth = AuthConfig()
    has_explicit_method = False

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ("-X", "--request"):
            i += 1
            if i < len(tokens):
                method_str = tokens[i].upper()
                try:
                    method = HttpMethod(method_str)
                except ValueError:
                    method = HttpMethod.GET
                has_explicit_method = True

        elif token in ("-H", "--header"):
            i += 1
            if i < len(tokens):
                header_str = tokens[i]
                if ":" in header_str:
                    key, _, value = header_str.partition(":")
                    headers.append(
                        KeyValuePair(key=key.strip(), value=value.strip())
                    )

        elif token in ("-d", "--data", "--data-raw", "--data-binary"):
            i += 1
            if i < len(tokens):
                body = tokens[i]
                # Detect JSON vs form
                body_stripped = body.strip()
                if body_stripped.startswith("{") or body_stripped.startswith("["):
                    body_type = BodyType.JSON
                elif "=" in body and not body_stripped.startswith("<"):
                    body_type = BodyType.FORM
                else:
                    body_type = BodyType.RAW

                if not has_explicit_method:
                    method = HttpMethod.POST

        elif token in ("-u", "--user"):
            i += 1
            if i < len(tokens):
                user_str = tokens[i]
                if ":" in user_str:
                    username, _, password = user_str.partition(":")
                    auth = AuthConfig(
                        auth_type=AuthType.BASIC,
                        username=username,
                        password=password,
                    )
                else:
                    auth = AuthConfig(
                        auth_type=AuthType.BASIC,
                        username=user_str,
                    )

        elif token in ("-A", "--user-agent"):
            i += 1
            if i < len(tokens):
                headers.append(
                    KeyValuePair(key="User-Agent", value=tokens[i])
                )

        elif token in ("-b", "--cookie"):
            i += 1
            if i < len(tokens):
                headers.append(
                    KeyValuePair(key="Cookie", value=tokens[i])
                )

        elif token in (
            "-L", "--location", "--compressed", "-s", "--silent",
            "-S", "--show-error", "-k", "--insecure", "-v", "--verbose",
            "-i", "--include",
        ):
            pass  # Ignore these flags

        elif token.startswith("-"):
            # Unknown flag — skip its value if it looks like a flag with arg
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                i += 1

        else:
            # Positional argument — likely the URL
            if not url:
                url = token

        i += 1

    # Extract query params from URL
    params: list[KeyValuePair] = []
    if url:
        parsed = urlparse(url)
        if parsed.query:
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            for key, values in query_params.items():
                for value in values:
                    params.append(KeyValuePair(key=key, value=value))
            # Rebuild URL without query string
            url = urlunparse(parsed._replace(query=""))

    # Check Authorization header for Bearer token
    for h in headers:
        if h.key.lower() == "authorization":
            value = h.value
            if value.lower().startswith("bearer "):
                auth = AuthConfig(
                    auth_type=AuthType.BEARER,
                    token=value[7:],
                )
                headers.remove(h)
                break

    return RequestModel(
        method=method,
        url=url,
        headers=headers,
        params=params,
        body=body,
        body_type=body_type,
        auth=auth,
    )


def to_curl(request: RequestModel, variables: dict[str, str] | None = None) -> str:
    """Export a RequestModel as a cURL command string."""
    from reqcraft.http_client import substitute_variables

    variables = variables or {}

    parts = ["curl"]

    # Method (only if not GET)
    if request.method != HttpMethod.GET:
        parts.append(f"-X {request.method.value}")

    # URL with query params
    url = substitute_variables(request.url, variables)
    if request.params:
        active_params = [p for p in request.params if p.enabled and p.key]
        if active_params:
            query = urlencode(
                [
                    (
                        substitute_variables(p.key, variables),
                        substitute_variables(p.value, variables),
                    )
                    for p in active_params
                ]
            )
            url = f"{url}?{query}"

    parts.append(f"'{url}'")

    # Headers
    for h in request.headers:
        if h.enabled and h.key:
            key = substitute_variables(h.key, variables)
            value = substitute_variables(h.value, variables)
            parts.append(f"-H '{key}: {value}'")

    # Auth
    if request.auth.auth_type == AuthType.BASIC:
        username = substitute_variables(request.auth.username, variables)
        password = substitute_variables(request.auth.password, variables)
        parts.append(f"-u '{username}:{password}'")
    elif request.auth.auth_type == AuthType.BEARER:
        token = substitute_variables(request.auth.token, variables)
        parts.append(f"-H 'Authorization: Bearer {token}'")
    elif request.auth.auth_type == AuthType.API_KEY:
        name = substitute_variables(request.auth.api_key_name, variables)
        value = substitute_variables(request.auth.api_key_value, variables)
        if request.auth.api_key_in == "header":
            parts.append(f"-H '{name}: {value}'")
        # If query, it's already in the URL params

    # Body
    if request.body_type != BodyType.NONE and request.body:
        body = substitute_variables(request.body, variables)
        # Escape single quotes in body
        body_escaped = body.replace("'", "'\\''")
        parts.append(f"--data-raw '{body_escaped}'")
        if request.body_type == BodyType.JSON:
            # Add Content-Type if not already in headers
            has_ct = any(
                h.key.lower() == "content-type"
                for h in request.headers
                if h.enabled
            )
            if not has_ct:
                parts.append("-H 'Content-Type: application/json'")

    return " \\\n  ".join(parts)
