"""Tests for variable substitution in HTTP client."""

from reqcraft.http_client import substitute_variables


class TestSubstituteVariables:
    def test_simple_substitution(self):
        result = substitute_variables(
            "{{base_url}}/users",
            {"base_url": "https://api.example.com"},
        )
        assert result == "https://api.example.com/users"

    def test_multiple_variables(self):
        result = substitute_variables(
            "{{base_url}}/{{version}}/users",
            {"base_url": "https://api.example.com", "version": "v2"},
        )
        assert result == "https://api.example.com/v2/users"

    def test_unknown_variable_preserved(self):
        result = substitute_variables(
            "{{base_url}}/{{unknown}}/users",
            {"base_url": "https://api.example.com"},
        )
        assert result == "https://api.example.com/{{unknown}}/users"

    def test_empty_variables(self):
        result = substitute_variables("{{base_url}}/users", {})
        assert result == "{{base_url}}/users"

    def test_no_variables_in_text(self):
        result = substitute_variables(
            "https://api.example.com/users",
            {"base_url": "something"},
        )
        assert result == "https://api.example.com/users"

    def test_spaces_in_braces(self):
        result = substitute_variables(
            "{{ base_url }}/users",
            {"base_url": "https://api.example.com"},
        )
        assert result == "https://api.example.com/users"

    def test_empty_text(self):
        result = substitute_variables("", {"key": "val"})
        assert result == ""

    def test_none_variables(self):
        result = substitute_variables("{{key}}", None)
        assert result == "{{key}}"
