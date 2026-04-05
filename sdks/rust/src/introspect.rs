//! Introspection and command-tree builder per ACLI spec §1.2.

use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Full command tree as specified in ACLI spec §1.2.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CommandTree {
    pub name: String,
    pub version: String,
    pub acli_version: String,
    pub commands: Vec<CommandInfo>,
}

/// Metadata for a single command.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CommandInfo {
    pub name: String,
    pub description: String,
    #[serde(default)]
    pub arguments: Vec<ParamInfo>,
    #[serde(default)]
    pub options: Vec<ParamInfo>,
    #[serde(default)]
    pub subcommands: Vec<CommandInfo>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub idempotent: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub examples: Option<Vec<Example>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub see_also: Option<Vec<String>>,
}

/// Parameter metadata (argument or option).
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ParamInfo {
    pub name: String,
    #[serde(rename = "type")]
    pub param_type: String,
    pub description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub required: Option<bool>,
}

/// A concrete usage example.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Example {
    pub description: String,
    pub invocation: String,
}

impl CommandTree {
    /// Create a new command tree.
    pub fn new(name: impl Into<String>, version: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            version: version.into(),
            acli_version: "0.1.0".to_string(),
            commands: Vec::new(),
        }
    }

    /// Add a command to the tree.
    pub fn add_command(&mut self, command: CommandInfo) {
        self.commands.push(command);
    }
}

impl CommandInfo {
    /// Create a new command info.
    pub fn new(name: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            arguments: Vec::new(),
            options: Vec::new(),
            subcommands: Vec::new(),
            idempotent: None,
            examples: None,
            see_also: None,
        }
    }

    /// Set idempotency.
    pub fn idempotent(mut self, value: bool) -> Self {
        self.idempotent = Some(Value::Bool(value));
        self
    }

    /// Set idempotency to "conditional".
    pub fn conditionally_idempotent(mut self) -> Self {
        self.idempotent = Some(Value::String("conditional".into()));
        self
    }

    /// Add examples.
    pub fn with_examples(mut self, examples: Vec<(&str, &str)>) -> Self {
        self.examples = Some(
            examples
                .into_iter()
                .map(|(desc, inv)| Example {
                    description: desc.to_string(),
                    invocation: inv.to_string(),
                })
                .collect(),
        );
        self
    }

    /// Add see_also references.
    pub fn with_see_also(mut self, refs: Vec<&str>) -> Self {
        self.see_also = Some(refs.into_iter().map(String::from).collect());
        self
    }

    /// Add an option.
    pub fn add_option(
        mut self,
        name: &str,
        param_type: &str,
        description: &str,
        default: Option<Value>,
    ) -> Self {
        self.options.push(ParamInfo {
            name: name.to_string(),
            param_type: param_type.to_string(),
            description: description.to_string(),
            default,
            required: None,
        });
        self
    }

    /// Add an argument.
    pub fn add_argument(
        mut self,
        name: &str,
        param_type: &str,
        description: &str,
        required: bool,
    ) -> Self {
        self.arguments.push(ParamInfo {
            name: name.to_string(),
            param_type: param_type.to_string(),
            description: description.to_string(),
            default: None,
            required: Some(required),
        });
        self
    }
}
