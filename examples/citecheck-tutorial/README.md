# citecheck-tutorial

Reference implementation of the `citecheck` CLI built in the
[ACLI tutorial](https://alpibrusl.github.io/acli/tutorial/). It scans Markdown
documents for broken or inaccurate citations: which links 404, which claims
aren't supported by the cited page, and (optionally) which contradict it.

The tutorial walks through how every piece of this CLI gets built. This package
is the runnable end-state of Parts 1-3, exactly as the docs describe.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

For the optional LLM-based semantic verification:

```bash
pip install -e ".[llm]"
```

## Usage

```bash
# Verify a single URL against a claim
citecheck verify https://example.com --claim "Example Domain"

# Scan every Markdown link in a file
citecheck scan examples/report.md

# Retrieve a past run from the local cache
citecheck report <run_id>

# ACLI auto-injected commands
citecheck introspect --output json
citecheck skill
citecheck version
```

With the `[llm]` extra installed and `GOOGLE_API_KEY` (or
`GOOGLE_CLOUD_PROJECT` for Vertex AI) set, the `--semantic` flag adds an LLM
check that catches paraphrases and contradictions.

## Tests

```bash
pip install pytest
pytest
```

Tests don't touch the network (they monkeypatch `httpx`).

## License

EUPL-1.2
