#!/usr/bin/env python3
"""Command-line interface for denv."""

import argparse
import sys
from .redactor import process_stream


def main():
    """Main entry point for the denv CLI."""
    ap = argparse.ArgumentParser(
        description="Redact .env files (filter). Reads stdin or files; writes to stdout by default.",
        prog="denv",
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

    try:
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
    finally:
        if out is not sys.stdout:
            out.close()


if __name__ == "__main__":
    main()
