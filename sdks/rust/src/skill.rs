//! Generate SKILL.md files from ACLI command trees.
//!
//! Emits a file conforming to the agentskills.io open standard
//! (<https://agentskills.io>): YAML frontmatter (`name`, `description`,
//! optional `when_to_use`) followed by the ACLI command reference body.

use crate::introspect::CommandTree;
use std::fs;
use std::path::Path;

const BUILTIN_COMMANDS: &[&str] = &["introspect", "version", "skill"];

/// Options forwarded into the SKILL.md frontmatter.
#[derive(Default, Clone, Debug)]
pub struct SkillOptions {
    pub description: Option<String>,
    pub when_to_use: Option<String>,
}

fn collapse_ws(s: &str) -> String {
    s.split_whitespace().collect::<Vec<_>>().join(" ")
}

const YAML_RESERVED_START: &[char] = &[
    '!', '&', '*', '?', '|', '>', '\'', '"', '%', '@', '`', '#', ',', '[', ']', '{', '}', '-', ':',
];

/// Render a scalar safe for a single-line YAML block mapping value.
fn yaml_scalar(value: &str) -> String {
    if value.is_empty() {
        return "\"\"".to_string();
    }
    let first = value.chars().next().unwrap();
    let needs_quoting = value.contains(": ")
        || value.contains(" #")
        || YAML_RESERVED_START.contains(&first)
        || value.ends_with(':')
        || value.trim() != value;
    if !needs_quoting {
        return value.to_string();
    }
    let escaped = value.replace('\\', "\\\\").replace('"', "\\\"");
    format!("\"{escaped}\"")
}

fn default_description(name: &str, user_commands: &[&crate::introspect::CommandInfo]) -> String {
    if user_commands.is_empty() {
        return format!("Invoke the `{name}` CLI.");
    }
    let shown: Vec<&str> = user_commands.iter().take(4).map(|c| c.name.as_str()).collect();
    let suffix = if user_commands.len() > 4 { "…" } else { "" };
    format!(
        "Invoke the `{name}` CLI. Commands: {}{suffix}",
        shown.join(", ")
    )
}

/// Generate a SKILL.md file from an ACLI command tree (default options).
pub fn generate_skill(tree: &CommandTree, target_path: Option<&Path>) -> std::io::Result<String> {
    generate_skill_with(tree, target_path, &SkillOptions::default())
}

