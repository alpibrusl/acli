//! ACLI error types with actionable messages per spec §4.

use crate::exit_codes::ExitCode;

/// Base error for ACLI commands. Always actionable per spec §4.2.
#[derive(Debug)]
pub struct AcliError {
    pub message: String,
    pub code: ExitCode,
    pub hint: Option<String>,
    pub docs: Option<String>,
    pub command: Option<String>,
}

impl AcliError {
    /// Create a new general error.
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            code: ExitCode::GeneralError,
            hint: None,
            docs: None,
            command: None,
        }
    }

    /// Set the exit code.
    pub fn with_code(mut self, code: ExitCode) -> Self {
        self.code = code;
        self
    }

    /// Set the hint.
    pub fn with_hint(mut self, hint: impl Into<String>) -> Self {
        self.hint = Some(hint.into());
        self
    }

    /// Set the docs reference.
    pub fn with_docs(mut self, docs: impl Into<String>) -> Self {
        self.docs = Some(docs.into());
        self
    }

    /// Set the command name.
    pub fn with_command(mut self, command: impl Into<String>) -> Self {
        self.command = Some(command.into());
        self
    }
}

impl std::fmt::Display for AcliError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl std::error::Error for AcliError {}

/// Create an InvalidArgs error.
pub fn invalid_args(message: impl Into<String>) -> AcliError {
    AcliError::new(message).with_code(ExitCode::InvalidArgs)
}

/// Create a NotFound error.
pub fn not_found(message: impl Into<String>) -> AcliError {
    AcliError::new(message).with_code(ExitCode::NotFound)
}

/// Create a Conflict error.
pub fn conflict(message: impl Into<String>) -> AcliError {
    AcliError::new(message).with_code(ExitCode::Conflict)
}

/// Create a PreconditionFailed error.
pub fn precondition_failed(message: impl Into<String>) -> AcliError {
    AcliError::new(message).with_code(ExitCode::PreconditionFailed)
}

/// Suggest a close match for a mistyped flag per spec §4.1.
pub fn suggest_flag<'a>(unknown: &str, known: &'a [&str]) -> Option<&'a str> {
    known
        .iter()
        .filter_map(|k| {
            let dist = levenshtein(unknown, k);
            if dist <= 2 {
                Some((*k, dist))
            } else {
                None
            }
        })
        .min_by_key(|(_, d)| *d)
        .map(|(k, _)| k)
}

fn levenshtein(a: &str, b: &str) -> usize {
    let a: Vec<char> = a.chars().collect();
    let b: Vec<char> = b.chars().collect();
    let mut matrix = vec![vec![0usize; b.len() + 1]; a.len() + 1];
    for (i, row) in matrix.iter_mut().enumerate() {
        row[0] = i;
    }
    for (j, cell) in matrix[0].iter_mut().enumerate() {
        *cell = j;
    }
    for i in 1..=a.len() {
        for j in 1..=b.len() {
            let cost = if a[i - 1] == b[j - 1] { 0 } else { 1 };
            matrix[i][j] = (matrix[i - 1][j] + 1)
                .min(matrix[i][j - 1] + 1)
                .min(matrix[i - 1][j - 1] + cost);
        }
    }
    matrix[a.len()][b.len()]
}
