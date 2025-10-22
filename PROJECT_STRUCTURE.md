# Project Structure

```
denv/
├── .github/
│   └── workflows/
│       └── test.yml              # GitHub Actions CI/CD pipeline
├── src/
│   └── denv/
│       ├── __init__.py           # Package initialization and exports
│       ├── cli.py                # Command-line interface entry point
│       └── redactor.py           # Core redaction logic
├── tests/
│   ├── __init__.py               # Test package initialization
│   ├── test_cli.py               # CLI functionality tests
│   └── test_redactor.py          # Core logic unit tests
├── .gitignore                    # Git ignore rules for Python projects
├── CONTRIBUTING.md               # Contribution guidelines
├── INSTALL.md                    # Installation instructions
├── LICENSE                       # MIT License
├── Makefile                      # Common development tasks
├── MANIFEST.in                   # Package manifest for distribution
├── MIGRATION.md                  # Migration guide from old structure
├── pyproject.toml                # Modern Python package configuration
├── README.md                     # Main project documentation
├── requirements-dev.txt          # Development dependencies
├── setup.py                      # Setup script (delegates to pyproject.toml)
└── denv.py                       # OLD FILE - Can be removed after migration

3 directories, 17 files (18 including old denv.py)
```

## Directory Descriptions

### `/src/denv/`
The main package source code following the modern "src layout" pattern.

- **`__init__.py`**: Package initialization, version info, and public API exports
- **`cli.py`**: Command-line interface implementation using argparse
- **`redactor.py`**: Core redaction logic with all parsing and processing functions

### `/tests/`
Comprehensive test suite using pytest.

- **`test_redactor.py`**: Unit tests for all redaction functions
- **`test_cli.py`**: Integration tests for CLI and stream processing

### Root Files

- **`pyproject.toml`**: Modern Python package configuration (PEP 518)
- **`setup.py`**: Minimal setup script for backward compatibility
- **`README.md`**: Main documentation with usage examples
- **`LICENSE`**: MIT License
- **`Makefile`**: Development task automation
- **`.gitignore`**: Python-specific ignore patterns
- **`CONTRIBUTING.md`**: Developer contribution guidelines
- **`INSTALL.md`**: Installation instructions
- **`MIGRATION.md`**: Guide for migrating from old structure
- **`MANIFEST.in`**: Files to include in distribution package
- **`requirements-dev.txt`**: Development dependencies (pytest, black, etc.)

## Key Features

### Modern Python Package Structure
- ✅ Follows PEP 518 (pyproject.toml)
- ✅ Uses src layout (best practice)
- ✅ Installable via pip
- ✅ Entry point for CLI command

### Development Tools
- ✅ Comprehensive test suite
- ✅ Code formatting (black, isort)
- ✅ Linting (flake8, mypy)
- ✅ Makefile for common tasks
- ✅ GitHub Actions CI/CD

### Documentation
- ✅ Detailed README with examples
- ✅ Installation guide
- ✅ Migration guide
- ✅ Contributing guidelines

## Next Steps

1. **Remove old file**: `rm denv.py`
2. **Install package**: `make install-dev`
3. **Run tests**: `make test`
4. **Verify installation**: `denv --help`

## Usage After Installation

```bash
# Install the package
pip install .

# Use the command
cat .env.local | denv
denv .env --mode both
denv .env --strip-secrets -o .env.redacted
```

## Development Workflow

```bash
# Install in development mode
make install-dev

# Run tests
make test

# Format code
make format

# Run linters
make lint

# Build distribution
make build
```
