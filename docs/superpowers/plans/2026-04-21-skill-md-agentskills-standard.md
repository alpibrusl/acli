# SKILL.md agentskills Standard Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the acli `skill` subcommand across all 7 SDKs from the custom `SKILLS.md` manual to the `SKILL.md` file format defined by the agentskills.io / Claude Code open standard: YAML frontmatter (`name`, `description`, `when_to_use`) + the existing markdown body.

**Architecture:** Same generator shape in every SDK — prepend frontmatter, keep the existing body. File name changes from `SKILLS.md` → `SKILL.md`. Public API of each generator grows two optional parameters (`description`, `when_to_use`); when omitted we synthesize a sensible default from the command tree. No backwards-compatibility shims (user has explicitly waived them).

**Tech Stack:** Python (ruff, mypy, pytest), TypeScript (vitest/jest — check), Rust (cargo test), Go (go test), Java (Maven, JUnit), .NET (xUnit or similar), R (testthat). Plus ACLI_SPEC.md, MkDocs docs, and weather/citecheck examples.

---

## Canonical SKILL.md shape

Every generator MUST emit content that starts with this frontmatter block, followed by the existing body (title, commands, exit codes, etc.):

```
---
name: <tool-name>
description: <single line; either caller-supplied or "Invoke the `<tool>` CLI for its registered commands.">
when_to_use: <optional; only emitted when caller supplies it>
---

# <tool-name>
…existing body…
```

**Rules:**
- `name` is always present — taken from the command tree `name` field.
- `description` is always present. Default when not supplied: ``Invoke the `<name>` CLI. Commands: <cmd1>, <cmd2>, …`` (first 4 non-builtin command names, joined with `, `, with trailing `…` if more exist).
- `when_to_use` is optional — only rendered when the caller passes a non-empty value.
- Frontmatter values MUST be single-line strings (no multi-line YAML). If a caller passes a multi-line value, the generator replaces newlines with a single space (defensive; avoids breaking the YAML block).
- The line immediately after the closing `---` of the frontmatter is a blank line, then the `# <name>` heading.

## Canonical file name

`SKILL.md` everywhere. All examples, docs, tests, fixtures, and default output paths use the singular form.

---

## File Structure

Files to modify (grouped by SDK):

**Python** (`sdks/python/`)
- Modify: `src/acli/skill.py` — `generate_skill()` signature + emit frontmatter.
- Modify: `src/acli/app.py:128-154` — `_register_skill` default out path + docstring.
- Modify: `src/acli/cli.py` — the `acli skill` meta-command description text (grep for `SKILLS.md` / `SKILLS`).
- Modify: `tests/test_skill.py` — rename fixture path, add frontmatter tests.
- Modify: `tests/test_app.py`, `tests/test_cli.py` — any references to `SKILLS.md`.

**TypeScript** (`sdks/typescript/`)
- Modify: `src/skill.ts` — `generateSkill()` signature + emit frontmatter.
- Modify: `src/app.ts` — if the file name is hardcoded there.
- Modify: `tests/sdk.test.ts` — fixture path + new frontmatter test.

**Rust** (`sdks/rust/`)
- Modify: `src/skill.rs` — `generate_skill()` signature + emit frontmatter.
- Modify: `tests/integration_test.rs` — fixture path + new frontmatter test.

**Go** (`sdks/go/`)
- Modify: `skill.go` — `GenerateSkill()` signature + emit frontmatter.
- Modify: `app.go:65-89` — `HandleSkill()` default path if any.
- Modify: any `*_test.go` under `sdks/go/`.

**Java** (`sdks/java/`)
- Modify: `src/main/java/dev/acli/Skill.java` — `generateSkill()` overloads.
- Modify: `src/main/java/dev/acli/AcliApp.java` — `handleSkill()`.
- Modify: `src/main/java/dev/acli/picocli/BuiltInCommands.java` if the file name is hardcoded.
- Modify: `src/test/java/dev/acli/SdkTest.java`.

**.NET** (`sdks/dotnet/`)
- Modify: `Acli.Spec/Skill.cs` — `Generate()`.
- Modify: `Acli.Spec/AcliApp.cs` — built-in skill command.
- Modify: tests (check `Acli.Spec.Tests/`).

**R** (`sdks/r/`)
- Modify: `R/acli.R` — `acli_skill_generate()` signature.
- Modify: `tests/testthat/test-acli.R`.

**Cross-cutting**
- Modify: `ACLI_SPEC.md` — update §Evolution (line 14), add §SKILL.md contract referencing agentskills.io, update any `SKILLS.md` string to `SKILL.md`.
- Modify: `docs/tutorial/index.md`, `docs/python-sdk/skill.md`, `docs/spec/evolution.md`, `docs/example.md`, `docs/sdks/index.md`, `docs/index.md`, `mkdocs.yml` (if referenced), `README.md`, `CHANGELOG.md`.
- Regenerate: `examples/weather/.cli/*` and `examples/weather/SKILL.md` (delete old `SKILLS.md`).
- Update: `examples/citecheck-tutorial/README.md`, `examples/weather-java/…`, `examples/weather-rust/src/main.rs`, `examples/weather-ts/…` — any `SKILLS.md` references.

