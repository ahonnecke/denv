# denv

A Python tool for redacting sensitive information from `.env` files. Perfect for sharing configuration examples, creating documentation, or safely logging environment configurations.

## Features

- **Flexible Redaction Modes**: Redact values, keys, or both
- **Smart Comment Handling**: Preserves comments, blank lines, and formatting
- **Quote-Aware Parsing**: Handles single quotes, double quotes, and escaped characters
- **Length Preservation**: Option to maintain original value length with asterisks
- **Secret Stripping**: Automatically remove lines containing sensitive keys
- **Stream Processing**: Works with stdin/stdout for easy piping

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/ahonnecke/denv.git
cd denv

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### From PyPI (when published)

```bash
pip install denv
```

## Usage

### Basic Usage

Redact values from stdin:

```bash
cat .env | denv
```

Redact values from a file:

```bash
denv .env
```

Save output to a file:

```bash
denv .env -o .env.redacted
# or
cat .env | denv > .env.redacted
```

### Redaction Modes

**Redact values only (default):**

```bash
cat .env | denv
# or explicitly
cat .env | denv --mode values
```

Input:
```
DATABASE_URL="postgresql://user:pass@localhost/db"
API_KEY=secret123
```

Output:
```
DATABASE_URL="REDACTED"
API_KEY=REDACTED
```

**Redact keys only:**

```bash
cat .env | denv --mode keys
```

Input:
```
DATABASE_URL="postgresql://user:pass@localhost/db"
API_KEY=secret123
```

Output:
```
VAR_A1B2C3D4E5="postgresql://user:pass@localhost/db"
VAR_F6G7H8I9J0=secret123
```

**Redact both keys and values:**

```bash
cat .env | denv --mode both
```

Output:
```
VAR_A1B2C3D4E5="REDACTED"
VAR_F6G7H8I9J0=REDACTED
```

### Advanced Options

**Keep original length with asterisks:**

```bash
cat .env | denv --keep-length
```

Input:
```
API_KEY="secret123"
PASSWORD=mypassword
```

Output:
```
API_KEY="*********"
PASSWORD=**********
```

**Strip secret lines entirely:**

```bash
cat .env | denv --strip-secrets
```

Input:
```
DATABASE_URL="postgresql://localhost/db"
API_KEY=secret123
SECRET_TOKEN=abc123
DEBUG=true
```

Output:
```
DATABASE_URL="postgresql://localhost/db"
DEBUG=true
```

Lines containing these keywords are considered secrets:
- `secret`
- `password`/`passwd`
- `token`
- `apikey`/`api_key`
- `key`
- `private`
- `credential`

**Custom placeholder:**

```bash
cat .env | denv --placeholder "***HIDDEN***"
```

Output:
```
API_KEY="***HIDDEN***"
```

### Real-World Example

From your usage example:

```bash
cat .env.local | denv
```

Input:
```
BLOB_READ_WRITE_TOKEN="vercel_blob_rw_abc123"
KV_URL="https://my-kv.upstash.io"
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
```

Output:
```
BLOB_READ_WRITE_TOKEN="REDACTED"
KV_URL="REDACTED"
AWS_ACCESS_KEY_ID=REDACTED
AWS_SECRET_ACCESS_KEY=REDACTED
GITLAB_TOKEN="REDACTED"
DATABASE_URL="REDACTED"
```

### Multiple Files

Process multiple files:

```bash
denv .env .env.local .env.production
```

## Command-Line Options

```
usage: denv [-h] [--mode {values,keys,both}] [--placeholder TEXT]
            [--keep-length] [--strip-secrets] [-o FILE]
            [files ...]

Redact .env files (filter). Reads stdin or files; writes to stdout by default.

positional arguments:
  files                 Input .env files (default: stdin)

options:
  -h, --help            show this help message and exit
  --mode {values,keys,both}
                        What to redact (default: values)
  --placeholder TEXT    Replacement text when not using --keep-length
                        (default: REDACTED)
  --keep-length         Preserve original value length with '*'s (keeps quote
                        style)
  --strip-secrets       Remove lines whose keys look like secrets entirely
  -o FILE, --output FILE
                        Output file (default: stdout)
```

## Features in Detail

### Comment Preservation

Comments are preserved, both full-line and inline:

Input:
```
# Database configuration
DATABASE_URL="postgresql://localhost/db"  # Production database
API_KEY=secret123  # API key for external service
```

Output:
```
# Database configuration
DATABASE_URL="REDACTED"  # Production database
API_KEY=REDACTED  # API key for external service
```

### Export Statement Support

Handles `export` statements:

Input:
```
export DATABASE_URL="postgresql://localhost/db"
export API_KEY=secret123
```

Output:
```
export DATABASE_URL="REDACTED"
export API_KEY=REDACTED
```

### Quote Handling

Properly handles single quotes, double quotes, and unquoted values:

Input:
```
SINGLE='value'
DOUBLE="value"
UNQUOTED=value
```

Output:
```
SINGLE='REDACTED'
DOUBLE="REDACTED"
UNQUOTED=REDACTED
```

## Use Cases

1. **Documentation**: Create safe examples for README files
2. **Debugging**: Share configuration without exposing secrets
3. **CI/CD**: Generate template files from production configs
4. **Logging**: Safely log environment configurations
5. **Code Reviews**: Share environment setups without credentials

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
```

### Project Structure

```
denv/
├── src/
│   └── denv/
│       ├── __init__.py      # Package initialization
│       ├── cli.py           # Command-line interface
│       └── redactor.py      # Core redaction logic
├── tests/
│   ├── __init__.py
│   ├── test_redactor.py     # Unit tests
│   └── test_cli.py          # CLI tests
├── pyproject.toml           # Package configuration
├── setup.py                 # Setup script
├── README.md                # This file
├── LICENSE                  # MIT License
└── .gitignore              # Git ignore rules
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Author

ahonnecke

## Changelog

### 1.0.0 (2024)
- Initial release
- Support for value, key, and combined redaction
- Length preservation option
- Secret stripping functionality
- Stream processing support
