---
title: SDKs
description: Language implementations of the ACLI specification in this monorepo.
---

# SDKs

All SDKs follow [`ACLI_SPEC.md`](https://github.com/alpibrusl/acli/blob/main/ACLI_SPEC.md) (v0.1.0 draft). Source lives under [`sdks/<language>/`](https://github.com/alpibrusl/acli/tree/main/sdks) in the repository.

## Published packages

These are released from tagged versions (see the repo [Releases](https://github.com/alpibrusl/acli/releases)).

| Language | Package | Install |
|----------|---------|---------|
| **Python** | [`acli-spec`](https://pypi.org/project/acli-spec/) | `pip install acli-spec` |
| **Rust** | [`acli`](https://crates.io/crates/acli) | `cargo add acli` |
| **TypeScript** | [`@acli/sdk`](https://www.npmjs.com/package/@acli/sdk) | `npm install @acli/sdk` |

## SDKs in-repo (build from source)

These are maintained in the monorepo; install by path or follow each SDK README until a registry publish is configured.

| Language | Path | Notes |
|----------|------|--------|
| **Go** | [`sdks/go`](https://github.com/alpibrusl/acli/tree/main/sdks/go) | Module `github.com/alpibrusl/acli-go` |
| **.NET** | [`sdks/dotnet`](https://github.com/alpibrusl/acli/tree/main/sdks/dotnet) | `Acli.Spec` class library |
| **R** | [`sdks/r`](https://github.com/alpibrusl/acli/tree/main/sdks/r) | Package `acli.spec` |
| **Java** | [`sdks/java`](https://github.com/alpibrusl/acli/tree/main/sdks/java) | Maven `dev.acli:acli-spec` (build locally) |

Per-README setup: [Python](https://github.com/alpibrusl/acli/blob/main/sdks/python/README.md) · [Rust](https://github.com/alpibrusl/acli/blob/main/sdks/rust/README.md) · [Go](https://github.com/alpibrusl/acli/blob/main/sdks/go/README.md) · [.NET](https://github.com/alpibrusl/acli/blob/main/sdks/dotnet/README.md) · [R](https://github.com/alpibrusl/acli/blob/main/sdks/r/README.md) · [Java](https://github.com/alpibrusl/acli/blob/main/sdks/java/README.md)

## Documentation on this site

- **Python** — full guides under [Python SDK](../python-sdk/index.md) (Typer integration, `ACLIApp`, envelopes, introspection, skill CLI).
- **Other languages** — use the spec ([Overview](../spec/index.md)) plus each SDK README in the repository; site sections for Rust/TS/Go/etc. may expand over time.

## Examples

| Example | Location |
|---------|----------|
| Python weather CLI | [`examples/weather/`](https://github.com/alpibrusl/acli/tree/main/examples/weather) |
| Rust | [`examples/weather-rust/`](https://github.com/alpibrusl/acli/tree/main/examples/weather-rust) |
| TypeScript | [`examples/weather-ts/`](https://github.com/alpibrusl/acli/tree/main/examples/weather-ts) |
| Java | [`examples/weather-java/`](https://github.com/alpibrusl/acli/tree/main/examples/weather-java) |
