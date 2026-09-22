# denv — durable per-project env store + redactor

`denv` is the single source of truth for a project's environment variables, safe to expose to
all three consumers: the **local app**, the **deployed environment** (staging/prod), and an
**LLM session**. It stores env vars once per project in `~/.config/<project>/`, classifies each
key `public|secret`, and renders secret-safe output by construction — the same engine that
powers its standalone `.env` redactor.

- **Store**: per-project value files + a manifest that classifies keys and declares deploy targets.
- **Redact**: turn any `.env` (or a stored env) into a shareable/loggable copy with secrets removed.

Point a project at this repo: **"use `~/src/denv`"** — this README is the guide; `denv --help`
is the command reference.

## Install

```sh
cd ~/src/denv && make install     # venv + editable install + symlink `denv` onto ~/.local/bin
denv --help
```

## Mental model

- **One store per project:** `~/.config/<project>/` — plaintext, mode 600, local-only (not
  committed; "durable" = your machine's backups). Override the root with `DENV_HOME`.
- **`manifest` classifies each key** `public|secret` × `llm:read|llm:blind`. This is the **LLM
  safety boundary**, not just file perms:
  - `ls` / `get` print `public` values but mask `secret` ones to `SET` / `MISSING`.
  - `load` writes a 600 env file and **never prints values**; `load --redacted` writes a
    shareable copy with secret values replaced.
  - `push` prints a masked plan and only executes with `--apply`.
- **Value files:** `common.env` (all envs) + `<env>.env` (per env, overrides common). A legacy
  flat `.env` is read as a fallback when neither exists.
- **`push` deploys an env** via a pluggable adapter: `vercel | gh | supabase | cloudflare |
  spaces | none`.

## Onboard a project (from any repo — the store lives in `~/.config`, never the repo)

```sh
denv init myproj dev staging prod      # scaffold ~/.config/myproj/{manifest,common.env,<env>.env} (600)
$EDITOR ~/.config/myproj/prod.env      # KEY=VALUE per env; common.env for shared
$EDITOR ~/.config/myproj/manifest      # classify keys + set push targets (grammar below)
denv ls myproj                         # verify: public values shown, secrets masked
denv doctor myproj                     # perms + declared-vs-present check
```

An **existing store with a flat `.env`** needs no init — drop a `manifest` beside it (the flat
`.env` is read as a fallback).

## Commands

```sh
denv ls     myproj [env]               # keys × class × llm × value|mask
denv get    myproj prod API_URL        # one value (add --unmask to reveal a secret)
denv load   myproj dev --to .env       # LOCAL APP: write a 600 .env, values never printed
denv load   myproj dev --redacted      # a shareable/loggable copy: secret values redacted
denv push   myproj prod                # DEPLOY: dry-run plan; add --apply to execute
denv doctor myproj                     # perms (incl. from: files) + declared-vs-present
denv envs   myproj
denv init   myproj [env ...]
denv redact [file ...] [--mode values|keys|both] [--keep-length] [--strip-secrets] [-o OUT]
```

## Manifest grammar

```
project  <name>
envs     <e1> <e2> ...
default_class  public|secret            # keys not listed default here (default: secret)
default_llm    read|blind               #                              (default: blind)
push  <env>  <adapter> [args...]         # vercel|gh|supabase|cloudflare|spaces|none
key   <NAME> <public|secret> [llm:read|llm:blind] [from:<file>] [from:<env>=<file> ...]
```

- `public llm:read` → value is safe for an LLM to see (URLs, ids, publishable keys).
- `secret llm:blind` → masked to `SET`/`MISSING` on read; redacted by `load --redacted`.
- `from:<file>` → source this key from a specific file (any env).
- `from:<env>=<file>` → source it per-env; the key is shown **only** under the envs it names.

## Legacy stores: describe, don't migrate

A project whose env vars already live in per-env or prefixed files stays where it is — the
manifest just teaches denv to read it. Example (`~/.config/chitchat/manifest`), mapping three
different "which env" schemes without moving a file:

- **env in the keyname** (`DB_STAGING_*` / `DB_PROD_*` in one `db.env`):
  `key DB_PROD_HOST public llm:read from:prod=db.env`
- **env in the filename, same keyname** (`paypal-live.env` / `paypal-sandbox.env`):
  `key PAYPAL_CLIENT_ID secret llm:blind from:prod=paypal-live.env from:staging=paypal-sandbox.env`
- **deployed config owned elsewhere** (chitchat's real source of truth is DO Spaces):
  `push prod spaces prod` — the `spaces` adapter delegates to `make env.<env>.set`.

## Design decisions

- **Plaintext, perms-only, local-only.** No encryption/commit (`age` is available if that ever
  changes). `doctor` flags any secret file not `600`/`640`.
- **Classification is the LLM boundary**, not file perms alone — an agent reads the manifest and
  public values freely; secret values never enter its context unless it `--unmask`s.
- **Describe legacy layouts, never rewrite a live repo's env consumption.**

## Development

```sh
make install && .venv/bin/pytest -q
```
