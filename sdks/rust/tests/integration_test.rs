use acli::acli_args;
use acli::app::AcliApp;
use acli::cli_folder::{generate_cli_folder, needs_update};
use acli::command::{examples, AcliCommand, CommandMeta, Idempotency};
use acli::errors::{invalid_args, not_found, suggest_flag, AcliError};
use acli::exit_codes::ExitCode;
use acli::introspect::{CommandInfo, CommandTree};
use acli::output::{error_envelope, success_envelope, CacheMeta, OutputFormat};
use acli::skill::{generate_skill, generate_skill_with, SkillOptions};
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
    let env = success_envelope("run", json!({"result": 42}), "1.0.0", None, None);
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
    let env = success_envelope("run", json!({}), "1.0.0", Some(start), None);
    assert!(env.meta.duration_ms >= 10);
}

#[test]
fn test_error_envelope() {
    let env = error_envelope(
        "run",
        ExitCode::InvalidArgs,
        "Missing --pipeline",
        Some("Run `noether run --help`"),
        None,
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
    let env = error_envelope(
        "run",
        ExitCode::NotFound,
        "gone",
        None,
        None,
        None,
        "1.0.0",
        None,
    );
    let err = env.error.unwrap();
    assert!(err.hint.is_none());
    assert!(err.hints.is_none());
    assert!(err.docs.is_none());
}

#[test]
fn test_error_envelope_hints() {
    let env = error_envelope(
        "run",
        ExitCode::NotFound,
        "gone",
        None,
        Some(vec!["Try X".into(), "Try Y".into()]),
        None,
        "1.0.0",
        None,
    );
    let err = env.error.unwrap();
    assert_eq!(err.hints.as_ref().unwrap().len(), 2);
}

#[test]
fn test_success_envelope_cache_meta() {
    let cache = CacheMeta {
        hit: true,
        key: Some("sha256:abc".into()),
        age_seconds: Some(3600),
    };
    let env = success_envelope(
        "run",
        json!({"x": 1}),
        "1.0.0",
        None,
        Some(cache.clone()),
    );
    assert_eq!(env.meta.cache, Some(cache));
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
fn test_option_since_version() {
    let cmd = CommandInfo::new("compose", "Compose").add_option_with_version(
        "force",
        "bool",
        "Bypass cache",
        None,
        Some("0.2.0"),
        None,
    );
    let opt = &cmd.options[0];
    assert_eq!(opt.since_version.as_deref(), Some("0.2.0"));
    assert!(opt.deprecated_since.is_none());
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
    let path = dir.path().join("SKILL.md");
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

#[test]
fn test_skill_default_frontmatter() {
    let content = generate_skill(&sample_tree(), None).unwrap();
    assert!(content.starts_with("---\n"));
    let lines: Vec<&str> = content.lines().collect();
    assert_eq!(lines[1], "name: noether");
    assert!(lines[2].starts_with("description: "));
    assert!(lines[2].contains("noether"));
    let closing = 1 + lines[1..].iter().position(|l| *l == "---").unwrap();
    for line in &lines[..=closing] {
        assert!(!line.starts_with("when_to_use:"));
    }
    assert_eq!(lines[closing + 1], "");
    assert_eq!(lines[closing + 2], "# noether");
}

#[test]
fn test_skill_explicit_frontmatter() {
    let opts = SkillOptions {
        description: Some("Run Noether pipelines.".into()),
        when_to_use: Some("Use when deploying.".into()),
    };
    let content = generate_skill_with(&sample_tree(), None, &opts).unwrap();
    assert!(content.contains("description: Run Noether pipelines."));
    assert!(content.contains("when_to_use: Use when deploying."));
}

#[test]
fn test_skill_collapses_newlines() {
    let opts = SkillOptions {
        description: Some("Line 1\nLine 2".into()),
        when_to_use: None,
    };
    let content = generate_skill_with(&sample_tree(), None, &opts).unwrap();
    assert!(content.contains("description: Line 1 Line 2"));
}

#[test]
fn test_skill_quotes_default_description() {
    // Default description contains "Commands: " (colon-space); must be quoted.
    let content = generate_skill(&sample_tree(), None).unwrap();
    let lines: Vec<&str> = content.lines().collect();
    assert!(lines[2].starts_with("description: \""));
    assert!(lines[2].ends_with("\""));
}

#[test]
fn test_skill_escapes_user_values_with_yaml_specials() {
    let opts = SkillOptions {
        description: Some("Usage: foo; see \"bar\" --- for details".into()),
        when_to_use: Some("has # and : both".into()),
    };
    let content = generate_skill_with(&sample_tree(), None, &opts).unwrap();
    assert!(content.contains("description: \"Usage: foo; see \\\"bar\\\" --- for details\""));
    assert!(content.contains("when_to_use: \"has # and : both\""));
}

#[test]
fn test_skill_leaves_plain_values_unquoted() {
    let opts = SkillOptions {
        description: Some("Run Noether pipelines.".into()),
        when_to_use: None,
    };
    let content = generate_skill_with(&sample_tree(), None, &opts).unwrap();
    assert!(content.contains("description: Run Noether pipelines."));
}

// ── AcliApp ──────────────────────────────────────────────────────────────────

#[test]
fn test_acli_app_new() {
    let app = AcliApp::new("myapp", "1.0.0");
    assert_eq!(app.name, "myapp");
    assert_eq!(app.version, "1.0.0");
}

#[test]
fn test_acli_app_register_command() {
    let mut app = AcliApp::new("myapp", "1.0.0");
    app.register_command(
        CommandInfo::new("hello", "Say hello")
            .idempotent(true)
            .with_examples(vec![
                ("Greet", "myapp hello --name world"),
                ("Formal", "myapp hello --formal"),
            ]),
    );
    assert_eq!(app.command_tree().commands.len(), 1);
    assert_eq!(app.command_tree().commands[0].name, "hello");
}

#[test]
fn test_acli_app_run_success() {
    let app = AcliApp::new("myapp", "1.0.0");
    let code = app.run(|| Ok(()));
    assert_eq!(code, ExitCode::Success);
}

#[test]
fn test_acli_app_run_error() {
    let app = AcliApp::new("myapp", "1.0.0");
    let code = app.run(|| Err(not_found("resource gone").with_hint("check id")));
    assert_eq!(code, ExitCode::NotFound);
}

// ── AcliCommand Trait ────────────────────────────────────────────────────────

acli_args! {
    pub struct TestGetArgs {
        #[arg(long)]
        pub city: String,
    }
}

impl AcliCommand for TestGetArgs {
    fn name() -> &'static str {
        "get"
    }
    fn description() -> &'static str {
        "Get weather"
    }
    fn meta() -> CommandMeta {
        CommandMeta {
            examples: examples(&[
                ("Get London", "weather get --city london"),
                ("Get Tokyo", "weather get --city tokyo"),
            ]),
            idempotent: Idempotency::Yes,
            see_also: vec!["forecast".into()],
        }
    }
}

#[test]
fn test_acli_command_trait() {
    let info = TestGetArgs::command_info();
    assert_eq!(info.name, "get");
    assert_eq!(info.description, "Get weather");
    assert_eq!(info.idempotent, Some(json!(true)));
    assert_eq!(info.examples.as_ref().unwrap().len(), 2);
    assert_eq!(info.see_also.as_ref().unwrap(), &vec!["forecast"]);
}

#[test]
fn test_acli_command_register_via_trait() {
    let mut app = AcliApp::new("weather", "1.0.0");
    app.register::<TestGetArgs>();
    assert_eq!(app.command_tree().commands.len(), 1);
    assert_eq!(app.command_tree().commands[0].name, "get");
}

// ── acli_args! Macro ─────────────────────────────────────────────────────────

#[test]
fn test_acli_args_has_output_field() {
    // TestGetArgs was defined above with acli_args! — verify output field exists
    let args = TestGetArgs {
        city: "london".into(),
        output: OutputFormat::Json,
    };
    assert_eq!(args.output, OutputFormat::Json);
}

acli_args! {
    pub struct TestDeployArgs {
        #[arg(long)]
        pub target: String,
    } with dry_run
}

#[test]
fn test_acli_args_with_dry_run() {
    let args = TestDeployArgs {
        target: "staging".into(),
        output: OutputFormat::Text,
        dry_run: true,
    };
    assert!(args.dry_run);
    assert_eq!(args.output, OutputFormat::Text);
}

// ── Idempotency ──────────────────────────────────────────────────────────────

#[test]
fn test_idempotency_values() {
    assert_eq!(Idempotency::Yes.to_json_value(), json!(true));
    assert_eq!(Idempotency::No.to_json_value(), json!(false));
    assert_eq!(
        Idempotency::Conditional.to_json_value(),
        json!("conditional")
    );
}
