"""Tests for the redactor module."""

import pytest
from denv.redactor import (
    find_unquoted_hash,
    split_inline_comment,
    parse_env_line,
    make_placeholder,
    redact_key_name,
    process_line,
)


class TestFindUnquotedHash:
    """Tests for find_unquoted_hash function."""

    def test_no_hash(self):
        assert find_unquoted_hash("no hash here") == -1

    def test_simple_hash(self):
        assert find_unquoted_hash("value # comment") == 6

    def test_hash_in_double_quotes(self):
        assert find_unquoted_hash('"value # inside"') == -1

    def test_hash_in_single_quotes(self):
        assert find_unquoted_hash("'value # inside'") == -1

    def test_hash_after_quotes(self):
        assert find_unquoted_hash('"value" # comment') == 8

    def test_escaped_quote(self):
        assert find_unquoted_hash('"value \\" # still inside" # outside') == 27


class TestSplitInlineComment:
    """Tests for split_inline_comment function."""

    def test_no_comment(self):
        content, comment = split_inline_comment("just value")
        assert content == "just value"
        assert comment == ""

    def test_with_comment(self):
        content, comment = split_inline_comment("value # comment")
        assert content == "value"
        assert comment == "# comment"

    def test_hash_in_quotes(self):
        content, comment = split_inline_comment('"value#inside" # outside')
        assert content == '"value#inside"'
        assert comment == "# outside"


class TestParseEnvLine:
    """Tests for parse_env_line function."""

    def test_blank_line(self):
        result = parse_env_line("\n")
        assert result["type"] == "pass"

    def test_comment_line(self):
        result = parse_env_line("# This is a comment\n")
        assert result["type"] == "pass"
        assert result["content"] == "# This is a comment"

    def test_simple_key_value(self):
        result = parse_env_line("KEY=value\n")
        assert result["type"] == "kv"
        assert result["key"] == "KEY"
        assert result["raw_value"] == "value"

    def test_quoted_value(self):
        result = parse_env_line('KEY="value"\n')
        assert result["type"] == "kv"
        assert result["key"] == "KEY"
        assert result["raw_value"] == '"value"'

    def test_export_statement(self):
        result = parse_env_line("export KEY=value\n")
        assert result["type"] == "kv"
        assert result["export"] == "export "
        assert result["key"] == "KEY"
        assert result["raw_value"] == "value"

    def test_inline_comment(self):
        result = parse_env_line("KEY=value # comment\n")
        assert result["type"] == "kv"
        assert result["key"] == "KEY"
        assert result["raw_value"] == "value"
        assert result["comment"] == "# comment"

    def test_leading_whitespace(self):
        result = parse_env_line("  KEY=value\n")
        assert result["type"] == "kv"
        assert result["leading"] == "  "
        assert result["key"] == "KEY"


class TestMakePlaceholder:
    """Tests for make_placeholder function."""

    def test_simple_placeholder(self):
        result = make_placeholder("secret", "REDACTED", False)
        assert result == "REDACTED"

    def test_quoted_placeholder(self):
        result = make_placeholder('"secret"', "REDACTED", False)
        assert result == '"REDACTED"'

    def test_keep_length_unquoted(self):
        result = make_placeholder("secret", "REDACTED", True)
        assert result == "******"

    def test_keep_length_quoted(self):
        result = make_placeholder('"secret"', "REDACTED", True)
        assert result == '"******"'

    def test_single_quotes(self):
        result = make_placeholder("'secret'", "REDACTED", False)
        assert result == "'REDACTED'"


class TestRedactKeyName:
    """Tests for redact_key_name function."""

    def test_redact_key(self):
        result = redact_key_name("DATABASE_URL")
        assert result.startswith("VAR_")
        assert len(result) == 14  # VAR_ + 10 hex chars

    def test_consistent_hashing(self):
        result1 = redact_key_name("API_KEY")
        result2 = redact_key_name("API_KEY")
        assert result1 == result2

    def test_different_keys(self):
        result1 = redact_key_name("KEY1")
        result2 = redact_key_name("KEY2")
        assert result1 != result2


class TestProcessLine:
    """Tests for process_line function."""

    def test_pass_through_comment(self):
        parsed = {"type": "pass", "leading": "", "content": "# comment", "trailing": "\n"}
        result = process_line(parsed, "values", "REDACTED", False, False)
        assert result == "# comment\n"

    def test_redact_value(self):
        parsed = {
            "type": "kv",
            "leading": "",
            "export": "",
            "key": "KEY",
            "sep": "=",
            "left_pad": "",
            "raw_value": "secret",
            "comment": "",
            "trailing": "\n",
        }
        result = process_line(parsed, "values", "REDACTED", False, False)
        assert result == "KEY=REDACTED\n"

    def test_redact_key(self):
        parsed = {
            "type": "kv",
            "leading": "",
            "export": "",
            "key": "SECRET_KEY",
            "sep": "=",
            "left_pad": "",
            "raw_value": "value",
            "comment": "",
            "trailing": "\n",
        }
        result = process_line(parsed, "keys", "REDACTED", False, False)
        assert result.startswith("VAR_")
        assert "=value\n" in result

    def test_strip_secrets(self):
        parsed = {
            "type": "kv",
            "leading": "",
            "export": "",
            "key": "API_KEY",
            "sep": "=",
            "left_pad": "",
            "raw_value": "secret",
            "comment": "",
            "trailing": "\n",
        }
        result = process_line(parsed, "values", "REDACTED", False, True)
        assert result == ""

    def test_preserve_export(self):
        parsed = {
            "type": "kv",
            "leading": "",
            "export": "export ",
            "key": "KEY",
            "sep": "=",
            "left_pad": "",
            "raw_value": "value",
            "comment": "",
            "trailing": "\n",
        }
        result = process_line(parsed, "values", "REDACTED", False, False)
        assert result == "export KEY=REDACTED\n"

    def test_preserve_inline_comment(self):
        parsed = {
            "type": "kv",
            "leading": "",
            "export": "",
            "key": "KEY",
            "sep": "=",
            "left_pad": "",
            "raw_value": "value",
            "comment": "# comment",
            "trailing": "\n",
        }
        result = process_line(parsed, "values", "REDACTED", False, False)
        assert result == "KEY=REDACTED # comment\n"
