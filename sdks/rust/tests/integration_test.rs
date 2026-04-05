use acli::cli_folder::{generate_cli_folder, needs_update};
use acli::errors::{invalid_args, not_found, suggest_flag, AcliError};
use acli::exit_codes::ExitCode;
use acli::introspect::{CommandInfo, CommandTree};
use acli::output::{error_envelope, error_envelope_raw, success_envelope, OutputFormat};
use acli::skill::generate_skill;
use serde_json::json;
use std::time::Instant;
use tempfile::TempDir;

// ── Exit Codes ───────────────────────────────────────────────────────────────

#[test]
fn test_exit_code_values() {
    assert_eq!(ExitCode::Success.code(), 0);
    assert_eq!(ExitCode::GeneralError.code(), 1);
    assert_eq!(ExitCode::InvalidArgs.code(), 2);
    assert_eq!(ExitCode::NotFound.code(), 3);
    assert_eq!(ExitCode::PermissionDenied.code(), 4);
    assert_eq!(ExitCode::Conflict.code(), 5);
    assert_eq!(ExitCode::Timeout.code(), 6);
    assert_eq!(ExitCode::UpstreamError.code(), 7);
    assert_eq!(ExitCode::PreconditionFailed.code(), 8);
    assert_eq!(ExitCode::DryRun.code(), 9);
}

#[test]
fn test_exit_code_names() {
    assert_eq!(ExitCode::Success.name(), "SUCCESS");
    assert_eq!(ExitCode::InvalidArgs.name(), "INVALID_ARGS");
    assert_eq!(ExitCode::DryRun.name(), "DRY_RUN");
}

// ── Output / Envelopes ───────────────────────────────────────────────────────

#[test]
fn test_output_format_parse() {
    assert_eq!("json".parse::<OutputFormat>().unwrap(), OutputFormat::Json);
    assert_eq!("text".parse::<OutputFormat>().unwrap(), OutputFormat::Text);
    assert_eq!(
        "table".parse::<OutputFormat>().unwrap(),
        OutputFormat::Table
    );
    assert!("invalid".parse::<OutputFormat>().is_err());
}

#[test]
fn test_output_format_display() {
    assert_eq!(OutputFormat::Json.to_string(), "json");
    assert_eq!(OutputFormat::Text.to_string(), "text");
    assert_eq!(OutputFormat::Table.to_string(), "table");
}

#[test]
fn test_success_envelope() {
    let env = success_envelope("run", json!({"result": 42}), "1.0.0", None);
    assert!(env.ok);
    assert_eq!(env.command, "run");
    assert_eq!(env.data.unwrap()["result"], 42);
    assert_eq!(env.meta.version, "1.0.0");
    assert!(env.error.is_none());
}

#[test]
fn test_success_envelope_with_timing() {
    let start = Instant::now();
    std::thread::sleep(std::time::Duration::from_millis(10));
    let env = success_envelope("run", json!({}), "1.0.0", Some(start));
    assert!(env.meta.duration_ms >= 10);
}

#[test]
fn test_error_envelope() {
    let env = error_envelope(
        "run",
        ExitCode::InvalidArgs,
        "Missing --pipeline",
        Some("Run `noether run --help`"),
        Some(".cli/examples/run.sh"),
        "1.0.0",
        None,
    );
    assert!(!env.ok);
    assert_eq!(env.command, "run");
    let err = env.error.unwrap();
    assert_eq!(err.code, "INVALID_ARGS");
    assert_eq!(err.message, "Missing --pipeline");
    assert_eq!(err.hint.unwrap(), "Run `noether run --help`");
    assert_eq!(err.docs.unwrap(), ".cli/examples/run.sh");
}

#[test]
fn test_error_envelope_no_hint() {
    let env = error_envelope("run", ExitCode::NotFound, "gone", None, None, "1.0.0", None);
    let err = env.error.unwrap();
    assert!(err.hint.is_none());
    assert!(err.docs.is_none());
}

// ── Errors ───────────────────────────────────────────────────────────────────

