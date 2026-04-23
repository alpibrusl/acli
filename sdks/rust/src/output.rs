//! Output format handling and JSON envelope as defined by ACLI spec §2.

use crate::exit_codes::ExitCode;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::io::{self, Write};
use std::time::Instant;

/// Supported output formats per ACLI spec §2.1.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub enum OutputFormat {
    #[default]
    Text,
    Json,
    Table,
}

impl std::str::FromStr for OutputFormat {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "text" => Ok(Self::Text),
            "json" => Ok(Self::Json),
            "table" => Ok(Self::Table),
            other => Err(format!(
                "Invalid output format: '{other}'. Use text, json, or table."
            )),
        }
    }
}

impl std::fmt::Display for OutputFormat {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Text => write!(f, "text"),
            Self::Json => write!(f, "json"),
            Self::Table => write!(f, "table"),
        }
    }
}

/// Standard JSON envelope per ACLI spec §2.2.
#[derive(Debug, Serialize, Deserialize)]
pub struct Envelope {
    pub ok: bool,
    pub command: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dry_run: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub planned_actions: Option<Vec<Value>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<ErrorDetail>,
    pub meta: Meta,
}

/// Error detail within the envelope.
#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorDetail {
    pub code: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hint: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hints: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub docs: Option<String>,
}

/// Optional cache metadata in success envelope `meta.cache` (ACLI spec §2.2).
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct CacheMeta {
    pub hit: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub key: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub age_seconds: Option<u64>,
}

/// Metadata within the envelope.
#[derive(Debug, Serialize, Deserialize)]
pub struct Meta {
    pub duration_ms: u64,
    pub version: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cache: Option<CacheMeta>,
}

/// Build a success envelope.
pub fn success_envelope(
    command: &str,
    data: Value,
    version: &str,
    start: Option<Instant>,
    cache: Option<CacheMeta>,
) -> Envelope {
    let duration_ms = start.map_or(0, |s| s.elapsed().as_millis() as u64);
    Envelope {
        ok: true,
        command: command.to_string(),
        data: Some(data),
        dry_run: None,
        planned_actions: None,
        error: None,
        meta: Meta {
            duration_ms,
            version: version.to_string(),
            cache,
        },
    }
}

/// Build a dry-run success envelope.
pub fn dry_run_envelope(
    command: &str,
    planned_actions: Vec<Value>,
    version: &str,
    start: Option<Instant>,
    cache: Option<CacheMeta>,
) -> Envelope {
    let duration_ms = start.map_or(0, |s| s.elapsed().as_millis() as u64);
    Envelope {
        ok: true,
        command: command.to_string(),
        data: None,
        dry_run: Some(true),
        planned_actions: Some(planned_actions),
        error: None,
        meta: Meta {
            duration_ms,
            version: version.to_string(),
            cache,
        },
    }
}

/// Build an error envelope using a typed ExitCode.
///
/// The argument count reflects the required shape of the ACLI error envelope
/// (spec §2.2: `command`, `code`, `message`, `hint`, `hints`, `docs`, `version`,
/// plus timing). Grouping these into a struct would hide the spec alignment;
/// the lint is silenced deliberately.
#[allow(clippy::too_many_arguments)]
pub fn error_envelope(
    command: &str,
    code: ExitCode,
    message: &str,
    hint: Option<&str>,
    hints: Option<Vec<String>>,
    docs: Option<&str>,
    version: &str,
    start: Option<Instant>,
) -> Envelope {
    error_envelope_raw(
        command,
        code.name(),
        message,
        hint,
        hints,
        docs,
        version,
        start,
    )
}

/// Build an error envelope from a raw code string.
///
/// See `error_envelope` — the argument shape mirrors the spec's error envelope
/// fields, so the `too_many_arguments` lint is allowed here.
#[allow(clippy::too_many_arguments)]
pub fn error_envelope_raw(
    command: &str,
    code: &str,
    message: &str,
    hint: Option<&str>,
    hints: Option<Vec<String>>,
    docs: Option<&str>,
    version: &str,
    start: Option<Instant>,
) -> Envelope {
    let duration_ms = start.map_or(0, |s| s.elapsed().as_millis() as u64);
    Envelope {
        ok: false,
        command: command.to_string(),
        data: None,
        dry_run: None,
        planned_actions: None,
        error: Some(ErrorDetail {
            code: code.to_string(),
            message: message.to_string(),
            hint: hint.map(String::from),
            hints,
            docs: docs.map(String::from),
        }),
        meta: Meta {
            duration_ms,
            version: version.to_string(),
            cache: None,
        },
    }
}