---

## Task 1: Spec update — define SKILL.md contract

**Files:**
- Modify: `ACLI_SPEC.md`

- [ ] **Step 1: Update the Evolution block (line 14)**

Old:
```
MCP           → schema defined externally, injected at agent startup
SKILLS.md     → instructions written by humans, loaded into context
<cli> --help  → tool teaches itself to the agent on demand (Progressive Skills)
```

New:
```
MCP           → schema defined externally, injected at agent startup
SKILL.md      → authored instructions (agentskills.io open standard)
<cli> --help  → tool teaches itself to the agent on demand (Progressive Skills)
```

- [ ] **Step 2: Add an "Agent Skills bridge" section**

After the Progressive Discovery section, insert a new section describing how ACLI tools emit a `SKILL.md` that conforms to [agentskills.io](https://agentskills.io). Use this text (copy verbatim — keep it tight):

```markdown
### 1.4 `SKILL.md` bridge (agentskills.io)

Every ACLI tool SHOULD expose a `skill` subcommand that emits a `SKILL.md` conforming to the [Agent Skills open standard](https://agentskills.io). This gives agents (Claude Code, Cursor, Gemini CLI, Codex, Copilot, …) a drop-in bootstrap file without having to learn ACLI conventions first.

The emitted file MUST:
- Be named `SKILL.md` (singular).
- Begin with a YAML frontmatter block containing at minimum `name` and `description`. `when_to_use` is RECOMMENDED when the tool's scope is narrow enough to state it.
- Have single-line frontmatter values (no multi-line YAML).
- After the frontmatter, render the same `--help`-equivalent body described by this spec (commands, options, arguments, exit codes, examples).

Example:

~~~markdown
---
name: weather
description: Invoke the `weather` CLI to fetch forecasts and alerts.
when_to_use: Use when the user asks about weather, forecasts, or regional advisories.
---

# weather

…
~~~

ACLI does not redefine the frontmatter schema; any additional keys supported by agentskills.io (e.g. `allowed-tools`, `argument-hint`) MAY be passed through verbatim by SDK implementations but are not required.
```

- [ ] **Step 3: Grep-replace remaining references**

Run: `Grep -n "SKILLS.md" ACLI_SPEC.md` — replace each non-evolution reference with `SKILL.md`. Keep the one in the Credits (line 444) unchanged (historical).

- [ ] **Step 4: Commit**

```bash
git add ACLI_SPEC.md
git commit -m "spec: align \`skill\` subcommand with agentskills.io standard (SKILL.md + frontmatter)"
```

---

## Task 2: Python SDK — generator + frontmatter

**Files:**
- Modify: `sdks/python/src/acli/skill.py`
- Modify: `sdks/python/tests/test_skill.py`

- [ ] **Step 1: Add failing test for frontmatter defaults**

Append to `sdks/python/tests/test_skill.py` (inside `TestGenerateSkill`):

```python
def test_frontmatter_default_description(self) -> None:
    content = generate_skill(_sample_tree())
    assert content.startswith("---\n")
    lines = content.splitlines()
    assert lines[1] == "name: noether"
    assert lines[2].startswith("description: ")
    assert "noether" in lines[2]
    assert "run" in lines[2] or "status" in lines[2]
    # when_to_use is omitted by default
    closing_idx = lines.index("---", 1)
    block = lines[:closing_idx + 1]
    assert not any(l.startswith("when_to_use:") for l in block)

def test_frontmatter_explicit(self) -> None:
    content = generate_skill(
        _sample_tree(),
        description="Run Noether pipelines.",
        when_to_use="Use when deploying pipelines.",
    )
    lines = content.splitlines()
    assert "description: Run Noether pipelines." in lines
    assert "when_to_use: Use when deploying pipelines." in lines

def test_frontmatter_strips_newlines(self) -> None:
    content = generate_skill(
        _sample_tree(),
        description="Line 1\nLine 2",
    )
    lines = content.splitlines()
    assert "description: Line 1 Line 2" in lines

def test_frontmatter_precedes_title(self) -> None:
    content = generate_skill(_sample_tree())
    lines = content.splitlines()
    closing = lines.index("---", 1)
    # blank line after closing, then heading
    assert lines[closing + 1] == ""
    assert lines[closing + 2] == "# noether"
```

- [ ] **Step 2: Run tests to verify failures**

Run: `cd sdks/python && pytest tests/test_skill.py -v`
Expected: the four new tests FAIL (no frontmatter emitted); existing tests PASS.

- [ ] **Step 3: Implement frontmatter in `generate_skill`**

Replace `sdks/python/src/acli/skill.py` body with the version below. Key changes: new `description` and `when_to_use` parameters, `_default_description()` helper, frontmatter emitted first, docstring updated to reference agentskills.io.

```python
"""Generate SKILL.md files from ACLI command trees.

Emits a file conforming to the agentskills.io open standard
(https://agentskills.io): YAML frontmatter (`name`, `description`, optional
`when_to_use`) followed by the ACLI command reference body. The generated
file is a drop-in for `.claude/skills/<tool>/SKILL.md`,
`.cursor/skills/<tool>/SKILL.md`, Gemini CLI, Codex, etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

_BUILTIN_COMMANDS = ("introspect", "version", "skill")

_OUTPUT_SECTION = (
    "All commands support `--output json|text|table`. "
    "When using `--output json`, responses follow a standard envelope:"
)

_JSON_EXAMPLE = (
    '{"ok": true, "command": "...", "data": {...}, "meta": {"duration_ms": ..., "version": "..."}}'
)

_ERROR_SECTION = (
    'Errors use the same envelope with `"ok": false` and an '
    '`"error"` object containing `code`, `message`, `hint`, and `docs`.'
)


def _default_description(name: str, user_commands: list[dict[str, Any]]) -> str:
    if not user_commands:
        return f"Invoke the `{name}` CLI."
    shown = [c["name"] for c in user_commands[:4]]
    suffix = "…" if len(user_commands) > 4 else ""
    return f"Invoke the `{name}` CLI. Commands: {', '.join(shown)}{suffix}"


def _one_line(value: str) -> str:
    return " ".join(value.split())


def generate_skill(
    command_tree: dict[str, Any],
    *,
    target_path: Path | None = None,
    description: str | None = None,
    when_to_use: str | None = None,
) -> str:
    """Generate a SKILL.md file from an ACLI command tree.

    Args:
        command_tree: Full command tree (as produced by ``build_command_tree``).
        target_path: If provided, write the skill file to this path.
        description: Frontmatter ``description``. When omitted, synthesised
            from the tool name and its first few user-facing commands.
        when_to_use: Optional frontmatter ``when_to_use``. Only rendered when
            explicitly supplied.

    Returns:
        The generated skill file content as a string.
    """
    name = command_tree.get("name", "tool")
    version = command_tree.get("version", "0.0.0")
    commands = command_tree.get("commands", [])
    user_commands = [c for c in commands if c["name"] not in _BUILTIN_COMMANDS]

    desc = _one_line(description) if description else _default_description(name, user_commands)

    lines: list[str] = ["---", f"name: {name}", f"description: {desc}"]
    if when_to_use:
        lines.append(f"when_to_use: {_one_line(when_to_use)}")
    lines.append("---")
    lines.append("")

    lines.append(f"# {name}")
    lines.append("")
    lines.append(f"> Auto-generated skill file for `{name}` v{version}")
    lines.append(f"> Re-generate with: `{name} skill` or `acli skill --bin {name}`")
    lines.append("")

    lines.append("## Available commands")
    lines.append("")
    for cmd in user_commands:
        idem = cmd.get("idempotent")
        idem_tag = ""
        if idem is True:
            idem_tag = " (idempotent)"
        elif idem == "conditional":
            idem_tag = " (conditionally idempotent)"
        lines.append(f"- `{name} {cmd['name']}` — {cmd.get('description', '')}{idem_tag}")
    lines.append("")

    for cmd in user_commands:
        _render_command(lines, name, cmd)

    lines.append("## Output format")
    lines.append("")
    lines.append(_OUTPUT_SECTION)
    lines.append("")
    lines.append("```json")
    lines.append(_JSON_EXAMPLE)
    lines.append("```")
    lines.append("")
    lines.append(_ERROR_SECTION)
    lines.append("")

    lines.append("## Exit codes")
    lines.append("")
    lines.append("| Code | Meaning | Action |")
    lines.append("|------|---------|--------|")
    lines.append("| 0 | Success | Proceed |")
    lines.append("| 2 | Invalid arguments | Correct and retry |")
    lines.append("| 3 | Not found | Check inputs |")
    lines.append("| 5 | Conflict | Resolve conflict |")
    lines.append("| 8 | Precondition failed | Fix precondition |")
    lines.append("| 9 | Dry-run completed | Review and confirm |")
    lines.append("")

    lines.append("## Further discovery")
    lines.append("")
    lines.append(f"- `{name} --help` — full help for any command")
    lines.append(f"- `{name} introspect` — machine-readable command tree (JSON)")
    lines.append("- `.cli/README.md` — persistent reference (survives context resets)")
    lines.append("")

    content = "\n".join(lines)

    if target_path is not None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)

    return content


