"""Tests for cURL parser and exporter."""

from reqcraft.curl_parser import parse_curl, to_curl
from reqcraft.models import (
    AuthType,
    BodyType,
    HttpMethod,
    KeyValuePair,
    RequestModel,
    AuthConfig,
)


class TestParseCurl:
    def test_simple_get(self):
        req = parse_curl("curl https://api.example.com/users")
        assert req.method == HttpMethod.GET
        assert req.url == "https://api.example.com/users"

    def test_explicit_method(self):
        req = parse_curl("curl -X DELETE https://api.example.com/users/1")
        assert req.method == HttpMethod.DELETE

    def test_headers(self):
        req = parse_curl(
            'curl -H "Content-Type: application/json" '
            '-H "Authorization: Bearer mytoken" '
            "https://api.example.com"
        )
        # Authorization header should be parsed into auth config
        assert req.auth.auth_type == AuthType.BEARER
        assert req.auth.token == "mytoken"
        # Content-Type should remain as a header
        assert any(h.key == "Content-Type" for h in req.headers)

    def test_post_with_data(self):
        req = parse_curl(
            'curl -X POST https://api.example.com/users '
            '-d \'{"name": "John"}\''
        )
        assert req.method == HttpMethod.POST
        assert req.body_type == BodyType.JSON
        assert "John" in req.body

    def test_implicit_post_with_data(self):
        req = parse_curl(
            'curl https://api.example.com/login -d "user=admin&pass=secret"'
        )
        assert req.method == HttpMethod.POST  # Implicit POST when -d is used
        assert req.body_type == BodyType.FORM

    def test_basic_auth(self):
        req = parse_curl("curl -u admin:password https://api.example.com")
        assert req.auth.auth_type == AuthType.BASIC
        assert req.auth.username == "admin"
        assert req.auth.password == "password"

    def test_query_params_extracted(self):
        req = parse_curl(
            "curl 'https://api.example.com/search?q=hello&page=2'"
        )
        assert req.url == "https://api.example.com/search"
        assert len(req.params) == 2
        assert any(p.key == "q" and p.value == "hello" for p in req.params)
        assert any(p.key == "page" and p.value == "2" for p in req.params)

    def test_multiline_command(self):
        req = parse_curl(
            "curl \\\n"
            "  -X POST \\\n"
            "  https://api.example.com/data \\\n"
            "  -H 'Accept: application/json'"
        )
        assert req.method == HttpMethod.POST
        assert req.url == "https://api.example.com/data"
        assert any(h.key == "Accept" for h in req.headers)

    def test_empty_curl(self):
        req = parse_curl("curl")
        assert req.method == HttpMethod.GET
        assert req.url == ""


class TestToCurl:
    def test_simple_get(self):
        req = RequestModel(
            method=HttpMethod.GET,
            url="https://api.example.com/users",
        )
        result = to_curl(req)
        assert "curl" in result
        assert "https://api.example.com/users" in result
        assert "-X" not in result  # GET is default

    def test_post_with_body(self):
        req = RequestModel(
            method=HttpMethod.POST,
            url="https://api.example.com/users",
            body='{"name": "test"}',
            body_type=BodyType.JSON,
        )
        result = to_curl(req)
        assert "-X POST" in result
        assert "--data-raw" in result
        assert "Content-Type: application/json" in result

    def test_with_headers(self):
        req = RequestModel(
            method=HttpMethod.GET,
            url="https://api.example.com",
            headers=[KeyValuePair(key="Accept", value="application/json")],
        )
        result = to_curl(req)
        assert "-H" in result
        assert "Accept: application/json" in result

    def test_with_params(self):
        req = RequestModel(
            method=HttpMethod.GET,
            url="https://api.example.com/search",
            params=[
                KeyValuePair(key="q", value="test"),
                KeyValuePair(key="page", value="1"),
            ],
        )
        result = to_curl(req)
        assert "q=test" in result
        assert "page=1" in result

    def test_with_bearer_auth(self):
        req = RequestModel(
            method=HttpMethod.GET,
            url="https://api.example.com",
            auth=AuthConfig(auth_type=AuthType.BEARER, token="mytoken"),
        )
        result = to_curl(req)
        assert "Authorization: Bearer mytoken" in result

    def test_with_basic_auth(self):
        req = RequestModel(
            method=HttpMethod.GET,
            url="https://api.example.com",
            auth=AuthConfig(
                auth_type=AuthType.BASIC,
                username="user",
                password="pass",
            ),
        )
        result = to_curl(req)
        assert "-u" in result
        assert "user:pass" in result

    def test_with_variable_substitution(self):
        req = RequestModel(
            method=HttpMethod.GET,
            url="{{base_url}}/users",
        )
        variables = {"base_url": "https://api.example.com"}
        result = to_curl(req, variables)
        assert "https://api.example.com/users" in result
