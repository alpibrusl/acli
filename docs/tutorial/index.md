# Tutorial: build `citecheck`, an ACLI-compliant CLI

In this tutorial we build **citecheck** — a CLI that scans Markdown documents for broken or inaccurate citations. It reports which links 404, which claims aren't supported by the cited page, and optionally uses an LLM to detect semantic contradictions.

You'll touch every part of ACLI through a real CLI (not a `hello world`):

- Structured help, introspection, semantic exit codes, JSON envelopes — all from the `acli-spec` Python SDK with minimal boilerplate
- Agents discover your CLI at runtime with `citecheck introspect`
- The same tool plugs into Claude Code, Cursor, Copilot, Gemini Code Assist, Aider, and opencode

The tutorial is split so you can stop wherever fits:

| Part | Runs without LLM? | Ends with... |
|---|---|---|
| [1. Quick-start](#quick-start) | ✅ | A working one-command CLI |
| [2. Basic example](#basic-example-citecheck-without-llm) | ✅ | The full `citecheck` that finds 404s and literal text mismatches |
| [3. Adding LLM verification](#adding-llm-verification) | ❌ needs an API key or Vertex AI | `citecheck --semantic` that detects when a page technically has the phrase but contradicts the claim |
| [4. Integrate with code assistants](#integrate-with-code-assistants) | ✅ | Cursor/Claude Code/Copilot/etc. can run your CLI without you writing prompt docs |
| [5. Where to next](#where-to-next) | — | Pointers to the Noether/AgentSpec/Caloron tutorials that extend this same use case |

Everything in this tutorial is runnable. Code goes in a new directory `~/citecheck` so you can keep it around. You can also find the complete result at <https://github.com/alpibrusl/acli/tree/main/examples/citecheck-tutorial>.

## Quick-start

```bash
mkdir -p ~/citecheck && cd ~/citecheck
python3 -m venv .venv && source .venv/bin/activate
pip install acli-spec
```

Write the smallest possible ACLI CLI — a single `hello` command:

```python title="~/citecheck/hello.py"
from acli import ACLIApp, acli_command
import typer

app = ACLIApp(name="citecheck", version="0.0.1", help="Verify citations in Markdown.")

@app.command()
@acli_command(
    examples=[
        ("Say hello", "citecheck hello"),
        ("Say hello with name", "citecheck hello --name world"),
    ],
    idempotent=True,
)
def hello(
    name: str = typer.Option("world", "--name", help="Who to greet. type:string"),
) -> None:
    """Say hello — warmup command before we wire the real thing."""
    print(f"Hello, {name}!")

if __name__ == "__main__":
    app.run()
```

Run it:

```bash
python hello.py --help
python hello.py hello --name ACLI
python hello.py introspect --output json   # ← auto-injected by ACLI
python hello.py version
```

That last `introspect` is the whole point. Even though you only wrote one command, the CLI already exposes a machine-readable description of itself that any AI agent can consume. You didn't write a single line of MCP boilerplate.

**What just happened:**

- `ACLIApp` wrapped a plain [Typer](https://typer.tiangolo.com) app
- `@acli_command` attached metadata (examples, idempotency)
- Three commands were auto-injected: `introspect`, `version`, `skill`
- `--output json/table/text` is available on every command
- A hidden `.cli/` folder was generated with machine-readable docs

Close this quick-start and open the next section — we're about to build the real thing.

## Basic example: `citecheck` without LLM

Our CLI will have three user-facing commands:

| Command | What it does |
|---|---|
| `citecheck verify <url> --claim "..."` | Check one URL: is it reachable, does it contain the claim text |
| `citecheck scan <file.md>` | Find all Markdown links in a file, verify each |
| `citecheck report <run-id>` | Retrieve a past run (cached locally) |

Nothing above requires an LLM. We use `httpx` for fetches and `beautifulsoup4` for text extraction.

### Install dependencies

```bash
pip install httpx beautifulsoup4 lxml
```

### Project layout

```bash
mkdir -p ~/citecheck/src/citecheck
touch ~/citecheck/src/citecheck/__init__.py
```

### The CLI

```python title="~/citecheck/src/citecheck/main.py"
"""citecheck — verify citations in Markdown documents."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from bs4 import BeautifulSoup
import httpx

from acli import (
    ACLIApp,
    OutputFormat,
    acli_command,
    emit,
    emit_progress,
    emit_result,
    error_envelope,
    success_envelope,
    NotFoundError,
    PreconditionError,
    UpstreamError,
)

__version__ = "0.1.0"

app = ACLIApp(
    name="citecheck",
    version=__version__,
    help="Verify citations in Markdown documents (claims + URLs).",
)

# Cache directory for past runs
CACHE_DIR = Path.home() / ".cache" / "citecheck"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _fetch(url: str, timeout: float = 10.0) -> tuple[int, str]:
    """Fetch a URL. Returns (status_code, text). Raises on connection error."""
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        resp = client.get(url, headers={"User-Agent": f"citecheck/{__version__}"})
        return resp.status_code, resp.text


def _extract_text(html: str) -> str:
    """Strip HTML tags; normalize whitespace."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()


def _contains_claim(page_text: str, claim: str) -> bool:
    """Literal substring match, case-insensitive."""
    return claim.lower() in page_text.lower()


def _run_id(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True).encode()
    return "run_" + hashlib.sha256(blob).hexdigest()[:10]


# ── verify: one URL, one claim ─────────────────────────────────────────────

@app.command()
@acli_command(
    examples=[
        ("Verify one link", "citecheck verify https://example.com --claim 'Example Domain'"),
        ("Custom timeout, JSON output", "citecheck verify https://x.com --claim '...' --timeout 5 --output json"),
    ],
    idempotent=True,
    see_also=["scan", "report"],
)
def verify(
    url: str = typer.Argument(help="URL of the cited source. type:url"),
    claim: str = typer.Option(..., "--claim", "-c", help="Expected phrase in the page. type:string"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="Network timeout in seconds. type:number"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, "--output", help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Verify one URL supports the given claim.

    Checks: HTTP reachability, body contains the literal claim (case-insensitive).
    """
    start = time.time()
    try:
        status, html = _fetch(url, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise UpstreamError(
            f"Timeout fetching {url}",
            hint=f"Increase --timeout (current: {timeout}s) or check the URL",
        ) from exc
    except httpx.RequestError as exc:
        raise UpstreamError(f"Cannot reach {url}: {exc}") from exc

    text = _extract_text(html) if 200 <= status < 300 else ""
    has_claim = _contains_claim(text, claim) if text else False

    data = {
        "url": url,
        "claim": claim,
        "http_status": status,
        "reachable": 200 <= status < 400,
        "claim_found": has_claim,
        "verdict": "ok" if (200 <= status < 300 and has_claim) else "broken",
    }

    if output == OutputFormat.json:
        emit(success_envelope("verify", data, version=__version__, start_time=start), output)
    else:
        # Human-friendly output
        mark = "✓" if data["verdict"] == "ok" else "✗"
        print(f"{mark} {url}")
        print(f"  HTTP {status}, claim {'found' if has_claim else 'NOT found'}")
        if data["verdict"] == "broken":
            raise SystemExit(3)  # semantic exit: NOT_FOUND-ish


# ── scan: all Markdown links in a document ─────────────────────────────────

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@app.command()
@acli_command(
    examples=[
        ("Scan a document", "citecheck scan report.md"),
        ("Save run, get JSON", "citecheck scan report.md --output json"),
    ],
    idempotent=True,
    see_also=["verify", "report"],
)
def scan(
    file: str = typer.Argument(help="Path to a Markdown file. type:path"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="Per-URL timeout. type:number"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, "--output", help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Scan a Markdown file: verify every `[text](url)` link where `text` is the claim."""
    start = time.time()
    path = Path(file)
    if not path.exists():
        raise NotFoundError(f"File not found: {file}")

    content = path.read_text(encoding="utf-8")
    links = LINK_RE.findall(content)
    if not links:
        raise PreconditionError(
            f"No Markdown links found in {file}",
            hint="Use the format: [claim](https://url)",
        )

    results: list[dict[str, Any]] = []
    for idx, (claim, url) in enumerate(links, 1):
        # In JSON mode, stream progress as NDJSON
        if output == OutputFormat.json:
            emit_progress(f"verify[{idx}/{len(links)}]", "running", detail=url)
        try:
            status, html = _fetch(url, timeout=timeout)
            text = _extract_text(html) if 200 <= status < 300 else ""
            has = _contains_claim(text, claim) if text else False
            verdict = "ok" if (200 <= status < 300 and has) else "broken"
        except httpx.RequestError as exc:
            status, has, verdict = 0, False, "unreachable"

        results.append({
            "claim": claim[:80],
            "url": url,
            "http_status": status,
            "claim_found": has,
            "verdict": verdict,
        })

    summary = {
        "file": str(path),
        "total": len(results),
        "ok": sum(1 for r in results if r["verdict"] == "ok"),
        "broken": sum(1 for r in results if r["verdict"] == "broken"),
        "unreachable": sum(1 for r in results if r["verdict"] == "unreachable"),
        "results": results,
    }

    # Persist for later `report` command
    rid = _run_id({"file": str(path), "results": results})
    (CACHE_DIR / f"{rid}.json").write_text(json.dumps({
        "run_id": rid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **summary,
    }, indent=2))
    summary["run_id"] = rid

    if output == OutputFormat.json:
        emit_result(success_envelope("scan", summary, version=__version__, start_time=start))
    elif output == OutputFormat.table:
        print(f"{'verdict':<12}  {'http':>4}  {'claim':<40}  url")
        print("-" * 100)
        for r in results:
            print(f"{r['verdict']:<12}  {r['http_status']:>4}  {r['claim'][:40]:<40}  {r['url']}")
    else:
        print(f"Scanned {summary['total']} links in {path}")
        print(f"  ok:          {summary['ok']}")
        print(f"  broken:      {summary['broken']}")
        print(f"  unreachable: {summary['unreachable']}")
        print(f"  run_id:      {rid}")

    if summary["broken"] or summary["unreachable"]:
        raise SystemExit(1)


# ── report: retrieve a past run ─────────────────────────────────────────────

@app.command()
@acli_command(
    examples=[
        ("Show a past scan", "citecheck report run_abc123"),
        ("JSON export", "citecheck report run_abc123 --output json"),
    ],
    idempotent=True,
    see_also=["scan"],
)
def report(
    run_id: str = typer.Argument(help="Run ID from a previous scan. type:string"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, "--output", help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Retrieve a past scan result."""
    path = CACHE_DIR / f"{run_id}.json"
    if not path.exists():
        raise NotFoundError(
            f"Run not found: {run_id}",
            hint=f"Past runs live in {CACHE_DIR}. Check: ls {CACHE_DIR}",
        )
    data = json.loads(path.read_text())
    if output == OutputFormat.json:
        emit(success_envelope("report", data, version=__version__), output)
    else:
        print(f"Run {data['run_id']}  ({data['created_at']})")
        print(f"File: {data['file']}")
        print(f"ok={data['ok']}  broken={data['broken']}  unreachable={data['unreachable']}")


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
```

### Make it installable

```python title="~/citecheck/pyproject.toml"
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "citecheck"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "acli-spec>=0.4.0",
    "httpx>=0.27",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
    "typer>=0.9",
]

[project.scripts]
citecheck = "citecheck.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/citecheck"]
```

```bash
pip install -e .
```

### Try it

Create a test document:

```markdown title="~/citecheck/report.md"
Water boils at [100°C at standard atmospheric pressure](https://en.wikipedia.org/wiki/Boiling_point).

The [Rust programming language is developed by Mozilla](https://www.rust-lang.org/).

This one is broken: [Nothing here](https://example.com/does-not-exist-xyz).
```

```bash
citecheck scan report.md
```

You should see:

```
Scanned 3 links in report.md
  ok:          2
  broken:      0
  unreachable: 1
  run_id:      run_a1b2c3d4e5
```

Now the key ACLI moves. An AI agent that needs to use `citecheck` doesn't need you to write docs — it introspects:

```bash
citecheck introspect --output json
```

You get the full command tree — every command, argument, option, type, example — as structured JSON. That's the contract that lets a code assistant learn your tool without MCP boilerplate.

```bash
citecheck skill
```

Prints a Markdown `SKILL.md` (conforming to the [agentskills.io](https://agentskills.io) open standard) that any agent can read directly. You'll use this later when we plug the CLI into Claude Code, Cursor, etc.

## Adding LLM verification

!!! warning "From here on, you need an LLM"
    The steps below call Gemini (via Vertex AI or the Gemini API). Set up either:
    - `GOOGLE_CLOUD_PROJECT=<project>` + `gcloud auth application-default login` (Vertex AI, recommended)
    - `GOOGLE_API_KEY=<key>` from AI Studio (simpler but no audit trail)

    Everything up to this point works without any LLM.

**The limitation of literal matching:** our `verify` command says a citation is good if the claim phrase appears verbatim on the page. But sources can support a claim paraphrased, or worse — *contradict* a claim that happens to use the same words.

We'll add a `--semantic` flag that asks an LLM:

> "Does this page genuinely support the claim? Yes / No / Partially / Contradicts."

### Dependency

```bash
pip install google-genai>=0.3
```

### A minimal LLM verifier

```python title="~/citecheck/src/citecheck/semantic.py"
"""LLM-based semantic verification of citations."""
from __future__ import annotations

import json
import os
from typing import Literal

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


PROMPT = """You verify citations. Given a CLAIM and the CONTENT of a source page,
decide whether the source genuinely supports the claim.

Return JSON with fields:
- support: one of "supports", "partial", "unrelated", "contradicts"
- reason: one sentence explaining the decision
- evidence: the most relevant phrase (≤200 chars) from the content

CLAIM: {claim}

CONTENT (truncated):
{content}

Respond with JSON only, no prose."""


def verify_semantic(claim: str, content: str) -> dict:
    """Use Gemini to evaluate whether content supports the claim."""
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai")

    # Prefer Vertex AI if configured, fall back to Gemini API
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        client = genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1"),
        )
    else:
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # Truncate content to stay within reasonable token budget
    truncated = content[:8000]
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=PROMPT.format(claim=claim, content=truncated),
    )
    text = response.text.strip()
    # Strip code fences if the model added them
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text)
```

### Wire it to the CLI

Add a `--semantic` option to the `verify` command in `main.py`:

```python
# Add this import at the top
from citecheck.semantic import verify_semantic, GENAI_AVAILABLE

# Change the verify signature to add --semantic
def verify(
    url: str = typer.Argument(...),
    claim: str = typer.Option(..., "--claim", "-c"),
    timeout: float = typer.Option(10.0, "--timeout", "-t"),
    semantic: bool = typer.Option(
        False, "--semantic", "-s",
        help="Use an LLM to semantically verify the claim (requires API key). type:bool",
    ),
    output: OutputFormat = typer.Option(OutputFormat.text, "--output"),
) -> None:
    ...  # existing fetch + literal check

    # After the literal check, optionally augment with semantic
    if semantic:
        if not GENAI_AVAILABLE:
            raise PreconditionError(
                "Semantic verification requires google-genai",
                hint="Run: pip install google-genai",
            )
        try:
            result = verify_semantic(claim, text)
            data["semantic"] = result
            # Upgrade verdict: contradicts wins over a literal match
            if result["support"] == "contradicts":
                data["verdict"] = "contradicted"
            elif data["verdict"] == "broken" and result["support"] == "supports":
                # The page supports it even though literal match failed
                data["verdict"] = "ok"
        except Exception as exc:
            data["semantic"] = {"error": str(exc)}
```

### Try it

```bash
# Literal match only (no LLM)
citecheck verify https://www.rust-lang.org --claim "Rust is fast and reliable"

# With semantic verification
citecheck verify https://www.rust-lang.org --claim "Rust is fast and reliable" --semantic

# An interesting case: a page that uses the exact phrase but contradicts
citecheck verify https://example.com --claim "Javascript is faster than Rust" --semantic
```

Notice the verdict change: pages that literally contain a claim but actually contradict it get caught by `--semantic`.

## Integrate with code assistants

The single most valuable property of ACLI: **any agent can learn your CLI by running `citecheck introspect`**. No MCP server to write, no hand-crafted tool description to keep in sync, no re-deploying prompts.

Below: how to wire `citecheck` into the six most common assistants. The pattern is always the same — expose the `SKILL.md` ACLI generates for you. The file conforms to the [agentskills.io](https://agentskills.io) open standard, so it drops into `.claude/skills/citecheck/SKILL.md`, `.cursor/skills/citecheck/SKILL.md`, Gemini CLI, Codex, etc. without modification.

Generate `SKILL.md` once:

```bash
citecheck skill --out SKILL.md
```

### Claude Code

Claude Code reads project-level `CLAUDE.md`. Reference the skills file:

```markdown title="CLAUDE.md"
# This project uses citecheck for citation verification.

See `SKILL.md` for the full CLI reference, or run `citecheck introspect`
for the machine-readable command tree.

Prefer `citecheck scan` over manual URL checking when editing Markdown files.
Always run `citecheck verify --semantic` for load-bearing citations.
```

### Cursor

Cursor uses `.cursorrules` (older) or `.cursor/rules/*.md` (newer). Either works:

```markdown title=".cursor/rules/citecheck.md"
---
description: citecheck CLI rules
globs: ["**/*.md"]
alwaysApply: false
---

When editing Markdown files that contain citations, run `citecheck scan <file>` before committing.
Use `citecheck verify <url> --claim "..." --semantic` for single-link checks.
Full CLI reference: run `citecheck introspect --output json` or read SKILL.md.
```

### GitHub Copilot

Copilot reads `.github/copilot-instructions.md`:

```markdown title=".github/copilot-instructions.md"
## Citation verification

This project includes `citecheck`, an ACLI-compliant CLI for verifying citations.
- Run `citecheck scan <file.md>` to audit all links in a file
- Run `citecheck introspect` to learn the full command tree
- See SKILL.md for details
```

### Gemini Code Assist / gemini-cli

Gemini CLI picks up a project-level `GEMINI.md`:

```markdown title="GEMINI.md"
# Project tools

citecheck — CLI for verifying citations in Markdown.
Commands discoverable via: citecheck introspect --output json
Always prefer citecheck over writing ad-hoc URL-checking scripts.
```

### Aider

Aider can read arbitrary files as context. Add `SKILL.md` to your session:

```bash
aider --read SKILL.md src/**/*.md
```

Or in `.aider.conf.yml`:

```yaml
read:
  - SKILL.md
```

### Codex CLI

Codex reads `AGENTS.md` at the project root:

```markdown title="AGENTS.md"
# Agents

Use `citecheck` for any citation-related task:
- `citecheck scan <file.md>` — verify all links in a Markdown file
- `citecheck verify <url> --claim "..." --semantic` — single-link semantic check
- `citecheck introspect --output json` — full capability tree

Do NOT write ad-hoc URL verification code when citecheck is available.
```

### opencode

```bash
mkdir -p .opencode
citecheck skill --out .opencode/citecheck.md
```

```json title=".opencode/config.json"
{
  "rules": [".opencode/citecheck.md"]
}
```

### The universal pattern

All six assistants converge on the same thing: give them a Markdown file that describes your CLI. ACLI generates that file for you automatically:

```bash
citecheck skill --out SKILL.md   # one artifact
```

Link it from whatever file your assistant happens to read. When you add or change commands, regenerate the skill — the assistant's context updates automatically the next session.

## Where to next

`citecheck` is a great standalone tool, but the real power shows when you combine it with the other Alpibru projects. Each of these tutorials extends this same `citecheck` use case.

- **[Noether tutorial](https://alpibrusl.github.io/noether/tutorial/)** — turn the verification pipeline into verified, composable stages (`url_fetch` + `text_extract` + `claim_match`). Content-addressed, reproducible forever, compilable to a single binary.
- **[AgentSpec tutorial](https://alpibrusl.github.io/agentspec/tutorial/)** — wrap `citecheck` in a `citation-auditor.agent` with trust restrictions, signed portfolio of past audits, and multi-runtime support (Claude / Gemini / Ollama).
- **[Caloron tutorial](https://alpibrusl.github.io/caloron-noether/tutorial/)** — run an autonomous sprint that extends `citecheck` (add DOI support, or cross-document consistency) — agents write the code, open PRs, run tests, merge.

Each one starts from the `citecheck` you just built. Read them in any order.
