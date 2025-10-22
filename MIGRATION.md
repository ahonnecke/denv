# Migration from Old Structure

## What Changed?

The project has been restructured from a single-file script to a proper Python package.

### Old Structure
```
denv/
└── denv.py
```

### New Structure
```
denv/
├── src/
│   └── denv/
│       ├── __init__.py
│       ├── cli.py
│       └── redactor.py
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_redactor.py
├── pyproject.toml
├── setup.py
├── README.md
├── LICENSE
├── .gitignore
├── Makefile
└── denv.py (old file - can be removed)
```

## Migration Steps

### If you were using the old `denv.py` directly:

**Before:**
```bash
python denv.py .env
cat .env | python denv.py
```

**After (install the package):**
```bash
pip install .
denv .env
cat .env | denv
```

### If you had the old file in your PATH:

**Before:**
```bash
# Had denv.py symlinked or in PATH
denv.py .env
```

**After:**
```bash
# Install the package
pip install .
# Now use the installed command
denv .env
```

## Removing the Old File

Once you've installed the package and verified it works, you can safely remove the old `denv.py` file:

```bash
rm denv.py
```

## Benefits of the New Structure

1. **Proper packaging**: Can be installed with pip
2. **Better organization**: Code split into logical modules
3. **Testing**: Comprehensive test suite included
4. **Documentation**: Improved README and contributing guides
5. **Development tools**: Makefile for common tasks
6. **Type hints**: Better IDE support and code quality
7. **Installable**: Works as a system-wide command

## Backward Compatibility

The functionality remains 100% compatible. All command-line options work exactly the same:

```bash
# All these still work the same way
denv .env
denv --mode both .env
denv --keep-length .env
denv --strip-secrets .env
cat .env | denv
```

## Questions?

If you encounter any issues during migration, please open an issue on GitHub.
