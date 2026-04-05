//! AcliApp — the main application wrapper, equivalent to Python's ACLIApp.

use crate::cli_folder::{generate_cli_folder, needs_update};
use crate::errors::AcliError;
use crate::exit_codes::ExitCode;
use crate::introspect::CommandTree;
use crate::output::{emit, error_envelope, success_envelope, OutputFormat};
use crate::skill::generate_skill;
use serde_json::json;
use std::path::PathBuf;

/// ACLI-compliant application wrapper.
///
/// Manages the command tree, auto-generates built-in commands
/// (introspect, version, skill), handles errors with JSON envelopes,
/// and maintains the `.cli/` folder.
///
/// # Example
///
/// ```rust
/// use acli::app::AcliApp;
///
/// let app = AcliApp::new("myapp", "1.0.0");
/// ```
pub struct AcliApp {
    pub name: String,
    pub version: String,
    tree: CommandTree,
    cli_dir: Option<PathBuf>,
}

impl AcliApp {
    /// Create a new ACLI application.
    pub fn new(name: impl Into<String>, version: impl Into<String>) -> Self {
        let name = name.into();
        let version = version.into();
        let tree = CommandTree::new(&name, &version);
        Self {
            name,
            version,
            tree,
            cli_dir: None,
        }
    }

    /// Set the .cli/ folder directory.
    pub fn with_cli_dir(mut self, dir: impl Into<PathBuf>) -> Self {
        self.cli_dir = Some(dir.into());
        self
    }

    /// Register a command's metadata for introspection.
    pub fn register<C: crate::command::AcliCommand>(&mut self) {
        self.tree.add_command(C::command_info());
    }

    /// Register a command info directly.
    pub fn register_command(&mut self, info: crate::introspect::CommandInfo) {
        self.tree.add_command(info);
    }

    /// Get the full command tree (including built-in commands).
    pub fn command_tree(&self) -> &CommandTree {
        &self.tree
    }

    /// Handle the `introspect` built-in command.
    pub fn handle_introspect(&self, output: &OutputFormat) {
        // Update .cli/ if needed
        let dir = self.cli_dir.as_deref();
        if needs_update(&self.tree, dir) {
            let _ = generate_cli_folder(&self.tree, dir);
        }

        let tree_json = serde_json::to_value(&self.tree).unwrap_or_default();
        let envelope = success_envelope("introspect", tree_json, &self.version, None);
        emit(&envelope, output);
    }

    /// Handle the `version` built-in command.
    pub fn handle_version(&self, output: &OutputFormat) {
        let data = json!({
            "tool": self.name,
            "version": self.version,
            "acli_version": "0.1.0",
        });

        if *output == OutputFormat::Json {
            let envelope = success_envelope("version", data, &self.version, None);
            emit(&envelope, output);
        } else {
            println!("{} {}", self.name, self.version);
            println!("acli 0.1.0");
        }

        // Update .cli/ if needed
        let dir = self.cli_dir.as_deref();
        if needs_update(&self.tree, dir) {
            let _ = generate_cli_folder(&self.tree, dir);
        }
    }

    /// Handle the `skill` built-in command.
    pub fn handle_skill(&self, out_path: Option<&str>, output: &OutputFormat) {
        let path = out_path.map(std::path::PathBuf::from);
        let content = generate_skill(&self.tree, path.as_deref()).unwrap_or_default();

        if *output == OutputFormat::Json {
            let data = json!({
                "path": out_path,
                "content": content,
            });
            let envelope = success_envelope("skill", data, &self.version, None);
            emit(&envelope, output);
        } else if out_path.is_some() {
            println!("Skill file written to {}", out_path.unwrap());
        } else {
            print!("{content}");
        }
    }

    /// Handle an AcliError — emit JSON error envelope and return the exit code.
    pub fn handle_error(&self, err: &AcliError) -> ExitCode {
        let cmd_name = err.command.as_deref().unwrap_or(&self.name);
        let envelope = error_envelope(
            cmd_name,
            err.code,
            &err.message,
            err.hint.as_deref(),
            err.docs.as_deref(),
            &self.version,
            None,
        );
        emit(&envelope, &OutputFormat::Json);
        err.code
    }

    /// Run a command handler, catching AcliErrors and emitting envelopes.
    ///
    /// Returns the exit code (0 for success).
    pub fn run<F>(&self, f: F) -> ExitCode
    where
        F: FnOnce() -> Result<(), AcliError>,
    {
        match f() {
            Ok(()) => ExitCode::Success,
            Err(err) => self.handle_error(&err),
        }
    }
}
