//! Generate SKILLS.md files from ACLI command trees.

use crate::introspect::CommandTree;
use std::fs;
use std::path::Path;

const BUILTIN_COMMANDS: &[&str] = &["introspect", "version", "skill"];

/// Generate a SKILLS.md file from an ACLI command tree.
pub fn generate_skill(tree: &CommandTree, target_path: Option<&Path>) -> std::io::Result<String> {
    let name = &tree.name;
    let version = &tree.version;
    let mut lines = Vec::new();

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

    let user_commands: Vec<_> = tree
        .commands
        .iter()
        .filter(|c| !BUILTIN_COMMANDS.contains(&c.name.as_str()))
        .collect();

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
