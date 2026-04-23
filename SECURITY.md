# Security Policy

## Reporting a Vulnerability

Private disclosure via GitHub Security Advisories on
<https://github.com/alpibrusl/acli> or email to `security@alpibru.com`.
Do not open a public issue.

Include: description, steps to reproduce, affected SDK + version, and a
proof of concept if you have one.

## Supported Versions

The spec is `v0.1.0` (Draft). SDK support:

| SDK | Status |
|---|---|
| Python (`acli-spec`) | First-party — security fixes backported |
| Rust (`acli`) | First-party — security fixes backported |
| TypeScript (`@acli/sdk`) | First-party — security fixes backported |
| Go / Java / R / .NET | Community — see `sdks/<lang>/README.md`; may lag |

## Trust Model

ACLI is a specification and a set of SDKs that help CLI authors emit a
standard JSON envelope, expose an `introspect` command, and generate
a `SKILL.md` artefact. The SDKs themselves are narrow: they wrap Typer
(Python), Clap (Rust), or Commander (TypeScript) and do not ship
command execution, credential storage, or network I/O primitives.

### Attack surface of the SDKs

- **The SDK does not execute user-supplied commands.** It only formats
  the output of commands the tool author defined.
- **It does not deserialize untrusted code.** The `introspect` output
  is built via reflection on the tool's own CommandTree in-process.
- **No network I/O.** The SDKs make no HTTP / socket calls.

### What the spec says about CLI authors

The spec defines the *shape* of output, exit codes, and `--help`
structure. It does not force any security behaviour on the underlying
tool. An ACLI-compliant tool can still be malicious or buggy — the
badge does not imply an audited implementation, only conformance to
the I/O contract.

### Envelope fields

- `ok: bool` is the only field agents are instructed to trust for
  success/failure classification. Error messages may leak internal
  detail if the CLI author includes it; that's a per-tool concern.
- `data` is free-form JSON and is not validated by the SDK. Tools
  that accept agent input and echo it back should sanitise as usual.

### Skill generation

- `acli skill` (Python SDK) writes a `SKILL.md` from the current
  command tree. The resulting file is a static artefact — **if the
  spec changes or the tool's commands evolve, the checked-in
  `SKILL.md` can drift**. Treat it like any other generated file:
  regenerate in CI and fail the build if the diff is non-empty.

### Conformance testing

A conformance test suite does not yet exist. "ACLI-compliant"
currently means "uses the SDK envelope and exit codes". A downstream
tool can claim compliance without being audited. Tracked in issue #22.

## What this document does not cover

- The security posture of individual tools built with ACLI. Each tool
  ships its own threat model and trust boundaries.
- The hosted PyPI / crates.io / npm publishing channels for SDK
  artefacts — rely on the platform's signing + 2FA requirements.
