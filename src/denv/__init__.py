"""denv - A tool for redacting sensitive information from .env files."""

__version__ = "1.0.0"
__author__ = "ahonnecke"

from .redactor import (
    find_unquoted_hash,
    split_inline_comment,
    parse_env_line,
    make_placeholder,
    redact_key_name,
    process_line,
    process_stream,
)

__all__ = [
    "find_unquoted_hash",
    "split_inline_comment",
    "parse_env_line",
    "make_placeholder",
    "redact_key_name",
    "process_line",
    "process_stream",
]