def _render_command(lines: list[str], tool_name: str, cmd: dict[str, Any]) -> None:
    """Render a single command's detailed section (unchanged behaviour)."""
    lines.append(f"## `{tool_name} {cmd['name']}`")
    lines.append("")
    if desc := cmd.get("description", ""):
        lines.append(desc)
        lines.append("")

    options = cmd.get("options", [])
    if options:
        lines.append("### Options")
        lines.append("")
        for opt in options:
            opt_name = opt["name"].replace("_", "-")
            opt_type = opt.get("type", "")
            opt_desc = opt.get("description", "")
            default = opt.get("default")
            default_str = f" [default: {default}]" if default is not None else ""
            lines.append(f"- `--{opt_name}` ({opt_type}) — {opt_desc}{default_str}")
        lines.append("")

    arguments = cmd.get("arguments", [])
    if arguments:
        lines.append("### Arguments")
        lines.append("")
        for arg in arguments:
            req = "required" if arg.get("required") else "optional"
            arg_type = arg.get("type", "")
            arg_desc = arg.get("description", "")
            lines.append(f"- `{arg['name']}` ({arg_type}, {req}) — {arg_desc}")
        lines.append("")

    examples = cmd.get("examples", [])
    if examples:
        lines.append("### Examples")
        lines.append("")
        for ex in examples:
            lines.append("```bash")
            lines.append(f"# {ex['description']}")
            lines.append(ex["invocation"])
            lines.append("```")
            lines.append("")

    see_also = cmd.get("see_also", [])
    if see_also:
        refs = ", ".join(f"`{tool_name} {s}`" for s in see_also)
        lines.append(f"**See also:** {refs}")
        lines.append("")
