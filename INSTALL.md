# Installation Guide

## Quick Start

### Install from source

```bash
# Clone the repository
git clone https://github.com/ahonnecke/denv.git
cd denv

# Install the package
pip install .
```

### Development Installation

For development work:

```bash
# Install in editable mode with dev dependencies
make install-dev

# Or manually:
pip install -e .
pip install -r requirements-dev.txt
```

## Verify Installation

After installation, verify that `denv` is available:

```bash
denv --help
```

You should see the help message with all available options.

## Usage Example

Test the installation:

```bash
# Create a test .env file
echo "API_KEY=secret123" > test.env
echo "DEBUG=true" >> test.env

# Redact it
cat test.env | denv

# Output should be:
# API_KEY=REDACTED
# DEBUG=REDACTED
```

## Uninstall

To remove the package:

```bash
pip uninstall denv
```

## Troubleshooting

### Command not found

If `denv` command is not found after installation:

1. Check if the installation directory is in your PATH:
```bash
python -m site --user-base
```

2. Add the bin directory to your PATH:
```bash
export PATH="$PATH:$(python -m site --user-base)/bin"
```

3. Or run directly with Python:
```bash
python -m denv.cli --help
```

### Import errors

If you get import errors, ensure you're in the correct directory and have installed the package:

```bash
pip list | grep denv
```

If not listed, reinstall:
```bash
pip install -e .
```
