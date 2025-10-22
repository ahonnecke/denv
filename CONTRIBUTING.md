# Contributing to denv

Thank you for your interest in contributing to denv!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/ahonnecke/denv.git
cd denv
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode with dev dependencies:
```bash
pip install -e .
pip install -r requirements-dev.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=denv --cov-report=html
```

## Code Style

This project uses:
- **black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Format your code:
```bash
black src/ tests/
isort src/ tests/
```

Check for issues:
```bash
flake8 src/ tests/
mypy src/
```

## Making Changes

1. Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Ensure all tests pass and code is formatted:
```bash
pytest
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

4. Commit your changes:
```bash
git add .
git commit -m "Description of your changes"
```

5. Push to your fork and submit a pull request

## Pull Request Guidelines

- Include tests for new features
- Update documentation as needed
- Follow the existing code style
- Write clear commit messages
- Keep pull requests focused on a single feature or fix

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Any relevant error messages

## Questions?

Feel free to open an issue for any questions or concerns.