```

- [ ] **Step 4: Update existing tests that hardcoded `SKILLS.md`**

In `sdks/python/tests/test_skill.py`:
- Change `target = tmp_path / "SKILLS.md"` → `target = tmp_path / "SKILL.md"` (both places).

- [ ] **Step 5: Run full test suite**

Run: `cd sdks/python && pytest -v`
Expected: ALL tests pass. If `test_app.py` or `test_cli.py` reference `SKILLS.md`, update them to `SKILL.md` in place.

- [ ] **Step 6: Update `_register_skill` in `app.py`**

In `sdks/python/src/acli/app.py`:
- Line 142 docstring: change `Generate a SKILLS.md file for agent bootstrapping.` → `Generate a SKILL.md (agentskills.io) file for agent bootstrapping.`
- Extend `ACLIApp.__init__` to accept `skill_description: str | None = None` and `skill_when_to_use: str | None = None`; store as instance attributes.
- Thread those into `generate_skill(...)` inside `_register_skill`.

Exact edits:

```python
def __init__(
    self,
    name: str,
    version: str,
    *,
    cli_dir: Path | None = None,
    skill_description: str | None = None,
    skill_when_to_use: str | None = None,
    **typer_kwargs: Any,
) -> None:
    self.name = name
    self.version = version
    self.cli_dir = cli_dir
    self.skill_description = skill_description
    self.skill_when_to_use = skill_when_to_use
    self._typer = typer.Typer(name=name, help=typer_kwargs.pop("help", None), **typer_kwargs)
    self._register_introspect()
    self._register_version()
    self._register_skill()
```

In `_register_skill`, change the `generate_skill` call to:

```python
content = generate_skill(
    tree,
    target_path=target,
    description=self.skill_description,
    when_to_use=self.skill_when_to_use,
)
```

And update the docstring line.

- [ ] **Step 7: Update `cli.py` meta-command description**

In `sdks/python/src/acli/cli.py`, grep for `SKILLS.md` and replace with `SKILL.md`. If there's a help string for `acli skill`, update it to mention "agentskills.io compatible SKILL.md".

- [ ] **Step 8: Re-run lint + types + tests**

Run:
```bash
cd sdks/python
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
pytest
```
Expected: all green. Fix lint/format issues if any.

- [ ] **Step 9: Commit**

```bash
git add sdks/python/src/acli/skill.py sdks/python/src/acli/app.py sdks/python/src/acli/cli.py sdks/python/tests/
git commit -m "feat(python): emit SKILL.md with agentskills.io frontmatter"
```

---

## Task 3: TypeScript SDK

**Files:**
- Modify: `sdks/typescript/src/skill.ts`
- Modify: `sdks/typescript/src/app.ts`
- Modify: `sdks/typescript/tests/sdk.test.ts`

- [ ] **Step 1: Add failing frontmatter tests**

Append to `sdks/typescript/tests/sdk.test.ts` (in the skill-related describe block — create one if absent):

```ts
it('emits default frontmatter', () => {
  const content = generateSkill(sampleTree);
  expect(content.startsWith('---\n')).toBe(true);
  const lines = content.split('\n');
  expect(lines[1]).toBe('name: noether');
  expect(lines[2]).toMatch(/^description: .+/);
  const closing = lines.indexOf('---', 1);
  expect(lines.slice(0, closing + 1).every(l => !l.startsWith('when_to_use:'))).toBe(true);
});

it('emits explicit frontmatter', () => {
  const content = generateSkill(sampleTree, undefined, {
    description: 'Run Noether pipelines.',
    whenToUse: 'Use when deploying.',
  });
  expect(content).toContain('description: Run Noether pipelines.');
  expect(content).toContain('when_to_use: Use when deploying.');
});

