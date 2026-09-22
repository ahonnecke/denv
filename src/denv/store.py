"""Durable env-var store — Python port of the ``denv`` bash reference.

A per-project MANIFEST classifies each key (public|secret, llm:read|blind) and
declares each env's push target; VALUE files hold the actual KEY=VALUE. The
classification is what makes a value safe for an LLM to read: ``ls``/``get``
print public values but mask secrets to SET/MISSING, ``load`` writes a file and
never prints values, ``push`` previews (masked) unless applied.

Store layout: ``$DENV_HOME/<project>/`` (DENV_HOME defaults to ``~/.config``)
  manifest     classification + envs + push targets (LLM-readable; no secrets)
  common.env   KEY=VALUE shared by all envs
  <env>.env    KEY=VALUE for one env (overrides common.env)
  .env         legacy flat fallback (used only if no common/<env> file exists)
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .redactor import make_placeholder

SELF = "denv"


class DenvError(Exception):
    """A user-facing error; the CLI prints it and exits 2 (matches bash ``die``)."""


def warn(msg: str) -> None:
    """Print a warning to stderr (matches bash ``warn``)."""
    print(f"{SELF}: {msg}", file=sys.stderr)


def denv_home() -> str:
    """Return the store root: ``$DENV_HOME`` or ``~/.config``."""
    return os.environ.get("DENV_HOME") or os.path.join(os.path.expanduser("~"), ".config")


def _tilde(path: str) -> str:
    """Collapse a leading home dir to ``~`` (matches bash ``${x/#$HOME/~}``)."""
    home = os.path.expanduser("~")
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def proj_dir(project: str) -> str:
    """Return the project store dir, erroring if it does not exist."""
    d = os.path.join(denv_home(), project)
    if not os.path.isdir(d):
        raise DenvError(f"no such project store: {_tilde(d)}  (create {d}/manifest)")
    return d


# --- manifest parsing -------------------------------------------------------
@dataclass
class Manifest:
    """Parsed manifest state (mirrors the bash globals)."""

    project: str = ""
    envs: List[str] = field(default_factory=list)
    default_class: str = "secret"
    default_llm: str = "blind"
    keys: List[str] = field(default_factory=list)  # declared order
    key_class: Dict[str, str] = field(default_factory=dict)
    key_llm: Dict[str, str] = field(default_factory=dict)
    key_from: Dict[str, str] = field(default_factory=dict)  # name -> file
    key_from_env: Dict[Tuple[str, str], str] = field(default_factory=dict)  # (name, env) -> file
    key_has_envfrom: Set[str] = field(default_factory=set)
    push_adapter: Dict[str, str] = field(default_factory=dict)  # env -> adapter
    push_args: Dict[str, str] = field(default_factory=dict)  # env -> args string

    def class_of(self, key: str) -> str:
        """Declared class, else the manifest default_class."""
        return self.key_class.get(key) or self.default_class

    def llm_of(self, key: str) -> str:
        """Declared llm flag, else the manifest default_llm."""
        return self.key_llm.get(key) or self.default_llm


def parse_manifest(mf: str) -> Manifest:
    """Parse a manifest file into a :class:`Manifest`."""
    m = Manifest()
    with open(mf, "r", encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if not parts or parts[0].startswith("#"):
                continue
            kw = parts[0]
            a = parts[1] if len(parts) > 1 else ""
            b = parts[2] if len(parts) > 2 else ""
            rest = parts[3:]
            if kw == "project":
                m.project = a
            elif kw == "envs":
                m.envs = parts[1:]
            elif kw == "default_class":
                m.default_class = a
            elif kw == "default_llm":
                m.default_llm = a
            elif kw == "push":
                m.push_adapter[a] = b
                m.push_args[a] = " ".join(rest)
            elif kw == "key":
                name = a
                cls = b if b else "secret"
                llm = "blind"
                for tok in rest:
                    if tok == "llm:read":
                        llm = "read"
                    elif tok == "llm:blind":
                        llm = "blind"
                    elif tok.startswith("from:"):
                        spec = tok[len("from:"):]
                        if "=" in spec:
                            env_name, fname = spec.split("=", 1)
                            m.key_from_env[(name, env_name)] = fname
                            m.key_has_envfrom.add(name)
                        else:
                            m.key_from[name] = spec
                m.key_class[name] = cls
                m.key_llm[name] = llm
                m.keys.append(name)
            else:
                warn(f"manifest: unknown directive '{kw}' (ignored)")
    return m


def load_manifest(project: str) -> Tuple[str, Manifest]:
    """Return ``(project_dir, Manifest)``, erroring if either is missing."""
    d = proj_dir(project)
    mf = os.path.join(d, "manifest")
    if not os.path.isfile(mf):
        raise DenvError(f"manifest missing: {_tilde(mf)}")
    return d, parse_manifest(mf)


# --- value resolution -------------------------------------------------------
def value_files_for(d: str, env: str) -> List[str]:
    """Value files for an env, lowest->highest precedence.

    ``common.env`` then ``<env>.env``; the legacy flat ``.env`` is used only
    when neither structured file exists.
    """
    out: List[str] = []
    common = os.path.join(d, "common.env")
    envf = os.path.join(d, f"{env}.env")
    if os.path.isfile(common):
        out.append(common)
    if os.path.isfile(envf):
        out.append(envf)
    if not out:
        legacy = os.path.join(d, ".env")
        if os.path.isfile(legacy):
            out.append(legacy)
    return out


def raw_value(d: str, m: Manifest, env: str, key: str) -> str:
    """Resolve one key's raw value for an env ('' if unset).

    Honors ``from:<env>=<file>`` (per-env) → ``from:<file>`` (all envs) →
    the default value-file search. Last matching ``^\\s*KEY=`` line wins.
    """
    from_env = m.key_from_env.get((key, env))
    from_bare = m.key_from.get(key)
    files: List[str]
    if from_env:
        p = os.path.join(d, from_env)
        files = [p] if os.path.isfile(p) else []
    elif from_bare:
        p = os.path.join(d, from_bare)
        files = [p] if os.path.isfile(p) else []
    else:
        files = value_files_for(d, env)

    pat = re.compile(r"^\s*" + re.escape(key) + r"=")
    v = ""
    for f in files:
        if not f or not os.path.isfile(f):
            continue
        with open(f, "r", encoding="utf-8") as fh:
            match = None
            for line in fh:
                if pat.match(line):
                    match = line
        if match is not None:
            v = match.rstrip("\n").split("=", 1)[1]
    return v


def mask(value: str) -> str:
    """SET if non-empty else MISSING (matches bash ``mask``)."""
    return "SET" if value else "MISSING"


_PRESENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)=")


def _keys_literally_present(d: str, env: str) -> Set[str]:
    """Keys literally assigned in an env's value files."""
    present: Set[str] = set()
    for f in value_files_for(d, env):
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                mo = _PRESENT_RE.match(line)
                if mo:
                    present.add(mo.group(1))
    return present


def keys_present_in_env(d: str, m: Manifest, env: str) -> List[str]:
    """Union of declared keys (respecting env-scoped visibility) and keys
    literally present in the env's value files, sorted unique."""
    result: Set[str] = set()
    for k in m.keys:
        # a key with any env-scoped from: appears only under the envs it names
        if k in m.key_has_envfrom and (k, env) not in m.key_from_env:
            continue
        result.add(k)
    result |= _keys_literally_present(d, env)
    return sorted(result)


# --- subcommands ------------------------------------------------------------
def cmd_envs(project: str) -> None:
    """Print declared envs, one per line."""
    _, m = load_manifest(project)
    print("\n".join(m.envs))


def cmd_ls(project: str, env: Optional[str] = None) -> None:
    """Table of KEY, CLASS, LLM, ENV, VALUE. public -> real value; secret -> SET/MISSING."""
    d, m = load_manifest(project)
    envs = [env] if env else m.envs
    print(f"{'KEY':<28} {'CLASS':<6} {'LLM':<5} {'ENV':<7} VALUE")
    for e in envs:
        for k in keys_present_in_env(d, m, e):
            cls = m.class_of(k)
            llm = m.llm_of(k)
            val = raw_value(d, m, e, k)
            show = val if cls == "public" else mask(val)
            print(f"{k:<28} {cls:<6} {llm:<5} {e:<7} {show}")


def cmd_get(project: str, env: str, key: str, unmask: bool = False) -> None:
    """Print a key's value: public or --unmask -> raw; else SET/MISSING."""
    d, m = load_manifest(project)
    cls = m.class_of(key)
    val = raw_value(d, m, env, key)
    if cls == "public" or unmask:
        print(val)
    else:
        print(mask(val))


def cmd_load(project: str, env: str, to: str = "./.env", redacted: bool = False) -> None:
    """Write a merged env file (mode 600); never prints values.

    With ``redacted=True``, every key classified ``secret`` has its value
    replaced by a redaction placeholder (public keys keep real values), so the
    written file is safe to share/log.
    """
    d, m = load_manifest(project)
    if not env:
        raise DenvError("load needs an env")
    keys = keys_present_in_env(d, m, env)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    lines: List[str] = []
    if redacted:
        lines.append(
            f"# generated by denv load --redacted {project} {env} at {stamp} "
            "— secrets redacted, safe to share"
        )
    else:
        lines.append(f"# generated by denv load {project} {env} at {stamp} — do not commit")
    n = 0
    n_redacted = 0
    for k in keys:
        val = raw_value(d, m, env, k)
        if redacted and m.class_of(k) == "secret":
            val = make_placeholder(val, "REDACTED", False)
            n_redacted += 1
        lines.append(f"{k}={val}")
        n += 1
    with open(to, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    os.chmod(to, 0o600)
    if redacted:
        print(f"wrote {n} keys -> {to} (mode 600, {n_redacted} secrets redacted, safe to share)")
    else:
        print(f"wrote {n} keys -> {to} (mode 600, values not printed)")


# --- push adapters ----------------------------------------------------------
def adapter_cmd(ad: str, ctx: str, key: str) -> str:
    """Shell command to set ONE key; value passed via env ``$V`` (never argv)."""
    if ad == "vercel":
        return f'printf %s "$V" | vercel env add {key} {ctx} --force'
    if ad == "gh":
        return f'gh secret set {key} --body "$V" {ctx}'
    if ad == "supabase":
        return f'supabase secrets set {key}="$V" {ctx}'
    if ad == "cloudflare":
        return f'printf %s "$V" | wrangler secret put {key} {ctx}'
    if ad == "spaces":
        return f"# delegated: run chitchat `make env.{ctx}.set KEY={key} VALUE=…` (Spaces source-of-truth)"
    if ad == "none":
        return "# push disabled for this env (adapter: none)"
    return f"# UNKNOWN adapter: {ad}"


def cmd_push(project: str, env: str, apply: bool = False) -> None:
    """Dry-run plan (masked) by default; ``apply=True`` executes each command."""
    d, m = load_manifest(project)
    ad = m.push_adapter.get(env)
    ctx = m.push_args.get(env, "")
    if not ad:
        raise DenvError(
            f"no push target declared for env '{env}' (add: push {env} <adapter> …)"
        )
    ctx_disp = f"({ctx})" if ctx else ""
    mode = "APPLY" if apply else "DRY-RUN"
    print(f">> push {project}/{env} via {ad} {ctx_disp} — {mode}")
    if ad == "none":
        print("   (adapter none — local only, nothing to push)")
        return
    n = 0
    for k in keys_present_in_env(d, m, env):
        val = raw_value(d, m, env, k)
        if not val:
            warn(f"skip {k} (no value in {env})")
            continue
        cmd = adapter_cmd(ad, ctx, k)
        if apply:
            print(f"   set {k}")
            child_env = dict(os.environ)
            child_env["V"] = val
            subprocess.run(["bash", "-c", cmd], env=child_env)
        else:
            print(f"   {k}  ->  {cmd.replace('$V', '<masked>', 1)}")
        n += 1
    if apply:
        print(f">> applied {n} keys")
    else:
        print(f">> planned {n} keys  (re-run with --apply to execute)")


def cmd_doctor(project: str) -> None:
    """Report envs/defaults, value-file perms, missing/undeclared keys, push targets."""
    d, m = load_manifest(project)
    print(f"== denv doctor: {project} ({d}) ==")
    print(
        f"envs: {' '.join(m.envs)}   "
        f"default_class={m.default_class} default_llm={m.default_llm}"
    )
    # perms on every value file, including files referenced via from:
    files = [os.path.join(d, "common.env"), os.path.join(d, ".env")]
    for e in m.envs:
        files.append(os.path.join(d, f"{e}.env"))
    for fname in m.key_from.values():
        if fname:
            files.append(os.path.join(d, fname))
    for fname in m.key_from_env.values():
        if fname:
            files.append(os.path.join(d, fname))
    for f in sorted(set(files)):
        if not os.path.isfile(f):
            continue
        mode = oct(os.stat(f).st_mode & 0o777)[2:]
        if mode not in ("600", "640"):
            warn(f"perms: {_tilde(f)} is {mode} (want 600)")
    # declared-but-absent, and present-but-undeclared
    for e in m.envs:
        for k in m.keys:
            if k in m.key_has_envfrom and (k, e) not in m.key_from_env:
                continue
            if not raw_value(d, m, e, k):
                print(f"  [{e}] declared, no value: {k}")
        for k in sorted(_keys_literally_present(d, e)):
            if k not in m.keys:
                print(
                    f"  [{e}] present, undeclared: {k} "
                    f"(defaults to {m.default_class}/{m.default_llm})"
                )
        adapter = m.push_adapter.get(e, "<none declared>")
        args = m.push_args.get(e, "")
        print(f"  [{e}] push: {adapter} {args}")


def cmd_init(project: str, envs: Optional[List[str]] = None) -> None:
    """Scaffold a new store (manifest + value files); refuse to clobber an existing one."""
    envs = list(envs) if envs else ["dev"]
    d = os.path.join(denv_home(), project)
    mf = os.path.join(d, "manifest")
    if os.path.isfile(mf):
        raise DenvError(f"store already exists: {_tilde(mf)} (edit it, don't init)")
    os.makedirs(d, exist_ok=True)
    os.chmod(d, 0o700)
    manifest_lines = [
        f"# denv manifest — {project}",
        "# Values live beside this file (common.env + <env>.env, mode 600). This file is",
        "# LLM-readable: classification + routing only, never secret values.",
        "",
        f"project {project}",
        f"envs    {' '.join(envs)}",
        "default_class secret     # keys not listed below default to secret + llm:blind",
        "default_llm   blind",
        "",
        "# push targets per env (adapter: vercel|gh|supabase|cloudflare|spaces|none):",
    ]
    for e in envs:
        manifest_lines.append(f"push {e} none")
    manifest_lines += [
        "",
        "# classify each key so an LLM can read the safe ones:",
        "#   key <NAME> public llm:read    # URLs, ids, publishable keys — value shown",
        "#   key <NAME> secret llm:blind   # credentials — masked to SET/MISSING on read",
        "#   key <NAME> secret llm:blind from:<env>=<file>   # legacy per-env source file",
    ]
    with open(mf, "w", encoding="utf-8") as fh:
        fh.write("\n".join(manifest_lines) + "\n")
    os.chmod(mf, 0o644)
    # value files
    common = os.path.join(d, "common.env")
    open(common, "w", encoding="utf-8").close()
    os.chmod(common, 0o600)
    for e in envs:
        ef = os.path.join(d, f"{e}.env")
        open(ef, "w", encoding="utf-8").close()
        os.chmod(ef, 0o600)
    print(f"created {_tilde(d)}/")
    print("  manifest         (edit: declare each key public|secret + push targets)")
    print("  common.env       (KEY=VALUE shared by all envs, mode 600)")
    for e in envs:
        print(f"  {e}.env" + " " * (12 - len(e)) + f"(KEY=VALUE for {e}, mode 600)")
    print("next: add KEY=VALUE to the value files, classify keys in the manifest, then:")
    print(f"  denv ls {project}        denv doctor {project}        denv push {project} <env>   (dry-run)")
