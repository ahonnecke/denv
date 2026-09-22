"""denv - a durable env-var store (public/secret classification, per-env value
files, push adapters) plus a .env redaction engine."""

__version__ = "2.0.0"
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
from .store import (
    DenvError,
    Manifest,
    denv_home,
    proj_dir,
    parse_manifest,
    load_manifest,
    value_files_for,
    raw_value,
    mask,
    keys_present_in_env,
    adapter_cmd,
    cmd_envs,
    cmd_ls,
    cmd_get,
    cmd_load,
    cmd_push,
    cmd_doctor,
    cmd_init,
)

__all__ = [
    # redactor
    "find_unquoted_hash",
    "split_inline_comment",
    "parse_env_line",
    "make_placeholder",
    "redact_key_name",
    "process_line",
    "process_stream",
    # store
    "DenvError",
    "Manifest",
    "denv_home",
    "proj_dir",
    "parse_manifest",
    "load_manifest",
    "value_files_for",
    "raw_value",
    "mask",
    "keys_present_in_env",
    "adapter_cmd",
    "cmd_envs",
    "cmd_ls",
    "cmd_get",
    "cmd_load",
    "cmd_push",
    "cmd_doctor",
    "cmd_init",
]
