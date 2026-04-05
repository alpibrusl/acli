//! ACLI — Agent-friendly CLI Rust SDK.
//!
//! Build CLI tools that AI agents can discover, learn, and use autonomously.
//! Wraps [clap](https://docs.rs/clap) with ACLI spec enforcement.
//!
//! # Quick Start
//!
//! ```rust
//! use acli::app::AcliApp;
//! use acli::command::{AcliCommand, CommandMeta, Idempotency, examples};
//! use acli::acli_args;
//! use acli::{OutputFormat, success_envelope, emit};
//! use serde_json::json;
//!
//! // Define args with auto-injected --output
//! acli_args! {
//!     pub struct GetArgs {
//!         #[arg(long)]
//!         pub city: String,
//!     }
//! }
//!
//! // Implement AcliCommand trait for metadata
//! impl AcliCommand for GetArgs {
//!     fn name() -> &'static str { "get" }
//!     fn description() -> &'static str { "Get current weather" }
//!     fn meta() -> CommandMeta {
//!         CommandMeta {
//!             examples: examples(&[
//!                 ("Get London weather", "weather get --city london"),
//!                 ("Get Tokyo in JSON", "weather get --city tokyo --output json"),
//!             ]),
//!             idempotent: Idempotency::Yes,
//!             see_also: vec!["forecast".into()],
//!         }
//!     }
//! }
//!
//! // Build app and register commands
//! let mut app = AcliApp::new("weather", "1.0.0");
//! app.register::<GetArgs>();
//!
//! // Emit structured output
//! let data = json!({"city": "london", "temp": 18.5});
//! let envelope = success_envelope("get", data, "1.0.0", None);
//! emit(&envelope, &OutputFormat::Json);
//! ```

pub mod app;
pub mod cli_folder;
pub mod command;
pub mod errors;
pub mod exit_codes;
pub mod introspect;
#[macro_use]
pub mod macros;
pub mod output;
pub mod skill;

// Re-export key types at crate root
pub use app::AcliApp;
pub use command::{AcliCommand, CommandMeta, Idempotency};
pub use errors::AcliError;
pub use exit_codes::ExitCode;
pub use introspect::{CommandInfo, CommandTree};
pub use output::{
    emit, emit_progress, emit_result, error_envelope, error_envelope_raw, success_envelope,
    OutputFormat,
};
