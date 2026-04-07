# Contributing

Thank you for your interest in contributing to ACLI!

## Getting started

1. Fork the repository
2. Clone your fork
3. Create a feature branch from `develop`
4. Make your changes
5. Submit a pull request targeting `develop`

## Development setup

### Python SDK

```bash
cd sdks/python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Other SDKs (Rust, TypeScript, Go, .NET, R, Java) have their own READMEs under `sdks/<language>/`. When you change a public API, update **root `README.md`**, **`docs/index.md`**, **`docs/sdks/index.md`**, and **`mkdocs.yml`** if navigation changes.

## Quality checks

All checks must pass before submitting a PR:

```bash
ruff check src/ tests/          # Linting
ruff format --check src/ tests/ # Formatting
mypy src/                       # Type checking
pytest                          # Tests (90% coverage minimum)
```

## Branch strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable releases, protected |
| `develop` | Integration branch for PRs |
| `feat/*` | Feature branches |
| `fix/*` | Bug fix branches |

## Pull request process

1. Branch from `develop` with a descriptive name
2. Keep PRs focused — one feature or fix per PR
3. Ensure all CI checks pass
4. Update documentation if you change public APIs
5. Add tests for new functionality

## Commit messages

```
feat: add acli validate command
fix: correct exit code for dry-run mode
docs: update Python SDK quick start
```

## License

By contributing, you agree that your contributions will be licensed under [EUPL-1.2](https://github.com/alpibrusl/acli/blob/main/LICENSE).