it('strips newlines from frontmatter values', () => {
  const content = generateSkill(sampleTree, undefined, { description: 'A\nB' });
  expect(content).toContain('description: A B');
});
```

(Rename existing `SKILLS.md` fixture path to `SKILL.md` while you're in this file.)

- [ ] **Step 2: Run tests to verify failures**

Run: `cd sdks/typescript && npm test` (or `pnpm test` / `yarn test` — match repo convention; inspect `package.json` scripts first).
Expected: new tests FAIL.

- [ ] **Step 3: Extend `generateSkill` signature**

Replace the current signature and prepend frontmatter. New signature:

```ts
export interface SkillOptions {
  description?: string;
  whenToUse?: string;
}

export function generateSkill(
  tree: CommandTree,
  targetPath?: string,
  options: SkillOptions = {},
): string {
  const { name, version, commands } = tree;
  const userCommands = commands.filter(c => !BUILTIN_COMMANDS.has(c.name));

  const oneLine = (v: string) => v.split(/\s+/).filter(Boolean).join(' ');
  const shown = userCommands.slice(0, 4).map(c => c.name);
  const defaultDesc = userCommands.length
    ? `Invoke the \`${name}\` CLI. Commands: ${shown.join(', ')}${userCommands.length > 4 ? '…' : ''}`
    : `Invoke the \`${name}\` CLI.`;
  const description = options.description ? oneLine(options.description) : defaultDesc;

  const lines: string[] = ['---', `name: ${name}`, `description: ${description}`];
  if (options.whenToUse) lines.push(`when_to_use: ${oneLine(options.whenToUse)}`);
  lines.push('---', '');

  lines.push(`# ${name}`, '');
  // …rest of existing body unchanged…
}
```

Leave the rest of the body generation as-is.

- [ ] **Step 4: Update `app.ts` to thread the options through**

If `registerSkill` / `ACLIApp` constructor exposes skill generation, add optional `skillDescription` / `skillWhenToUse` constructor fields and pass them. Match the Python SDK surface names where possible — TS uses camelCase (`skillDescription`).

- [ ] **Step 5: Run tests + lint**

Run:
```bash
cd sdks/typescript
npm test
npm run lint  # or whatever the script is
```
Expected: green.

- [ ] **Step 6: Commit**

```bash
git add sdks/typescript/
git commit -m "feat(typescript): emit SKILL.md with agentskills.io frontmatter"
```

---

## Task 4: Rust SDK

**Files:**
- Modify: `sdks/rust/src/skill.rs`
- Modify: `sdks/rust/tests/integration_test.rs`

- [ ] **Step 1: Add failing frontmatter test**

Append to `sdks/rust/tests/integration_test.rs`:

```rust
#[test]
fn skill_emits_default_frontmatter() {
    let tree = sample_tree(); // reuse helper; create if needed
    let content = acli::skill::generate_skill(&tree, None).unwrap();
    assert!(content.starts_with("---\n"));
    let lines: Vec<&str> = content.lines().collect();
    assert_eq!(lines[1], "name: noether");
    assert!(lines[2].starts_with("description: "));
    let closing = lines.iter().skip(1).position(|l| *l == "---").unwrap() + 1;
    assert!(lines[..=closing].iter().all(|l| !l.starts_with("when_to_use:")));
}

#[test]
fn skill_emits_explicit_frontmatter() {
    let tree = sample_tree();
    let opts = acli::skill::SkillOptions {
        description: Some("Run Noether pipelines.".into()),
        when_to_use: Some("Use when deploying.".into()),
    };
    let content = acli::skill::generate_skill_with(&tree, None, &opts).unwrap();
    assert!(content.contains("description: Run Noether pipelines."));
    assert!(content.contains("when_to_use: Use when deploying."));
}
```

Update any existing `"SKILLS.md"` fixture path to `"SKILL.md"`.

- [ ] **Step 2: Run tests to verify failures**

Run: `cd sdks/rust && cargo test`
Expected: new tests FAIL (missing symbols).

- [ ] **Step 3: Extend `generate_skill` API**

Add a struct `SkillOptions` and a `generate_skill_with` variant so the old `generate_skill(tree, path)` keeps its signature (callers already in the SDK don't need changes), while new callers get the richer API. Prepend frontmatter inside a shared helper.

```rust
#[derive(Default, Clone, Debug)]
pub struct SkillOptions {
    pub description: Option<String>,
    pub when_to_use: Option<String>,
}

pub fn generate_skill(tree: &CommandTree, target_path: Option<&Path>) -> std::io::Result<String> {
    generate_skill_with(tree, target_path, &SkillOptions::default())
}