#[test]
fn test_acli_error_builder() {
    let err = AcliError::new("something broke")
        .with_hint("try this")
        .with_docs("readme.md")
        .with_command("deploy");
    assert_eq!(err.message, "something broke");
    assert_eq!(err.code, ExitCode::GeneralError);
    assert_eq!(err.hint.unwrap(), "try this");
    assert_eq!(err.docs.unwrap(), "readme.md");
    assert_eq!(err.command.unwrap(), "deploy");
}

#[test]
fn test_error_constructors() {
    assert_eq!(invalid_args("bad").code, ExitCode::InvalidArgs);
    assert_eq!(not_found("gone").code, ExitCode::NotFound);
    assert_eq!(acli::errors::conflict("locked").code, ExitCode::Conflict);
    assert_eq!(
        acli::errors::precondition_failed("setup needed").code,
        ExitCode::PreconditionFailed
    );
}

#[test]
fn test_error_display() {
    let err = invalid_args("Missing --file");
    assert_eq!(format!("{err}"), "Missing --file");
}

#[test]
fn test_suggest_flag() {
    let known = vec!["--pipeline", "--env", "--dry-run"];
    assert_eq!(suggest_flag("--pipline", &known), Some("--pipeline"));
    assert_eq!(suggest_flag("--zzzzz", &known), None);
    assert_eq!(suggest_flag("--env", &known), Some("--env"));
}

// ── Introspect ───────────────────────────────────────────────────────────────

#[test]
fn test_command_tree_builder() {
    let mut tree = CommandTree::new("noether", "1.0.0");
    tree.add_command(
        CommandInfo::new("run", "Execute a pipeline")
            .idempotent(false)
            .with_examples(vec![
                ("Run basic", "noether run --file x.yaml"),
                ("Dry run", "noether run --file x.yaml --dry-run"),
            ])
            .with_see_also(vec!["status"])
            .add_option("file", "path", "Pipeline file", None)
            .add_option("env", "string", "Environment", Some(json!("dev"))),
    );

    assert_eq!(tree.name, "noether");
    assert_eq!(tree.version, "1.0.0");
    assert_eq!(tree.acli_version, "0.1.0");
    assert_eq!(tree.commands.len(), 1);

    let cmd = &tree.commands[0];
    assert_eq!(cmd.name, "run");
    assert_eq!(cmd.idempotent, Some(json!(false)));
    assert_eq!(cmd.examples.as_ref().unwrap().len(), 2);
    assert_eq!(cmd.see_also.as_ref().unwrap(), &vec!["status"]);
    assert_eq!(cmd.options.len(), 2);
    assert_eq!(cmd.options[1].default, Some(json!("dev")));
}

#[test]
fn test_command_with_arguments() {
    let cmd = CommandInfo::new("deploy", "Deploy to target").add_argument(
        "target",
        "string",
        "Deploy target",
        true,
    );
    assert_eq!(cmd.arguments.len(), 1);
    assert_eq!(cmd.arguments[0].required, Some(true));
}

#[test]
fn test_conditional_idempotent() {
    let cmd = CommandInfo::new("apply", "Apply config").conditionally_idempotent();
    assert_eq!(cmd.idempotent, Some(json!("conditional")));
}

#[test]
fn test_command_tree_serializes() {
    let mut tree = CommandTree::new("test", "0.1.0");
    tree.add_command(CommandInfo::new("hello", "Say hello").idempotent(true));
    let json = serde_json::to_string(&tree).unwrap();
    assert!(json.contains("\"name\":\"test\""));
    assert!(json.contains("\"acli_version\":\"0.1.0\""));
}

// ── CLI Folder ───────────────────────────────────────────────────────────────

fn sample_tree() -> CommandTree {
    let mut tree = CommandTree::new("noether", "1.0.0");
    tree.add_command(
        CommandInfo::new("run", "Run a pipeline")
            .idempotent(false)
            .with_examples(vec![
                ("Run basic", "noether run --file x.yaml"),
                ("Dry run", "noether run --file x.yaml --dry-run"),
            ]),
    );
    tree
}

