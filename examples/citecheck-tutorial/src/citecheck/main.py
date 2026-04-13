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
