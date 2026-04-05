//! Generate and maintain the .cli/ reference folder per ACLI spec §1.3.

use crate::introspect::CommandTree;
use std::fs;
use std::path::{Path, PathBuf};

/// Generate the .cli/ folder with all required files.
pub fn generate_cli_folder(
    tree: &CommandTree,
    target_dir: Option<&Path>,
) -> std::io::Result<PathBuf> {
    let root = target_dir
        .map(|p| p.join(".cli"))
        .unwrap_or_else(|| PathBuf::from(".cli"));

    fs::create_dir_all(root.join("examples"))?;
    fs::create_dir_all(root.join("schemas"))?;

    // commands.json
    let json = serde_json::to_string_pretty(tree).expect("Failed to serialize command tree");
    fs::write(root.join("commands.json"), format!("{json}\n"))?;

    // README.md
    write_readme(&root, tree)?;

    // Example scripts
    write_examples(&root, tree)?;

    // changelog.md (create if missing)
    let changelog = root.join("changelog.md");
    if !changelog.exists() {
        fs::write(
            changelog,
            format!("# Changelog\n\n## {}\n\n- Initial release\n", tree.version),
        )?;
    }

    Ok(root)
}

/// Check whether .cli/commands.json is out of date.
pub fn needs_update(tree: &CommandTree, target_dir: Option<&Path>) -> bool {
    let root = target_dir
        .map(|p| p.join(".cli"))
        .unwrap_or_else(|| PathBuf::from(".cli"));

    let commands_file = root.join("commands.json");
    if !commands_file.exists() {
        return true;
    }

    let Ok(content) = fs::read_to_string(&commands_file) else {
        return true;
    };
    let Ok(existing) = serde_json::from_str::<serde_json::Value>(&content) else {
        return true;
    };
    let current = serde_json::to_value(tree).unwrap_or_default();
    existing != current
}

fn write_readme(cli_dir: &Path, tree: &CommandTree) -> std::io::Result<()> {
    let mut lines = vec![
        format!("# {}", tree.name),
        String::new(),
        format!("Version: {}", tree.version),
        format!("ACLI version: {}", tree.acli_version),
        String::new(),
        "## Commands".to_string(),
        String::new(),
    ];

    for cmd in &tree.commands {
        lines.push(format!("### {}", cmd.name));
        lines.push(String::new());
        lines.push(cmd.description.clone());
        lines.push(String::new());
        if let Some(ref idem) = cmd.idempotent {
            lines.push(format!("Idempotent: {idem}"));
            lines.push(String::new());
        }
    }

    fs::write(cli_dir.join("README.md"), lines.join("\n") + "\n")
}

fn write_examples(cli_dir: &Path, tree: &CommandTree) -> std::io::Result<()> {
    for cmd in &tree.commands {
        if let Some(ref examples) = cmd.examples {
            if examples.is_empty() {
                continue;
            }
            let mut lines = vec![
                "#!/usr/bin/env bash".to_string(),
                format!("# Examples for: {}", cmd.name),
                String::new(),
            ];
            for ex in examples {
                lines.push(format!("# {}", ex.description));
                lines.push(ex.invocation.clone());
                lines.push(String::new());
            }
            fs::write(
                cli_dir.join("examples").join(format!("{}.sh", cmd.name)),
                lines.join("\n"),
            )?;
        }
    }
    Ok(())
}