pub fn generate_skill_with(
    tree: &CommandTree,
    target_path: Option<&Path>,
    opts: &SkillOptions,
) -> std::io::Result<String> {
    // build frontmatter first, then body (existing code)
}
```

Inside `generate_skill_with`, compute the default description identically to Python (first 4 user commands, `…` if more), collapse whitespace on user-supplied values, then push:

```rust
let mut lines = Vec::new();
lines.push("---".to_string());
lines.push(format!("name: {name}"));
lines.push(format!("description: {description}"));
if let Some(w) = &opts.when_to_use {
    lines.push(format!("when_to_use: {}", collapse_ws(w)));
}
lines.push("---".to_string());
lines.push(String::new());
// …existing body…
```

Helper `fn collapse_ws(s: &str) -> String { s.split_whitespace().collect::<Vec<_>>().join(" ") }`.

- [ ] **Step 4: Run tests + clippy**

Run:
```bash
cd sdks/rust
cargo test
cargo clippy -- -D warnings
cargo fmt --check
```

- [ ] **Step 5: Commit**

```bash
git add sdks/rust/
git commit -m "feat(rust): emit SKILL.md with agentskills.io frontmatter"
```

---

## Task 5: Go SDK

**Files:**
- Modify: `sdks/go/skill.go`
- Modify: `sdks/go/app.go`
- Modify: tests under `sdks/go/`

- [ ] **Step 1: Add failing frontmatter test**

Append to `sdks/go/acli_test.go` (or create `skill_test.go`):

```go
func TestSkillEmitsDefaultFrontmatter(t *testing.T) {
    tree := sampleTree()
    content, err := acli.GenerateSkill(tree, "")
    if err != nil { t.Fatal(err) }
    if !strings.HasPrefix(content, "---\n") {
        t.Fatalf("no frontmatter: %q", content[:40])
    }
    lines := strings.Split(content, "\n")
    if lines[1] != "name: noether" { t.Errorf("got %q", lines[1]) }
    if !strings.HasPrefix(lines[2], "description: ") { t.Errorf("got %q", lines[2]) }
}

func TestSkillEmitsExplicitFrontmatter(t *testing.T) {
    tree := sampleTree()
    content, err := acli.GenerateSkillWith(tree, "", acli.SkillOptions{
        Description: "Run Noether pipelines.",
        WhenToUse:   "Use when deploying.",
    })
    if err != nil { t.Fatal(err) }
    if !strings.Contains(content, "description: Run Noether pipelines.") {
        t.Errorf("missing description")
    }
    if !strings.Contains(content, "when_to_use: Use when deploying.") {
        t.Errorf("missing when_to_use")
    }
}
```

- [ ] **Step 2: Run tests to verify failures**

Run: `cd sdks/go && go test ./...`
Expected: new tests FAIL (missing symbols).

- [ ] **Step 3: Extend API in `skill.go`**

Add:
```go
type SkillOptions struct {
    Description string
    WhenToUse   string
}

func GenerateSkill(tree *CommandTree, targetPath string) (string, error) {
    return GenerateSkillWith(tree, targetPath, SkillOptions{})
}

func GenerateSkillWith(tree *CommandTree, targetPath string, opts SkillOptions) (string, error) {
    // frontmatter + existing body
}
```

Compute default description, collapse whitespace on user-supplied values, prepend `---\nname: ...\ndescription: ...\n[when_to_use: ...\n]---\n\n`.

- [ ] **Step 4: Update `app.go` `HandleSkill`**

If it calls `GenerateSkill` directly, either leave it (backward-compatible) or plumb through options from an `AcliApp` struct field. Prefer threading options to keep parity with Python/TS. Add fields `SkillDescription string` and `SkillWhenToUse string` to the app struct.

- [ ] **Step 5: Run tests + vet**

Run:
```bash
cd sdks/go
go test ./...
go vet ./...
gofmt -l .   # must output nothing
```

- [ ] **Step 6: Commit**

```bash
git add sdks/go/
git commit -m "feat(go): emit SKILL.md with agentskills.io frontmatter"
```

---

## Task 6: Java SDK

**Files:**
- Modify: `sdks/java/src/main/java/dev/acli/Skill.java`
- Modify: `sdks/java/src/main/java/dev/acli/AcliApp.java`
- Modify: `sdks/java/src/main/java/dev/acli/picocli/BuiltInCommands.java` (if referenced)
- Modify: `sdks/java/src/test/java/dev/acli/SdkTest.java`

- [ ] **Step 1: Add failing frontmatter test in `SdkTest.java`**

```java
@Test
void skillEmitsDefaultFrontmatter() throws Exception {
    CommandTree tree = sampleTree();
    String content = Skill.generateSkill(tree);
    assertTrue(content.startsWith("---\n"), "expected frontmatter");
    String[] lines = content.split("\n");
    assertEquals("name: noether", lines[1]);
    assertTrue(lines[2].startsWith("description: "));
}

@Test
void skillEmitsExplicitFrontmatter() throws Exception {
    CommandTree tree = sampleTree();
    Skill.Options opts = new Skill.Options("Run Noether pipelines.", "Use when deploying.");
    String content = Skill.generateSkill(tree, null, opts);
    assertTrue(content.contains("description: Run Noether pipelines."));
    assertTrue(content.contains("when_to_use: Use when deploying."));
}
```

- [ ] **Step 2: Run tests**

Run: `cd sdks/java && mvn -q test`
Expected: new tests FAIL.

- [ ] **Step 3: Extend `Skill.java` with an `Options` record**

```java
public record Options(String description, String whenToUse) {
    public static Options empty() { return new Options(null, null); }
}

