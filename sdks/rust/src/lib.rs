//! ACLI — Agent-friendly CLI Rust SDK.
//!
//! Build CLI tools that AI agents can discover, learn, and use autonomously.
//! Wraps [clap](https://docs.rs/clap) with ACLI spec enforcement.
//!
//! # Quick Start
//!
//! ```rust
//! use acli::introspect::{CommandTree, CommandInfo};
//! use acli::output::{OutputFormat, success_envelope, emit};
//! use serde_json::json;
//!
//! let mut tree = CommandTree::new("myapp", "1.0.0");
//! tree.add_command(
//!     CommandInfo::new("hello", "Greet someone")
//!         .idempotent(true)
//!         .with_examples(vec![
//!             ("Greet world", "myapp hello --name world"),
//!             ("Greet formally", "myapp hello --name world --formal"),
//!         ])
//!         .add_option("name", "string", "Who to greet", None)
//! );
//!
//! let envelope = success_envelope("hello", json!({"greeting": "Hello!"}), "1.0.0", None);
//! emit(&envelope, &OutputFormat::Json);
//! ```

pub mod cli_folder;
pub mod errors;
pub mod exit_codes;
pub mod introspect;
pub mod output;
pub mod skill;

// Re-export key types at crate root
pub use errors::AcliError;
pub use exit_codes::ExitCode;
pub use introspect::{CommandInfo, CommandTree};
pub use output::{
    emit, emit_progress, emit_result, error_envelope, success_envelope, OutputFormat,
};