#[test]
fn test_generate_cli_folder() {
    let dir = TempDir::new().unwrap();
    let tree = sample_tree();
    let cli_dir = generate_cli_folder(&tree, Some(dir.path())).unwrap();

    assert!(cli_dir.join("commands.json").exists());
    assert!(cli_dir.join("README.md").exists());
    assert!(cli_dir.join("changelog.md").exists());
    assert!(cli_dir.join("examples").is_dir());
    assert!(cli_dir.join("schemas").is_dir());
}

#[test]
fn test_commands_json_content() {
    let dir = TempDir::new().unwrap();
    let tree = sample_tree();
    let cli_dir = generate_cli_folder(&tree, Some(dir.path())).unwrap();

    let content = std::fs::read_to_string(cli_dir.join("commands.json")).unwrap();
    let parsed: serde_json::Value = serde_json::from_str(&content).unwrap();
    assert_eq!(parsed["name"], "noether");
    assert_eq!(parsed["version"], "1.0.0");
}

#[test]
fn test_readme_content() {
    let dir = TempDir::new().unwrap();
    let tree = sample_tree();
    let cli_dir = generate_cli_folder(&tree, Some(dir.path())).unwrap();

    let readme = std::fs::read_to_string(cli_dir.join("README.md")).unwrap();
    assert!(readme.contains("# noether"));
    assert!(readme.contains("Version: 1.0.0"));
    assert!(readme.contains("### run"));
}

#[test]
fn test_example_scripts() {
    let dir = TempDir::new().unwrap();
    let tree = sample_tree();
    let cli_dir = generate_cli_folder(&tree, Some(dir.path())).unwrap();

    let script = cli_dir.join("examples").join("run.sh");
    assert!(script.exists());
    let content = std::fs::read_to_string(script).unwrap();
    assert!(content.contains("noether run --file x.yaml"));
}

#[test]
fn test_changelog_not_overwritten() {
    let dir = TempDir::new().unwrap();
    let tree = sample_tree();
    let cli_dir = generate_cli_folder(&tree, Some(dir.path())).unwrap();

    std::fs::write(cli_dir.join("changelog.md"), "# Custom").unwrap();
    generate_cli_folder(&tree, Some(dir.path())).unwrap();
    let content = std::fs::read_to_string(cli_dir.join("changelog.md")).unwrap();
    assert_eq!(content, "# Custom");
}

#[test]
fn test_needs_update() {
    let dir = TempDir::new().unwrap();
    let tree = sample_tree();

    assert!(needs_update(&tree, Some(dir.path())));
    generate_cli_folder(&tree, Some(dir.path())).unwrap();
    assert!(!needs_update(&tree, Some(dir.path())));
}

// ── Skill ────────────────────────────────────────────────────────────────────

#[test]
fn test_generate_skill() {
    let tree = sample_tree();
    let content = generate_skill(&tree, None).unwrap();

    assert!(content.contains("# noether"));
    assert!(content.contains("v1.0.0"));
    assert!(content.contains("## Available commands"));
    assert!(content.contains("`noether run`"));
    assert!(content.contains("## Exit codes"));
    assert!(content.contains("## Further discovery"));
}

#[test]
fn test_skill_write_to_file() {
    let dir = TempDir::new().unwrap();
    let tree = sample_tree();
    let path = dir.path().join("SKILLS.md");
    let content = generate_skill(&tree, Some(&path)).unwrap();

    assert!(path.exists());
    assert_eq!(std::fs::read_to_string(&path).unwrap(), content);
}

#[test]
fn test_skill_excludes_builtins() {
    let mut tree = sample_tree();
    tree.add_command(CommandInfo::new("introspect", "Introspect"));
    tree.add_command(CommandInfo::new("version", "Version"));

    let content = generate_skill(&tree, None).unwrap();
    let available = content
        .split("## Available commands")
        .nth(1)
        .unwrap()
        .split("##")
        .next()
        .unwrap();
    assert!(!available.contains("`noether introspect`"));
    assert!(!available.contains("`noether version`"));
    assert!(available.contains("`noether run`"));
}
