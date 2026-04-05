# Contributing to ACLI

Thank you for your interest in contributing to ACLI! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch from `main`
4. Make your changes
5. Submit a pull request

## Development Setup

### Python SDK

```bash
cd sdks/python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Checks

All checks must pass before submitting a PR:

```bash
ruff check src/ tests/        # Linting
ruff format --check src/ tests/ # Formatting
mypy src/                      # Type checking
pytest                         # Tests (90% coverage minimum)
```

## Pull Request Process

1. Create a branch from `main` with a descriptive name (e.g., `feat/validate-command`, `fix/exit-code-handling`)
2. Keep PRs focused — one feature or fix per PR
3. Ensure all CI checks pass
4. Update documentation if you change public APIs
5. Add tests for new functionality
6. Request review from a maintainer

## Commit Messages

Use clear, descriptive commit messages:

```
feat: add acli validate command
fix: correct exit code for dry-run mode
docs: update Python SDK quick start example
```

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include steps to reproduce for bugs
- Include the ACLI spec section reference when relevant

## Code of Conduct

This project is licensed under the [EUPL-1.2](LICENSE).

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