public static String generateSkill(CommandTree tree) { /* calls (tree, null, Options.empty()) */ }
public static String generateSkill(CommandTree tree, Path targetPath) throws IOException {
    return generateSkill(tree, targetPath, Options.empty());
}
public static String generateSkill(CommandTree tree, Path targetPath, Options opts) throws IOException {
    // frontmatter + existing body
}
```

Use the same default-description rule and whitespace collapse.

- [ ] **Step 4: Thread options into `AcliApp.handleSkill`**

Add `skillDescription` and `skillWhenToUse` fields with builder-style setters on `AcliApp`. Pass them when calling `Skill.generateSkill`.

- [ ] **Step 5: Run tests**

Run: `mvn -q test`

- [ ] **Step 6: Commit**

```bash
git add sdks/java/
git commit -m "feat(java): emit SKILL.md with agentskills.io frontmatter"
```

---

## Task 7: .NET SDK

**Files:**
- Modify: `sdks/dotnet/Acli.Spec/Skill.cs`
- Modify: `sdks/dotnet/Acli.Spec/AcliApp.cs`
- Modify: any `Acli.Spec.Tests/` test files (create `SkillTests.cs` if needed)

- [ ] **Step 1: Add failing tests**

Create / extend `sdks/dotnet/Acli.Spec.Tests/SkillTests.cs`:

```csharp
[Fact]
public void EmitsDefaultFrontmatter()
{
    var tree = SampleTree();
    var content = Skill.Generate(tree, null);
    Assert.StartsWith("---\n", content);
    var lines = content.Split('\n');
    Assert.Equal("name: noether", lines[1]);
    Assert.StartsWith("description: ", lines[2]);
}

[Fact]
public void EmitsExplicitFrontmatter()
{
    var tree = SampleTree();
    var opts = new SkillOptions { Description = "Run Noether pipelines.", WhenToUse = "Use when deploying." };
    var content = Skill.Generate(tree, null, opts);
    Assert.Contains("description: Run Noether pipelines.", content);
    Assert.Contains("when_to_use: Use when deploying.", content);
}
```

- [ ] **Step 2: Run tests**

Run: `cd sdks/dotnet && dotnet test`
Expected: new tests FAIL.

- [ ] **Step 3: Extend `Skill.cs`**

```csharp
public record SkillOptions
{
    public string? Description { get; init; }
    public string? WhenToUse { get; init; }
}

public static string Generate(CommandTree tree, string? path)
    => Generate(tree, path, new SkillOptions());

public static string Generate(CommandTree tree, string? path, SkillOptions opts)
{
    // frontmatter + existing body
}
```

- [ ] **Step 4: Thread options through `AcliApp.cs`**

Add `SkillDescription` and `SkillWhenToUse` public properties; pass them in the skill command handler.

- [ ] **Step 5: Run tests**

Run: `dotnet test`

- [ ] **Step 6: Commit**

```bash
git add sdks/dotnet/
git commit -m "feat(dotnet): emit SKILL.md with agentskills.io frontmatter"
```

---

## Task 8: R SDK

**Files:**
- Modify: `sdks/r/R/acli.R`
- Modify: `sdks/r/tests/testthat/test-acli.R`

- [ ] **Step 1: Add failing test**

Append to `sdks/r/tests/testthat/test-acli.R`:

```r
test_that("skill emits default frontmatter", {
  content <- acli_skill_generate(sample_tree())
  expect_true(startsWith(content, "---\n"))
  lines <- strsplit(content, "\n", fixed = TRUE)[[1]]
  expect_equal(lines[2], "name: noether")
  expect_true(startsWith(lines[3], "description: "))
})

