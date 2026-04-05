//! AcliCommand trait and metadata per ACLI spec §1, §5, §6.

use crate::introspect::{CommandInfo, Example};

/// Metadata for an ACLI command — equivalent to Python's `@acli_command`.
pub struct CommandMeta {
    pub examples: Vec<Example>,
    pub idempotent: Idempotency,
    pub see_also: Vec<String>,
}

/// Idempotency declaration per spec §6.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Idempotency {
    Yes,
    No,
    Conditional,
}

impl Idempotency {
    pub fn to_json_value(&self) -> serde_json::Value {
        match self {
            Self::Yes => serde_json::Value::Bool(true),
            Self::No => serde_json::Value::Bool(false),
            Self::Conditional => serde_json::Value::String("conditional".into()),
        }
    }
}

/// Trait that ACLI commands implement to provide metadata.
///
/// This is the Rust equivalent of Python's `@acli_command` decorator.
pub trait AcliCommand {
    /// Command name (used in CLI and introspection).
    fn name() -> &'static str;

    /// One-line description.
    fn description() -> &'static str;

    /// Command metadata: examples, idempotency, see_also.
    fn meta() -> CommandMeta;

    /// Build a CommandInfo for introspection.
    fn command_info() -> CommandInfo {
        let meta = Self::meta();
        let mut info = CommandInfo::new(Self::name(), Self::description());
        info.idempotent = Some(meta.idempotent.to_json_value());
        info.examples = Some(
            meta.examples
                .into_iter()
                .map(|e| Example {
                    description: e.description,
                    invocation: e.invocation,
                })
                .collect(),
        );
        if !meta.see_also.is_empty() {
            info.see_also = Some(meta.see_also);
        }
        info
    }
}

/// Helper to build examples for `CommandMeta`.
pub fn examples(pairs: &[(&str, &str)]) -> Vec<Example> {
    pairs
        .iter()
        .map(|(desc, inv)| Example {
            description: desc.to_string(),
            invocation: inv.to_string(),
        })
        .collect()
}