/// Emit an envelope to stdout in the requested format.
pub fn emit(envelope: &Envelope, format: &OutputFormat) {
    match format {
        OutputFormat::Json => {
            if let Ok(json) = serde_json::to_string_pretty(envelope) {
                println!("{json}");
            }
        }
        OutputFormat::Text => emit_text(envelope),
        OutputFormat::Table => emit_table(envelope),
    }
}

/// Emit a progress line as NDJSON per spec §2.3.
pub fn emit_progress(step: &str, status: &str, detail: Option<&str>) {
    let mut line = serde_json::Map::new();
    line.insert("type".into(), Value::String("progress".into()));
    line.insert("step".into(), Value::String(step.into()));
    line.insert("status".into(), Value::String(status.into()));
    if let Some(d) = detail {
        line.insert("detail".into(), Value::String(d.into()));
    }
    if let Ok(json) = serde_json::to_string(&line) {
        println!("{json}");
        io::stdout().flush().ok();
    }
}

/// Emit a final result line as NDJSON per spec §2.3.
pub fn emit_result(data: Value, ok: bool) {
    let mut line = serde_json::Map::new();
    line.insert("type".into(), Value::String("result".into()));
    line.insert("ok".into(), Value::Bool(ok));
    if let Value::Object(map) = data {
        for (k, v) in map {
            line.insert(k, v);
        }
    }
    if let Ok(json) = serde_json::to_string(&line) {
        println!("{json}");
        io::stdout().flush().ok();
    }
}

fn emit_text(envelope: &Envelope) {
    if !envelope.ok {
        if let Some(ref err) = envelope.error {
            eprintln!("Error [{}]: {}", err.code, err.message);
            if let Some(ref hint) = err.hint {
                eprintln!("  {hint}");
            }
            if let Some(ref hints) = err.hints {
                for line in hints {
                    eprintln!("  {line}");
                }
            }
            if let Some(ref docs) = err.docs {
                eprintln!("  Reference: {docs}");
            }
        }
    } else if let Some(Value::Object(ref map)) = envelope.data {
        for (key, value) in map {
            println!("{key}: {value}");
        }
    }
}

fn emit_table(envelope: &Envelope) {
    if let Some(Value::Object(map)) = &envelope.data {
        let max_key = map.keys().map(|k| k.len()).max().unwrap_or(0);
        for (key, value) in map {
            println!("{key:<max_key$}  {value}");
        }
    } else if let Some(Value::Array(items)) = &envelope.data {
        if let Some(Value::Object(first)) = items.first() {
            let headers: Vec<&String> = first.keys().collect();
            let mut widths: HashMap<&str, usize> =
                headers.iter().map(|h| (h.as_str(), h.len())).collect();
            for item in items {
                if let Value::Object(row) = item {
                    for h in &headers {
                        let val_len = row.get(h.as_str()).map_or(0, |v| v.to_string().len());
                        let w = widths.entry(h.as_str()).or_insert(0);
                        *w = (*w).max(val_len);
                    }
                }
            }
            let header_line: Vec<String> = headers
                .iter()
                .map(|h| format!("{:<width$}", h, width = widths[h.as_str()]))
                .collect();
            println!("{}", header_line.join("  "));
            let sep: Vec<String> = headers
                .iter()
                .map(|h| "-".repeat(widths[h.as_str()]))
                .collect();
            println!("{}", sep.join("  "));
            for item in items {
                if let Value::Object(row) = item {
                    let vals: Vec<String> = headers
                        .iter()
                        .map(|h| {
                            let v = row
                                .get(h.as_str())
                                .map_or("".to_string(), |v| v.to_string());
                            format!("{:<width$}", v, width = widths[h.as_str()])
                        })
                        .collect();
                    println!("{}", vals.join("  "));
                }
            }
        }
    }
}
