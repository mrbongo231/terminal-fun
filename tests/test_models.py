"""Tests for data models."""

from reqcraft.models import (
    AuthConfig,
    AuthType,
    BodyType,
    Collection,
    Environment,
    HistoryEntry,
    HttpMethod,
    KeyValuePair,
    RequestModel,
    ResponseModel,
)


class TestKeyValuePair:
    def test_create_default(self):
        kv = KeyValuePair()
        assert kv.key == ""
        assert kv.value == ""
        assert kv.enabled is True

    def test_round_trip(self):
        kv = KeyValuePair(key="X-Auth", value="token123", enabled=False)
        d = kv.to_dict()
        kv2 = KeyValuePair.from_dict(d)
        assert kv2.key == "X-Auth"
        assert kv2.value == "token123"
        assert kv2.enabled is False


class TestRequestModel:
    def test_create_default(self):
        req = RequestModel()
        assert req.method == HttpMethod.GET
        assert req.url == ""
        assert req.headers == []
        assert req.body_type == BodyType.NONE

    def test_round_trip(self):
        req = RequestModel(
            method=HttpMethod.POST,
            url="https://api.example.com/users",
            headers=[KeyValuePair(key="Content-Type", value="application/json")],
            params=[KeyValuePair(key="page", value="1")],
            body='{"name": "test"}',
            body_type=BodyType.JSON,
            auth=AuthConfig(auth_type=AuthType.BEARER, token="mytoken"),
        )
        d = req.to_dict()
        req2 = RequestModel.from_dict(d)
        assert req2.method == HttpMethod.POST
        assert req2.url == "https://api.example.com/users"
        assert len(req2.headers) == 1
        assert req2.headers[0].key == "Content-Type"
        assert req2.body_type == BodyType.JSON
        assert req2.auth.auth_type == AuthType.BEARER
        assert req2.auth.token == "mytoken"

    def test_display_name_with_name(self):
        req = RequestModel(name="Get Users", url="https://api.example.com/users")
        assert req.display_name() == "Get Users"

    def test_display_name_from_url(self):
        req = RequestModel(url="https://api.example.com/users")
        assert "GET" in req.display_name()
        assert "/users" in req.display_name()


class TestResponseModel:
    def test_status_class(self):
        assert ResponseModel(status_code=200).status_class == "status-2xx"
        assert ResponseModel(status_code=301).status_class == "status-3xx"
        assert ResponseModel(status_code=404).status_class == "status-4xx"
        assert ResponseModel(status_code=500).status_class == "status-5xx"

    def test_formatted_size(self):
        assert "B" in ResponseModel(size_bytes=500).formatted_size
        assert "KB" in ResponseModel(size_bytes=2048).formatted_size
        assert "MB" in ResponseModel(size_bytes=2_000_000).formatted_size

    def test_round_trip(self):
        resp = ResponseModel(
            status_code=200,
            reason="OK",
            headers={"Content-Type": "application/json"},
            body='{"ok": true}',
            elapsed_ms=42.5,
            size_bytes=12,
        )
        d = resp.to_dict()
        resp2 = ResponseModel.from_dict(d)
        assert resp2.status_code == 200
        assert resp2.body == '{"ok": true}'


class TestCollection:
    def test_round_trip(self):
        col = Collection(
            name="My API",
            requests=[
                RequestModel(method=HttpMethod.GET, url="https://example.com"),
            ],
        )
        d = col.to_dict()
        col2 = Collection.from_dict(d)
        assert col2.name == "My API"
        assert len(col2.requests) == 1


class TestEnvironment:
    def test_round_trip(self):
        env = Environment(
            name="Production",
            variables={"base_url": "https://api.prod.com", "api_key": "secret"},
            is_active=True,
        )
        d = env.to_dict()
        env2 = Environment.from_dict(d)
        assert env2.name == "Production"
        assert env2.variables["base_url"] == "https://api.prod.com"
        assert env2.is_active is True


class TestHistoryEntry:
    def test_round_trip(self):
        entry = HistoryEntry(
            request=RequestModel(method=HttpMethod.GET, url="https://example.com"),
            response=ResponseModel(status_code=200, reason="OK"),
        )
        d = entry.to_dict()
        entry2 = HistoryEntry.from_dict(d)
        assert entry2.request.url == "https://example.com"
        assert entry2.response.status_code == 200

    def test_round_trip_with_error(self):
        entry = HistoryEntry(
            request=RequestModel(),
            error="Connection refused",
        )
        d = entry.to_dict()
        entry2 = HistoryEntry.from_dict(d)
        assert entry2.error == "Connection refused"
        assert entry2.response is None
