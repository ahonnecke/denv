# Quick Start Guide

## Installation (30 seconds)

```bash
cd ~/src/denv
pip install -e .
```

## Verify Installation

```bash
denv --help
```

## Basic Usage

### Example 1: Redact from stdin (your use case)

```bash
cat .env.local | denv
```

**Input:**
```
BLOB_READ_WRITE_TOKEN="vercel_blob_rw_abc123"
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
```

**Output:**
```
BLOB_READ_WRITE_TOKEN="REDACTED"
AWS_ACCESS_KEY_ID=REDACTED
GITLAB_TOKEN="REDACTED"
DATABASE_URL="REDACTED"
```

### Example 2: Redact from file

```bash
denv .env.local
```

### Example 3: Save to file

```bash
cat .env.local | denv > .env.redacted
# or
denv .env.local -o .env.redacted
```

### Example 4: Strip secrets entirely

```bash
cat .env.local | denv --strip-secrets
```

This removes lines with keys containing: `secret`, `password`, `token`, `key`, `private`, `credential`

### Example 5: Keep original length

```bash
cat .env.local | denv --keep-length
```

**Output:**
```
BLOB_READ_WRITE_TOKEN="**********************"
AWS_ACCESS_KEY_ID=*******************
```

### Example 6: Redact both keys and values

```bash
cat .env.local | denv --mode both
```

**Output:**
```
VAR_A1B2C3D4E5="REDACTED"
VAR_F6G7H8I9J0=REDACTED
```

## Common Options

| Option | Description |
|--------|-------------|
| `--mode values` | Redact values only (default) |
| `--mode keys` | Redact keys only |
| `--mode both` | Redact both keys and values |
| `--keep-length` | Use asterisks to preserve length |
| `--strip-secrets` | Remove secret lines entirely |
| `--placeholder TEXT` | Custom placeholder (default: REDACTED) |
| `-o FILE` | Output to file instead of stdout |

## Development

### Run tests

```bash
make test
```

### Format code

```bash
make format
```

### Run all checks

```bash
make lint
make test
```

## Cleanup

The old `denv.py` file is no longer needed and can be removed:

```bash
rm denv.py
```

## Need Help?

```bash
denv --help
```

Or check the full [README.md](README.md) for detailed documentation.
