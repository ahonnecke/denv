#!/usr/bin/env python3
#
# env_redactor.py — redact .env files from stdin or files.
# Usage examples:
#   cat .env | env_redactor.py
#   env_redactor.py .env > .env.redacted
# Options:
#   --mode values|keys|both     What to redact (default: values)
#   --placeholder TEXT          Replacement text (default: REDACTED)
#   --keep-length               Preserve original value length using '*' characters
#   --strip-secrets             Remove lines that look like secrets entirely
#   -o FILE, --output FILE      Write to file (default stdout)
# Notes:
# - Preserves comments, blank lines, and export prefixes.
# - Handles quoted values, escaped quotes, and inline comments (#) outside quotes.

import argparse, sys, re, hashlib


def find_unquoted_hash(s: str) -> int:
    in_single = in_double = False
    escape = False
    for i, ch in enumerate(s):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return i
    return -1


def split_inline_comment(s: str):
    idx = find_unquoted_hash(s)
    if idx == -1:
        return s, ""
    return s[:idx].rstrip(), s[idx:]


def parse_env_line(line: str):
    original = line
    nl = ""
    if line.endswith("\n"):
        nl = "\n"
        line = line[:-1]

    stripped = line.lstrip()
    leading = line[: len(line) - len(stripped)]
    if stripped == "" or stripped.startswith("#"):
        return {"type": "pass", "leading": leading, "content": stripped, "trailing": nl}

    export = ""
    rest = stripped
    if rest.startswith("export "):
        export = "export "
        rest = rest[len("export ") :].lstrip()

    m = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\s*=\s*(.*)$", rest)
    if not m:
        return {"type": "raw", "content": original}

    key = m.group(1)
    value_part = m.group(2)

    value_core, comment = split_inline_comment(value_part)

    left_pad_len = len(value_core) - len(value_core.lstrip())
    left_pad = value_core[:left_pad_len]
    raw_value = value_core[left_pad_len:]

    return {
        "type": "kv",
        "leading": leading,
        "export": export,
        "key": key,
        "sep": "=",
        "left_pad": left_pad,
        "raw_value": raw_value,
        "comment": comment,
        "trailing": nl,
        "original": original,
    }


def make_placeholder(original_value: str, placeholder: str, keep_length: bool) -> str:
    if keep_length:
        v = original_value
        if (len(v) >= 2) and ((v[0] == v[-1]) and v[0] in ("'", '"')):
            q = v[0]
            inner_len = len(v) - 2
            return q + ("*" * inner_len) + q
        return "*" * len(v) if len(v) > 0 else placeholder
    else:
        v = original_value
        if (len(v) >= 2) and ((v[0] == v[-1]) and v[0] in ("'", '"')):
            q = v[0]
            return q + placeholder + q
        return placeholder


def redact_key_name(name: str) -> str:
    h = hashlib.sha256(name.encode()).hexdigest()[:10].upper()
    return f"VAR_{h}"


def process_line(d, mode, placeholder, keep_length, strip_secrets):
    if d["type"] == "pass":
        return d["leading"] + d["content"] + d["trailing"]
    if d["type"] == "raw":
        return d["content"]
    if d["type"] == "kv":
        likely_secret = any(
            tok in d["key"].lower()
            for tok in [
                "secret",
                "password",
                "passwd",
                "token",
                "apikey",
                "api_key",
                "key",
                "private",
                "credential",
            ]
        )
        if strip_secrets and likely_secret:
            return ""
        key_out = d["key"]
        value_out = d["raw_value"]

        if mode in ("keys", "both"):
            key_out = redact_key_name(key_out)

        if mode in ("values", "both"):
            value_out = make_placeholder(d["raw_value"], placeholder, keep_length)

        # space before comment if there was a value
        space = "" if d["comment"] == "" else " "
        return f'{d["leading"]}{d["export"]}{key_out}{d["sep"]}{d["left_pad"]}{value_out}{space}{d["comment"]}{d["trailing"]}'
    return d.get("original", "")


def process_stream(inp, out, mode, placeholder, keep_length, strip_secrets):
    for line in inp:
        d = parse_env_line(line)
        out.write(process_line(d, mode, placeholder, keep_length, strip_secrets))


def main():
    ap = argparse.ArgumentParser(
        description="Redact .env files (filter). Reads stdin or files; writes to stdout by default."
    )
    ap.add_argument("files", nargs="*", help="Input .env files (default: stdin)")
    ap.add_argument(
        "--mode",
        choices=["values", "keys", "both"],
        default="values",
        help="What to redact (default: values)",
    )
    ap.add_argument(
        "--placeholder",
        default="REDACTED",
        help="Replacement text when not using --keep-length (default: REDACTED)",
    )
    ap.add_argument(
        "--keep-length",
        action="store_true",
        help="Preserve original value length with '*'s (keeps quote style)",
    )
    ap.add_argument(
        "--strip-secrets",
        action="store_true",
        help="Remove lines whose keys look like secrets entirely",
    )
    ap.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = ap.parse_args()

    if args.output:
        out = open(args.output, "w", encoding="utf-8")
    else:
        out = sys.stdout

    if args.files:
        for i, path in enumerate(args.files):
            with open(path, "r", encoding="utf-8") as f:
                process_stream(
                    f,
                    out,
                    args.mode,
                    args.placeholder,
                    args.keep_length,
                    args.strip_secrets,
                )
            if i < len(args.files) - 1:
                out.write("\n")
    else:
        process_stream(
            sys.stdin,
            out,
            args.mode,
            args.placeholder,
            args.keep_length,
            args.strip_secrets,
        )

    if out is not sys.stdout:
        out.close()


if __name__ == "__main__":
    main()
