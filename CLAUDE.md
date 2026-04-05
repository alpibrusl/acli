# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

ACLI (Agent-friendly CLI) is a specification and reference implementation for designing CLI tools that AI agents can discover, learn, and use autonomously via `--help` and introspection — without pre-loaded schemas or external tool registries.

The spec lives in `ACLI_SPEC.md` (v0.1.0, draft). This is a monorepo: language SDKs live under `sdks/<language>/`.

## Repo structure

```
ACLI_SPEC.md          # The specification document
sdks/
  python/             # Python SDK (acli-spec package)
    src/acli/         # Source code
    tests/            # Test suite
    pyproject.toml    # Package config, linting, test settings
```

## Python SDK

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e "sdks/python[dev]"
```

### Commands (run from `sdks/python/`)

```bash
# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Auto-format
ruff format src/ tests/

# Type check
mypy src/

# Tests (with coverage, fails under 90%)
pytest

# Run a single test
pytest tests/test_app.py::TestACLIApp::test_has_introspect_command
```

### Architecture

The SDK wraps Typer to enforce the ACLI spec automatically:

- **`app.py`** — `ACLIApp` class: wraps `typer.Typer`, auto-registers `introspect` and `version` commands, handles `ACLIError` → JSON error envelope conversion
- **`command.py`** — `@acli_command` decorator: attaches `CommandMeta` (examples, idempotency, see_also) to command functions
- **`output.py`** — `OutputFormat` enum + `success_envelope()`/`error_envelope()`/`emit()` for the JSON envelope contract
- **`exit_codes.py`** — `ExitCode` IntEnum mapping the spec's semantic exit codes (0-9)
- **`errors.py`** — `ACLIError` hierarchy (`InvalidArgsError`, `NotFoundError`, `ConflictError`, `PreconditionError`) + `suggest_flag()` for typo correction
- **`introspect.py`** — `build_command_tree()` extracts the full command tree from a Typer app via reflection
- **`cli_folder.py`** — `generate_cli_folder()` writes the `.cli/` reference folder (commands.json, README, examples, changelog)

### Spec core concepts

- **Progressive Discovery**: agents bootstrap understanding via `--help` → `introspect` → `.cli/` folder
- **Output contracts**: all commands support `--output json|text|table`; JSON uses envelope `{ok, command, data|error, meta}`
- **Semantic exit codes**: 0=success, 2=invalid args, 3=not found, 4=permission denied, 5=conflict, 6=timeout, 7=upstream error, 8=precondition failed, 9=dry-run
- **Dry-run**: every state-modifying command must support `--dry-run`
- **Idempotency**: each command declares `idempotent: true|false|conditional`

### Linting conventions

- Ruff with strict rules (pyflakes, pycodestyle, isort, pep8-naming, bugbear, bandit, etc.)
- `B008` is globally ignored — `typer.Option()` in argument defaults is standard Typer pattern
- mypy in strict mode
- `py.typed` marker included for downstream type checking
