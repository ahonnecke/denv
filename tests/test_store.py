"""Tests for the denv env-var store (ported from the bash reference)."""

import os
import stat

import pytest

from denv import store
from denv.store import DenvError


def _mode(path):
    return oct(os.stat(path).st_mode & 0o777)[2:]


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A temp DENV_HOME pointed at by the env var."""
    root = tmp_path / "config"
    root.mkdir()
    monkeypatch.setenv("DENV_HOME", str(root))
    return root


def _make_project(home):
    """A project exercising public/secret, bare from:, and env-scoped from:."""
    d = home / "proj"
    d.mkdir()
    (d / "manifest").write_text(
        "project proj\n"
        "envs staging prod\n"
        "default_class secret\n"
        "default_llm blind\n"
        "push staging spaces staging\n"
        "push prod vercel production\n"
        "key API_URL public llm:read\n"
        "key API_TOKEN secret llm:blind\n"
        "key ADMIN_EMAIL public llm:read from:api.env\n"
        "key ADMIN_PASSWORD secret llm:blind from:api.env\n"
        "key PAYPAL_CLIENT_ID secret llm:blind "
        "from:prod=paypal-live.env from:staging=paypal-sandbox.env\n"
        "key DB_HOST public llm:read from:staging=ops.env from:prod=ops-prod.env\n"
    )
    # structured value files
    (d / "common.env").write_text("API_URL=https://api.example.com\n")
    (d / "staging.env").write_text("API_TOKEN=stg-token-xyz\n")
    (d / "prod.env").write_text("API_TOKEN=prod-token-abc\n")
    # bare-from file (all envs)
    (d / "api.env").write_text("ADMIN_EMAIL=admin@example.com\nADMIN_PASSWORD=s3cr3t\n")
    # env-scoped from files
    (d / "paypal-live.env").write_text("PAYPAL_CLIENT_ID=AQYOB3live\n")
    (d / "paypal-sandbox.env").write_text("PAYPAL_CLIENT_ID=ARA_6Lsandbox\n")
    (d / "ops.env").write_text("DB_HOST=staging.db.local\n")
    (d / "ops-prod.env").write_text("DB_HOST=prod.db.local\n")
    for f in d.iterdir():
        if f.name != "manifest":
            os.chmod(f, 0o600)
    return d


# --- manifest parse ---------------------------------------------------------
def test_manifest_parse(home):
    _make_project(home)
    d, m = store.load_manifest("proj")
    assert m.project == "proj"
    assert m.envs == ["staging", "prod"]
    assert m.default_class == "secret"
    assert m.default_llm == "blind"
    assert m.class_of("API_URL") == "public"
    assert m.llm_of("API_URL") == "read"
    assert m.class_of("API_TOKEN") == "secret"
    assert m.key_from["ADMIN_EMAIL"] == "api.env"
    assert m.key_from_env[("PAYPAL_CLIENT_ID", "prod")] == "paypal-live.env"
    assert m.key_from_env[("PAYPAL_CLIENT_ID", "staging")] == "paypal-sandbox.env"
    assert "PAYPAL_CLIENT_ID" in m.key_has_envfrom
    assert m.push_adapter["staging"] == "spaces"
    assert m.push_args["prod"] == "production"


def test_no_such_project(home):
    with pytest.raises(DenvError):
        store.load_manifest("nope")


# --- env-scoped from: resolution + visibility -------------------------------
def test_env_scoped_from_resolution(home):
    d, m = home, None
    d = _make_project(home)
    d, m = store.load_manifest("proj")
    assert store.raw_value(d, m, "prod", "PAYPAL_CLIENT_ID") == "AQYOB3live"
    assert store.raw_value(d, m, "staging", "PAYPAL_CLIENT_ID") == "ARA_6Lsandbox"
    assert store.raw_value(d, m, "staging", "DB_HOST") == "staging.db.local"
    assert store.raw_value(d, m, "prod", "DB_HOST") == "prod.db.local"


def test_env_scoped_visibility(home):
    _make_project(home)
    d, m = store.load_manifest("proj")
    # env-scoped keys appear under every env they name (both name staging+prod)
    for env in ("staging", "prod"):
        keys = store.keys_present_in_env(d, m, env)
        assert "PAYPAL_CLIENT_ID" in keys
        assert "DB_HOST" in keys
    # a bare-from key appears everywhere; a plain declared key too
    assert "ADMIN_EMAIL" in store.keys_present_in_env(d, m, "staging")
    assert "API_URL" in store.keys_present_in_env(d, m, "prod")


def test_env_scoped_visibility_excludes_unnamed_env(home):
    d = home / "p2"
    d.mkdir()
    (d / "manifest").write_text(
        "project p2\n"
        "envs staging prod\n"
        "key ONLY_STAGING secret llm:blind from:staging=s.env\n"
    )
    (d / "s.env").write_text("ONLY_STAGING=x\n")
    os.chmod(d / "s.env", 0o600)
    dd, m = store.load_manifest("p2")
    assert "ONLY_STAGING" in store.keys_present_in_env(dd, m, "staging")
    assert "ONLY_STAGING" not in store.keys_present_in_env(dd, m, "prod")


# --- ls: public shown, secret masked ---------------------------------------
def test_ls_public_shown_secret_masked(home, capsys):
    _make_project(home)
    store.cmd_ls("proj", "staging")
    out = capsys.readouterr().out
    assert "https://api.example.com" in out  # public value
    assert "admin@example.com" in out  # public via bare from
    assert "stg-token-xyz" not in out  # secret masked
    assert "ARA_6Lsandbox" not in out  # secret masked
    # API_TOKEN row is SET
    tok_line = [ln for ln in out.splitlines() if ln.startswith("API_TOKEN ")][0]
    assert tok_line.endswith("SET")


def test_ls_missing_secret(home, capsys):
    d = _make_project(home)
    # remove staging token value so it is MISSING
    (d / "staging.env").write_text("\n")
    store.cmd_ls("proj", "staging")
    out = capsys.readouterr().out
    tok_line = [ln for ln in out.splitlines() if ln.startswith("API_TOKEN ")][0]
    assert tok_line.endswith("MISSING")


# --- get / --unmask ---------------------------------------------------------
def test_get_public_and_secret(home, capsys):
    _make_project(home)
    store.cmd_get("proj", "staging", "API_URL")
    assert capsys.readouterr().out.strip() == "https://api.example.com"
    store.cmd_get("proj", "staging", "API_TOKEN")
    assert capsys.readouterr().out.strip() == "SET"


def test_get_unmask(home, capsys):
    _make_project(home)
    store.cmd_get("proj", "staging", "API_TOKEN", unmask=True)
    assert capsys.readouterr().out.strip() == "stg-token-xyz"


# --- load: 0600, no secret values printed -----------------------------------
def test_load_writes_0600_no_values_printed(home, tmp_path, capsys):
    _make_project(home)
    dst = tmp_path / "out.env"
    store.cmd_load("proj", "staging", to=str(dst))
    out = capsys.readouterr().out
    assert "stg-token-xyz" not in out
    assert "ARA_6Lsandbox" not in out
    assert "values not printed" in out
    assert _mode(str(dst)) == "600"
    body = dst.read_text()
    assert "API_TOKEN=stg-token-xyz" in body  # real value in the file
    assert body.splitlines()[0].startswith("# generated by denv load proj staging")


# --- load --redacted: secrets redacted, public kept -------------------------
def test_load_redacted(home, tmp_path, capsys):
    _make_project(home)
    dst = tmp_path / "red.env"
    store.cmd_load("proj", "staging", to=str(dst), redacted=True)
    out = capsys.readouterr().out
    assert "secrets redacted" in out
    body = dst.read_text()
    # secret values replaced with the redactor placeholder
    assert "API_TOKEN=REDACTED" in body
    assert "stg-token-xyz" not in body
    assert "PAYPAL_CLIENT_ID=REDACTED" in body
    assert "ARA_6Lsandbox" not in body
    # public values kept
    assert "API_URL=https://api.example.com" in body
    assert "ADMIN_EMAIL=admin@example.com" in body
    assert _mode(str(dst)) == "600"


# --- push dry-run plan strings per adapter (masked) -------------------------
def test_push_dryrun_spaces(home, capsys):
    _make_project(home)
    store.cmd_push("proj", "staging")
    out = capsys.readouterr().out
    assert ">> push proj/staging via spaces (staging) — DRY-RUN" in out
    assert "# delegated: run chitchat `make env.staging.set KEY=API_TOKEN VALUE=…`" in out
    assert "stg-token-xyz" not in out
    assert "re-run with --apply" in out


def test_push_dryrun_vercel_masked(home, capsys):
    _make_project(home)
    store.cmd_push("proj", "prod")
    out = capsys.readouterr().out
    assert ">> push proj/prod via vercel (production) — DRY-RUN" in out
    assert 'printf %s "<masked>" | vercel env add API_TOKEN production --force' in out
    assert "prod-token-abc" not in out


def test_push_adapter_strings():
    assert store.adapter_cmd("gh", "-R o/r", "K") == 'gh secret set K --body "$V" -R o/r'
    assert store.adapter_cmd("supabase", "ctx", "K") == 'supabase secrets set K="$V" ctx'
    assert (
        store.adapter_cmd("cloudflare", "", "K")
        == 'printf %s "$V" | wrangler secret put K '
    )
    assert store.adapter_cmd("none", "", "K") == "# push disabled for this env (adapter: none)"


def test_push_none_adapter(home, capsys):
    d = home / "np"
    d.mkdir()
    (d / "manifest").write_text("project np\nenvs dev\npush dev none\nkey X public llm:read\n")
    (d / "common.env").write_text("X=1\n")
    os.chmod(d / "common.env", 0o600)
    store.cmd_push("np", "dev")
    out = capsys.readouterr().out
    assert "adapter none — local only, nothing to push" in out


def test_push_no_target(home):
    d = home / "nt"
    d.mkdir()
    (d / "manifest").write_text("project nt\nenvs dev\nkey X public llm:read\n")
    with pytest.raises(DenvError):
        store.cmd_push("nt", "dev")


# --- doctor: flags a 0644 secret file ---------------------------------------
def test_doctor_flags_bad_perms(home, capsys):
    d = _make_project(home)
    os.chmod(d / "staging.env", 0o644)  # a secret file world-readable
    store.cmd_doctor("proj")
    captured = capsys.readouterr()
    assert "== denv doctor: proj" in captured.out
    assert "perms:" in captured.err
    assert "staging.env is 644 (want 600)" in captured.err


def test_doctor_clean_and_reports(home, capsys):
    _make_project(home)
    store.cmd_doctor("proj")
    captured = capsys.readouterr()
    assert "perms:" not in captured.err  # all files are 600
    assert "[staging] push: spaces staging" in captured.out
    assert "[prod] push: vercel production" in captured.out


def test_doctor_undeclared_and_missing(home, capsys):
    d = home / "dd"
    d.mkdir()
    (d / "manifest").write_text(
        "project dd\nenvs dev\ndefault_class secret\ndefault_llm blind\n"
        "push dev none\nkey DECLARED secret llm:blind\n"
    )
    (d / "dev.env").write_text("STRAY=1\n")
    os.chmod(d / "dev.env", 0o600)
    store.cmd_doctor("dd")
    out = capsys.readouterr().out
    assert "[dev] declared, no value: DECLARED" in out
    assert "[dev] present, undeclared: STRAY (defaults to secret/blind)" in out


# --- envs -------------------------------------------------------------------
def test_envs(home, capsys):
    _make_project(home)
    store.cmd_envs("proj")
    assert capsys.readouterr().out.strip().split("\n") == ["staging", "prod"]


# --- init: scaffolds + refuses to clobber -----------------------------------
def test_init_scaffolds(home, capsys):
    store.cmd_init("newproj", ["dev", "prod"])
    out = capsys.readouterr().out
    d = home / "newproj"
    assert (d / "manifest").is_file()
    assert (d / "common.env").is_file()
    assert (d / "dev.env").is_file()
    assert (d / "prod.env").is_file()
    assert _mode(str(d)) == "700"
    assert _mode(str(d / "manifest")) == "644"
    assert _mode(str(d / "common.env")) == "600"
    assert _mode(str(d / "dev.env")) == "600"
    manifest = (d / "manifest").read_text()
    assert "project newproj" in manifest
    assert "envs    dev prod" in manifest
    assert "default_class secret" in manifest
    assert "push dev none" in manifest
    assert "push prod none" in manifest
    assert "created" in out


def test_init_default_env(home):
    store.cmd_init("solo")
    assert (home / "solo" / "dev.env").is_file()
    d, m = store.load_manifest("solo")
    assert m.envs == ["dev"]


def test_init_refuses_clobber(home):
    store.cmd_init("dup")
    with pytest.raises(DenvError):
        store.cmd_init("dup")