/// Generate a SKILL.md file with caller-supplied frontmatter options.
pub fn generate_skill_with(
    tree: &CommandTree,
    target_path: Option<&Path>,
    opts: &SkillOptions,
) -> std::io::Result<String> {
    let name = &tree.name;
    let version = &tree.version;
    let mut lines = Vec::new();

    let user_commands: Vec<_> = tree
        .commands
        .iter()
        .filter(|c| !BUILTIN_COMMANDS.contains(&c.name.as_str()))
        .collect();

    let description = opts
        .description
        .as_ref()
        .map(|d| collapse_ws(d))
        .unwrap_or_else(|| default_description(name, &user_commands));

    lines.push("---".to_string());
    lines.push(format!("name: {}", yaml_scalar(name)));
    lines.push(format!("description: {}", yaml_scalar(&description)));
    if let Some(w) = &opts.when_to_use {
        lines.push(format!("when_to_use: {}", yaml_scalar(&collapse_ws(w))));
    }
    lines.push("---".to_string());
    lines.push(String::new());

    lines.push(format!("# {name}"));
    lines.push(String::new());
    lines.push(format!(
        "> Auto-generated skill file for `{name}` v{version}"
    ));
    lines.push(format!(
        "> Re-generate with: `{name} skill` or `acli skill --bin {name}`"
    ));
    lines.push(String::new());

    // Quick reference
    lines.push("## Available commands".to_string());
    lines.push(String::new());

    for cmd in &user_commands {
        let idem_tag = match cmd.idempotent.as_ref().and_then(|v| v.as_bool()) {
            Some(true) => " (idempotent)",
            _ if cmd.idempotent.as_ref().and_then(|v| v.as_str()) == Some("conditional") => {
                " (conditionally idempotent)"
            }
            _ => "",
        };
        lines.push(format!(
            "- `{name} {}` — {}{idem_tag}",
            cmd.name, cmd.description
        ));
    }
    lines.push(String::new());

    // Detailed usage per command
    for cmd in &user_commands {
        lines.push(format!("## `{name} {}`", cmd.name));
        lines.push(String::new());
        if !cmd.description.is_empty() {
            lines.push(cmd.description.clone());
            lines.push(String::new());
        }

        if !cmd.options.is_empty() {
            lines.push("### Options".to_string());
            lines.push(String::new());
            for opt in &cmd.options {
                let default_str = opt
                    .default
                    .as_ref()
                    .map(|d| format!(" [default: {d}]"))
                    .unwrap_or_default();
                let opt_name = opt.name.replace('_', "-");
                lines.push(format!(
                    "- `--{opt_name}` ({}) — {}{default_str}",
                    opt.param_type, opt.description
                ));
            }
            lines.push(String::new());
        }

        if !cmd.arguments.is_empty() {
            lines.push("### Arguments".to_string());
            lines.push(String::new());
            for arg in &cmd.arguments {
                let req = if arg.required.unwrap_or(false) {
                    "required"
                } else {
                    "optional"
                };
                lines.push(format!(
                    "- `{}` ({}, {req}) — {}",
                    arg.name, arg.param_type, arg.description
                ));
            }
            lines.push(String::new());
        }

        if let Some(ref examples) = cmd.examples {
            if !examples.is_empty() {
                lines.push("### Examples".to_string());
                lines.push(String::new());
                for ex in examples {
                    lines.push("```bash".to_string());
                    lines.push(format!("# {}", ex.description));
                    lines.push(ex.invocation.clone());
                    lines.push("```".to_string());
                    lines.push(String::new());
                }
            }
        }

        if let Some(ref see_also) = cmd.see_also {
            if !see_also.is_empty() {
                let refs: Vec<String> = see_also.iter().map(|s| format!("`{name} {s}`")).collect();
                lines.push(format!("**See also:** {}", refs.join(", ")));
                lines.push(String::new());
            }
        }
    }

    // Output contracts
    lines.push("## Output format".to_string());
    lines.push(String::new());
    lines.push(
        "All commands support `--output json|text|table`. When using `--output json`, \
         responses follow a standard envelope:"
            .to_string(),
    );
    lines.push(String::new());
    lines.push("```json".to_string());
    lines.push(
        r#"{"ok": true, "command": "...", "data": {...}, "meta": {"duration_ms": ..., "version": "..."}}"#
            .to_string(),
    );
    lines.push("```".to_string());
    lines.push(String::new());

    // Exit codes
    lines.push("## Exit codes".to_string());
    lines.push(String::new());
    lines.push("| Code | Meaning | Action |".to_string());
    lines.push("|------|---------|--------|".to_string());
    lines.push("| 0 | Success | Proceed |".to_string());
    lines.push("| 2 | Invalid arguments | Correct and retry |".to_string());
    lines.push("| 3 | Not found | Check inputs |".to_string());
    lines.push("| 5 | Conflict | Resolve conflict |".to_string());
    lines.push("| 8 | Precondition failed | Fix precondition |".to_string());
    lines.push("| 9 | Dry-run completed | Review and confirm |".to_string());
    lines.push(String::new());

    // Discovery
    lines.push("## Further discovery".to_string());
    lines.push(String::new());
    lines.push(format!("- `{name} --help` — full help for any command"));
    lines.push(format!(
        "- `{name} introspect` — machine-readable command tree (JSON)"
    ));
    lines.push("- `.cli/README.md` — persistent reference (survives context resets)".to_string());
    lines.push(String::new());

    let content = lines.join("\n");

    if let Some(path) = target_path {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(path, &content)?;
    }

    Ok(content)
}
