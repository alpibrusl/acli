---
title: "Why ACLI? Evolution from MCP to Skills to CLI"
description: How agent tool integration evolved through MCP, SKILLS.md, and ACLI — comparison of schema ownership, discovery, output format, and infrastructure requirements.
---

# Evolution of Agent Tool Integration

AI agents need to use external tools. How those tools are made available to agents has evolved through three distinct stages — each solving limitations of the previous one.

## Stage 1: MCP — Schema injected at startup

The [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) defines tools as JSON schemas that are loaded into the agent's context at startup. The agent sees the full capability surface immediately and can call tools via structured function calls.

**How it works:** A registry or server exposes tool definitions. The agent runtime fetches these schemas before the conversation begins and injects them into the system prompt.

**Strengths:**

- Tools are fully typed and discoverable from the first message
- Structured input/output eliminates parsing ambiguity
- Well-suited for hosted tool ecosystems

**Limitations:**

- Schemas must be defined and maintained *externally* — separate from the tool itself
- Every tool needs a registry entry or server; standalone CLIs are excluded
- Schema drift: the tool changes but the registry definition lags behind
- Context cost: all tool schemas consume tokens whether or not the agent uses them
- Requires infrastructure (MCP server, registry) beyond the tool itself

## Stage 2: SKILLS.md — Human-written instructions

Skills files (e.g., `SKILLS.md`, `.cursorrules`, `CLAUDE.md`) are human-authored documents loaded into the agent's context. They describe available tools, common workflows, and usage patterns in natural language.

**How it works:** A markdown file in the project root tells the agent what tools exist, how to invoke them, and what to watch out for. The agent reads this on first interaction.

**Strengths:**

- Zero infrastructure — just a file in the repo
- Can capture nuance, workflows, and judgment calls that schemas cannot
- Flexible and easy to write

**Limitations:**

- Written and maintained by *humans*, not by the tool itself — always at risk of being stale
- No structured output contract — the agent parses human prose and hopes for the best
- No machine-readable capability discovery — the agent can't programmatically enumerate what a tool can do
- Doesn't scale: a project with 20 tools needs a very long skills file
- One-shot: loaded at context start, no incremental discovery

## Stage 3: ACLI — The tool teaches itself to the agent

ACLI takes a different approach: **the tool is its own documentation**. An agent that encounters an ACLI-compliant tool can bootstrap its understanding entirely at runtime by running `<tool> --help`.

**How it works:**

```
1. Agent runs:  mytool --help          → learns top-level commands
2. Agent runs:  mytool run --help      → learns arguments, types, examples
3. Agent runs:  mytool introspect      → gets full command tree as JSON
4. Agent reads: .cli/README.md         → orients itself (survives context resets)
```

**What makes this different:**

| Property | MCP | SKILLS.md | ACLI |
|----------|-----|-----------|------|
| Who maintains the schema? | Humans (external) | Humans (external) | The tool itself |
| Discovery | All at once (startup) | All at once (startup) | Incremental (on demand) |
| Output format | Structured (JSON) | Unstructured (prose) | Structured (JSON envelope) |
| Error handling | Varies | None | Semantic exit codes + hints |
| Staleness risk | High (registry drift) | High (manual docs) | None (generated from code) |
| Infrastructure needed | MCP server/registry | File in repo | Nothing — just the CLI |
| Token cost | All schemas upfront | Full file upfront | Only what's needed |

**Strengths:**

- The tool *is* the source of truth — no external schema to drift
- Incremental discovery means agents only pay the token cost for what they actually use
- Structured output (JSON envelopes) and semantic exit codes enable reliable automation
- `.cli/` folder provides persistent orientation that survives context resets
- Works with any CLI — no server, no registry, no infrastructure

**Limitations:**

- Requires the tool to be ACLI-compliant (the reason this spec exists)
- First interaction is slower — the agent must run `--help` or `introspect` before it can act
- The tool must be installed and executable (unlike MCP schemas which are pure data)

## They're complementary, not competing

These stages are not mutually exclusive. A well-designed tool ecosystem might use:

- **MCP** for hosted API services where schemas are stable and centrally managed
- **SKILLS.md** for workflow guidance, project conventions, and judgment calls
- **ACLI** for CLI tools that need to be self-describing and independently discoverable

ACLI targets the gap where MCP is too heavy and SKILLS.md is too fragile: **standalone CLI tools that agents need to use reliably without prior configuration**.

## See also

The idea of agents discovering tools at runtime through `--help` has emerged independently in several projects. Notably, [Scion](https://googlecloudplatform.github.io/scion/philosophy/) (Google Cloud Platform) refers to this pattern as **Progressive Skills**. ACLI formalises this concept into a full specification — adding structured output contracts, semantic exit codes, introspection commands, and persistent discovery artifacts.
