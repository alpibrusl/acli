# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-04-06

### Added

- **Spec**: optional `meta.cache`, `error.hints`, introspection `since_version` / `deprecated_since` (see `ACLI_SPEC.md`).
- **Python & Rust SDKs**: implement the above (envelopes, introspect param metadata).
- **Monorepo**: Go, .NET, R, and Java SDKs; weather examples (Rust, TypeScript); Java weather example — merged to `develop`.

### Changed (breaking)

- **Rust**: `success_envelope` and `error_envelope` / `error_envelope_raw` signatures extended (`cache`, `hints` parameters).

## [0.3.0] - 2026-04-05

### Added

- **Rust SDK** (`acli` crate) with full feature parity to Python SDK
  - `AcliApp` — application wrapper with error handling and built-in commands
  - `AcliCommand` trait — Rust equivalent of `@acli_command` decorator
  - `acli_args!` macro — auto-injects `--output` and `--dry-run` (with `with dry_run`)
  - `Idempotency` enum — typed `Yes`/`No`/`Conditional` instead of raw values
  - All core modules: envelopes, exit codes, errors, introspect, `.cli/` folder, skill files, NDJSON streaming
  - CI workflow with clippy, rustfmt, cargo test
  - Published to crates.io
- **Python SDK**: auto-inject `--output` on all `@acli_command` decorated commands (§2.1)
- **Python SDK**: auto-inject `--dry-run` on `idempotent=False` commands (§5)
- **Python SDK**: `emit_progress()` and `emit_result()` for NDJSON streaming (§2.3)
- **Python SDK**: `acli validate --deep` — runs tool and verifies JSON envelopes
- Weather example: new `refresh` command demonstrating NDJSON streaming

### Changed (breaking)

- **Rust**: `generate_skill()` now returns `io::Result<String>` instead of `String`
- **Rust**: `error_envelope()` now takes typed `ExitCode` instead of `&str` (use `error_envelope_raw()` for string codes)

## [0.2.0] - 2026-04-05

### Added

- Rust SDK initial release (core modules only, no AcliApp/macro)
- Python SDK: auto-inject and deep validation features

## [0.1.4] - 2026-04-05

### Fixed

- Fix duplicate template files in Python wheel (caused PyPI upload rejection)
- First successful PyPI publish

## [0.1.1] - 2026-04-05

### Fixed

- Release pipeline: fix PyPI Trusted Publishing environment configuration

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

[Unreleased]: https://github.com/alpibrusl/acli/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/alpibrusl/acli/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/alpibrusl/acli/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/alpibrusl/acli/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/alpibrusl/acli/compare/v0.1.1...v0.1.4
[0.1.1]: https://github.com/alpibrusl/acli/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/alpibrusl/acli/releases/tag/v0.1.0
