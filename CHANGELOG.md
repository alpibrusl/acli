# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-05

### Added

- ACLI specification v0.1.0 (draft)
- Python SDK (`acli-spec`) with Typer integration
  - `ACLIApp` application wrapper with auto-registered `introspect` and `version` commands
  - `@acli_command` decorator for examples, idempotency, and see_also metadata
  - `OutputFormat` enum with `text`, `json`, `table` support
  - JSON success/error envelope builders
  - Semantic exit codes (0–9) as `ExitCode` IntEnum
  - Error hierarchy: `ACLIError`, `InvalidArgsError`, `NotFoundError`, `ConflictError`, `PreconditionError`
  - `suggest_flag()` for typo correction
  - `.cli/` folder generation and update detection
  - Command tree introspection via reflection
- MkDocs Material documentation site
- CI pipeline with Python 3.10–3.13 matrix
- Release pipeline with PyPI Trusted Publishing

[Unreleased]: https://github.com/alpibrusl/acli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alpibrusl/acli/releases/tag/v0.1.0
