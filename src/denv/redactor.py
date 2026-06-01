"""Core redaction logic for environment files."""

import re
import hashlib


def find_unquoted_hash(s: str) -> int:
    """Find the position of an unquoted hash character in a string.
    
    Args:
        s: The string to search
        
    Returns:
        The index of the first unquoted hash, or -1 if not found
    """
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
    """Split a string into content and inline comment parts.
    
    Args:
        s: The string to split
        
    Returns:
        A tuple of (content, comment)
    """
    idx = find_unquoted_hash(s)
    if idx == -1:
        return s, ""
    return s[:idx].rstrip(), s[idx:]


def parse_env_line(line: str):
    """Parse a line from an environment file.
    
    Args:
        line: The line to parse
        
    Returns:
        A dictionary containing the parsed components
    """
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
    """Create a placeholder for a redacted value.
    
    Args:
        original_value: The original value to redact
        placeholder: The placeholder text to use
        keep_length: Whether to preserve the original length
        
    Returns:
        The placeholder string
    """
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
    """Redact a key name by hashing it.
    
    Args:
        name: The key name to redact
        
    Returns:
        A redacted key name
    """
    h = hashlib.sha256(name.encode()).hexdigest()[:10].upper()
    return f"VAR_{h}"


def process_line(d, mode, placeholder, keep_length, strip_secrets):
    """Process a parsed line and apply redaction.
    
    Args:
        d: The parsed line dictionary
        mode: Redaction mode ('values', 'keys', or 'both')
        placeholder: The placeholder text
        keep_length: Whether to preserve original length
        strip_secrets: Whether to remove secret lines entirely
        
    Returns:
        The processed line as a string
    """
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
    """Process a stream of lines and apply redaction.
    
    Args:
        inp: Input stream
        out: Output stream
        mode: Redaction mode
        placeholder: Placeholder text
        keep_length: Whether to preserve length
        strip_secrets: Whether to strip secret lines
    """
    for line in inp:
        d = parse_env_line(line)
        out.write(process_line(d, mode, placeholder, keep_length, strip_secrets))
