# denv — narrative

## Goal
One reusable tool for a project's environment variables across all three consumers — the local
app, the deployed environment (staging/prod), and an LLM session — where secrets are safe to
expose by construction. A project just says "use `~/src/denv`".

## Arc (2026-09-21)
This repo began as a `.env` **redactor** (Python, tested). Separately, a **store-manager** was
prototyped in bash (in claude-config) generalizing chitchat's `~/.config/<project>/` + four-homes
model: per-project manifest classifying keys `public|secret` × `llm:read|blind`, per-env value
files, and pluggable deploy `push` adapters. They were two halves of one product with a name
collision. Decision: **unify into this one Python package** — store-manager subcommands + the
redactor — because the redactor is exactly the "LLM sees safe output, not raw secrets" mechanism
the store needs. Reuse-before-invent.

## State (unified, done)
- `src/denv/store.py` — store logic (manifest parse, per-env value resolution incl. env-scoped
  `from:<env>=<file>`, ls/get/load/push/doctor/init/envs, push adapters).
- `src/denv/cli.py` — argparse subcommands: `init ls get load push doctor envs` + `redact`
  (the original redactor). `load --redacted` renders a shareable copy: manifest classification
  decides what's secret, `redactor` renders it.
- `redactor.py` kept and reused; suite green (67 passed; fixed 2 pre-existing off-by-one test
  assertions). Byte-identical parity with the retired bash version on the real stores; the port
  also fixed a `set -u` bug where bash `doctor` aborted on a project with no `from:` keys.
- Installed via `make install` (venv + `~/.local/bin/denv` symlink). Bash version retired from
  claude-config (pointer left in its REFERENCE.md).
- Direnv-prompt cruft split out to `~/src/project-context/`.
- Onboarded stores live in `~/.config/`: `encore_werks` (greenfield), `chitchat` (descriptive
  map of a legacy mixed layout; deployed config still Spaces-owned).
- **Scope reduction (2026-09-29, #1):** `load --to` is now confined to the current directory
  tree — a target under `/tmp`, `~`, `../..` is refused (canonicalizes `..`/symlinks first),
  `--allow-external` overrides. Root cause: unconstrained `--to` let sessions/scripts render
  full unredacted secrets to `/tmp` (chitchat's `/tmp/prod.backend.env` etc.), defeating
  "secrets safe by construction." 4 new tests; suite 71 green.

- **Consumption ergonomics (2026-10-12):** the only way to feed a project's env to a
  consumer was `load --to <file>` + source it — per-project boilerplate, a secret file at
  rest, the `--to` tree-confinement dance, and a README prose step to adopt. Root-cause fix:
  make consumption first-class. `denv exec [project [env]] -- <cmd>` injects the merged env
  into a child process (no file; reuses `keys_present_in_env`/`raw_value`, then `execvpe`).
  A committable `.denv` repo pointer (`project` + default `env`, non-secret) lets a repo
  *be* a denv consumer by committing one file; `denv exec` resolves project/env from it
  (1 positional = env override, 2 = explicit project+env). `denv link <project> <env>`
  writes the pointer. `load --to` stays for genuine file-consumers (docker compose
  `--env-file`). encore_werks migrated: `.denv` committed, `db_sync.sh` sourcing loop
  removed, `.env.dev.ops` retired.

## NEXT
- Push both repos (this + claude-config) once reviewed — user's call.
- Real `push --apply` adapters get exercised as each env is first deployed (dry-run until then).
- `paypal.txt` in `~/.config/chitchat/` is confirmed dead/redundant — delete on user go.
- Optional: add a `denv` dev dep pin / CI; publish to PyPI if ever wanted (packaging is ready).