test_that("skill emits explicit frontmatter", {
  content <- acli_skill_generate(
    sample_tree(),
    description = "Run Noether pipelines.",
    when_to_use = "Use when deploying."
  )
  expect_true(grepl("description: Run Noether pipelines.", content, fixed = TRUE))
  expect_true(grepl("when_to_use: Use when deploying.", content, fixed = TRUE))
})
```

- [ ] **Step 2: Run tests**

Run: `cd sdks/r && Rscript -e 'devtools::test()'`
Expected: new tests FAIL.

- [ ] **Step 3: Extend `acli_skill_generate`**

Change signature:
```r
acli_skill_generate <- function(tree, path = NULL, description = NULL, when_to_use = NULL) {
  # compute default desc from tree$commands
  # collapse whitespace on user-supplied values
  # build frontmatter lines, then existing body
}
```

- [ ] **Step 4: Run tests + lint**

Run:
```bash
Rscript -e 'devtools::test()'
Rscript -e 'lintr::lint_package()'
```

- [ ] **Step 5: Commit**

```bash
git add sdks/r/
git commit -m "feat(r): emit SKILL.md with agentskills.io frontmatter"
```

---

## Task 9: Docs update

**Files:**
- Modify: `docs/tutorial/index.md`
- Modify: `docs/python-sdk/skill.md`
- Modify: `docs/spec/evolution.md`
- Modify: `docs/example.md`
- Modify: `docs/sdks/index.md`
- Modify: `docs/index.md`
- Modify: `README.md`
- Modify: `examples/citecheck-tutorial/README.md`

- [ ] **Step 1: Grep for all `SKILLS.md` references**

Run: `Grep -n "SKILLS\.md" docs/ examples/ README.md`

- [ ] **Step 2: Replace each reference**

For each match: replace `SKILLS.md` with `SKILL.md`. For any shell example like `citecheck skill > SKILLS.md`, rewrite to `citecheck skill --out SKILL.md` (the SDK now accepts `--out` to write; stdout is the default).

- [ ] **Step 3: Add an "agentskills.io compatibility" callout**

In `docs/python-sdk/skill.md` (and equivalent SDK docs if any), add a short note at the top:

```markdown
> The generated `SKILL.md` conforms to the [agentskills.io](https://agentskills.io) open standard and drops into `.claude/skills/<tool>/SKILL.md`, `.cursor/skills/<tool>/SKILL.md`, Gemini CLI, Codex, etc. without modification.
```

- [ ] **Step 4: Commit**

```bash
git add docs/ README.md examples/citecheck-tutorial/README.md
git commit -m "docs: update SKILLS.md → SKILL.md + agentskills.io note"
```

---

## Task 10: Regenerate examples

**Files:**
- Delete: `examples/weather/SKILLS.md` (if present)
- Regenerate: `examples/weather/.cli/*`, `examples/weather/SKILL.md`
- Modify: `examples/weather-java/`, `examples/weather-rust/`, `examples/weather-ts/` — rename any committed `SKILLS.md` to `SKILL.md` and regenerate content using the new SDK.

- [ ] **Step 1: Run the Python weather example to regenerate**

```bash
cd examples/weather
python3 weather.py skill --out SKILL.md
python3 weather.py introspect > /dev/null  # refreshes .cli/ if needed
```

- [ ] **Step 2: Remove stale `SKILLS.md` files**

```bash
find examples -name "SKILLS.md" -print
find examples -name "SKILLS.md" -delete
```

- [ ] **Step 3: Regenerate other language examples**

For each of `weather-java`, `weather-rust`, `weather-ts`: run the example's skill command (or a small driver) and confirm a `SKILL.md` is produced with frontmatter.

- [ ] **Step 4: Check `.cli/commands.json` and `.cli/README.md`**

If they contain the string `SKILLS.md`, let the generator overwrite them (the Python `cli_folder.py` will regenerate on the next introspect run). Verify.

- [ ] **Step 5: Commit**

```bash
git add examples/
git commit -m "examples: regenerate SKILL.md (agentskills.io) across weather+citecheck"
```

---

## Task 11: CHANGELOG + final validation

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add breaking-change entry**

Prepend to the "Unreleased" section of `CHANGELOG.md`:

```markdown
### Changed (breaking)
- `skill` subcommand now emits `SKILL.md` (singular) with YAML frontmatter conforming to the [agentskills.io](https://agentskills.io) open standard. The previous `SKILLS.md` filename is no longer produced. Generated files drop directly into `.claude/skills/<tool>/SKILL.md`, `.cursor/skills/<tool>/SKILL.md`, Gemini CLI, Codex, and other agentskills-compatible tools.
- All SDKs gained `description` / `when_to_use` parameters on their skill generator (names vary by language convention).
```

- [ ] **Step 2: Run every SDK's test suite one last time**

```bash
(cd sdks/python && pytest -q)
(cd sdks/typescript && npm test --silent)
(cd sdks/rust && cargo test -q)
(cd sdks/go && go test ./...)
(cd sdks/java && mvn -q test)
(cd sdks/dotnet && dotnet test --nologo --verbosity quiet)
(cd sdks/r && Rscript -e 'devtools::test()')
```
Expected: all green.

- [ ] **Step 3: Confirm no stale `SKILLS.md` remain**

Run: `Grep "SKILLS\.md" .`
Expected: zero hits outside this plan document and any historical CHANGELOG entry.

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "chore: changelog entry for SKILL.md agentskills migration"
```

---

## Self-Review Notes

- **Spec coverage:** Task 1 locks the contract; Tasks 2–8 implement it per SDK; Tasks 9–11 propagate to docs/examples/changelog. No requirement left behind.
- **No placeholders:** Every code block is directly pasteable. Test code shows exact assertions; implementation code shows full helpers.
- **Type consistency:** Option-container names vary intentionally per language idiom (`SkillOptions` struct in Rust/Go/.NET, `Skill.Options` record in Java, dataclass-free kwargs in Python, named args in R, object arg in TS). Field names are consistent: `description` / `when_to_use` in snake_case languages, `description` / `whenToUse` in camelCase.
- **Commit cadence:** One commit per SDK plus one each for spec, docs, examples, changelog — 11 commits total. Each is independently revertable.
