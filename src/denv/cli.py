#!/usr/bin/env python3
"""Command-line interface for denv — an env-var store plus a .env redactor."""

import argparse
import sys

from . import store
from .redactor import process_stream


def _run_redact(args) -> None:
    """Run the redactor (the original ``denv`` behavior, now ``denv redact``)."""
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


def _add_redact_parser(sub) -> None:
    """Add the ``redact`` subparser (unchanged redactor options)."""
    p = sub.add_parser(
        "redact",
        help="Redact .env files (filter). Reads stdin or files; writes stdout by default.",
        description="Redact .env files (filter). Reads stdin or files; writes to stdout by default.",
    )
    p.add_argument("files", nargs="*", help="Input .env files (default: stdin)")
    p.add_argument(
        "--mode",
        choices=["values", "keys", "both"],
        default="values",
        help="What to redact (default: values)",
    )
    p.add_argument(
        "--placeholder",
        default="REDACTED",
        help="Replacement text when not using --keep-length (default: REDACTED)",
    )
    p.add_argument(
        "--keep-length",
        action="store_true",
        help="Preserve original value length with '*'s (keeps quote style)",
    )
    p.add_argument(
        "--strip-secrets",
        action="store_true",
        help="Remove lines whose keys look like secrets entirely",
    )
    p.add_argument("-o", "--output", help="Output file (default: stdout)")
    p.set_defaults(func=_run_redact)


def _add_store_parsers(sub) -> None:
    """Add the store-manager subparsers ported from the bash reference."""
    p = sub.add_parser("ls", help="List keys: class, llm, value|mask (presence for secrets)")
    p.add_argument("project")
    p.add_argument("env", nargs="?", default=None)
    p.set_defaults(func=lambda a: store.cmd_ls(a.project, a.env))

    p = sub.add_parser("get", help="Print one key's value (public/--unmask) or SET/MISSING")
    p.add_argument("project")
    p.add_argument("env")
    p.add_argument("key")
    p.add_argument("--unmask", action="store_true", help="Show the raw value even if secret")
    p.set_defaults(func=lambda a: store.cmd_get(a.project, a.env, a.key, a.unmask))

    p = sub.add_parser("load", help="Write a merged env file; never prints values")
    p.add_argument("project")
    p.add_argument("env")
    p.add_argument("--to", default="./.env", help="Output file (default: ./.env)")
    p.add_argument(
        "--redacted",
        action="store_true",
        help="Redact secret values in the written file (safe to share)",
    )
    p.add_argument(
        "--allow-external",
        action="store_true",
        help="Permit --to outside the current directory tree (default: refused, "
        "so secrets can't leak to /tmp/~/etc.)",
    )
    p.set_defaults(
        func=lambda a: store.cmd_load(a.project, a.env, a.to, a.redacted, a.allow_external)
    )

    p = sub.add_parser("push", help="Dry-run push plan by default; --apply executes")
    p.add_argument("project")
    p.add_argument("env")
    p.add_argument("--apply", action="store_true", help="Execute the push commands")
    p.set_defaults(func=lambda a: store.cmd_push(a.project, a.env, a.apply))

    p = sub.add_parser("doctor", help="Manifest vs value files: missing/undeclared/perms")
    p.add_argument("project")
    p.set_defaults(func=lambda a: store.cmd_doctor(a.project))

    p = sub.add_parser("envs", help="Print declared envs, one per line")
    p.add_argument("project")
    p.set_defaults(func=lambda a: store.cmd_envs(a.project))

    p = sub.add_parser("init", help="Scaffold a new store (manifest + value files, 600)")
    p.add_argument("project")
    p.add_argument("envs", nargs="*", help="Envs to scaffold (default: dev)")
    p.set_defaults(func=lambda a: store.cmd_init(a.project, a.envs))

    p = sub.add_parser("link", help="Write a committable .denv repo pointer (project + env)")
    p.add_argument("project")
    p.add_argument("env")
    p.add_argument("--to", default=store.POINTER, help=f"Pointer path (default: {store.POINTER})")
    p.set_defaults(func=lambda a: store.cmd_link(a.project, a.env, a.to))

    # `exec` captures its tail with REMAINDER so the command's own flags and the
    # `--` separator pass through untouched; _run_exec splits them (add_help=False
    # so a `-h` in the command is not hijacked).
    p = sub.add_parser(
        "exec",
        help="Run a command with the merged env injected (no file; reads .denv)",
        add_help=False,
    )
    p.add_argument("rest", nargs=argparse.REMAINDER)
    p.set_defaults(func=lambda a: _run_exec(a.rest))


_EXEC_USAGE = """\
usage: denv exec [project [env]] -- <command> ...

Run <command> with the project's merged env injected into its environment
(no file written; secrets live only in the child process).

Resolving the target:
  denv exec -- <cmd>              project + env from the nearest .denv pointer
  denv exec <env> -- <cmd>        project from .denv, env overridden
  denv exec <project> <env> -- <cmd>   fully explicit (no pointer needed)

Adopt denv in a repo:  denv link <project> <env>   (writes a committable .denv)

The child sees DENV_ACTIVE=1, DENV_PROJECT, DENV_ENV — a script can use these to
trust the injected env and skip sourcing its own fallback .env files."""


def _run_exec(rest) -> None:
    """Split ``[project [env]] -- cmd...`` deterministically and run cmd_exec."""
    rest = list(rest or [])
    if not rest or rest[0] in ("-h", "--help"):
        print(_EXEC_USAGE)
        return
    if "--" in rest:
        i = rest.index("--")
        pre, cmd = rest[:i], rest[i + 1:]
    else:
        pre, cmd = [], rest  # no `--`: whole tail is the command, target from .denv
    if len(pre) == 0:
        project, env = None, None
    elif len(pre) == 1:
        project, env = None, pre[0]  # a lone positional is the env override
    elif len(pre) == 2:
        project, env = pre[0], pre[1]
    else:
        raise store.DenvError(
            f"exec takes at most `project env` before `--`, got {pre!r}\n{_EXEC_USAGE}"
        )
    store.cmd_exec(project, env, cmd)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands."""
    ap = argparse.ArgumentParser(
        prog="denv",
        description="Durable env-var store (public/secret classification, per-env "
        "value files, push adapters) plus a .env redactor.",
    )
    sub = ap.add_subparsers(dest="command", metavar="<command>")
    _add_store_parsers(sub)
    _add_redact_parser(sub)
    return ap


def main(argv=None) -> None:
    """Main entry point for the denv CLI."""
    argv = list(sys.argv[1:] if argv is None else argv)
    # `exec` is parsed by hand: argparse's REMAINDER mishandles a leading flag
    # (e.g. `denv exec -h`), and we want the command's tail wholly untouched.
    if argv and argv[0] == "exec":
        try:
            _run_exec(argv[1:])
        except store.DenvError as exc:
            print(f"{store.SELF}: {exc}", file=sys.stderr)
            sys.exit(2)
        return
    ap = build_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        ap.print_help()
        sys.exit(2)
    try:
        args.func(args)
    except store.DenvError as exc:
        print(f"{store.SELF}: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
