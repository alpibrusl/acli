//! Semantic exit codes as defined by ACLI spec §3.

/// ACLI semantic exit codes.
///
/// Codes 0-9 are defined by the spec. Codes 10-63 are reserved for tool-specific use.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(i32)]
pub enum ExitCode {
    Success = 0,
    GeneralError = 1,
    InvalidArgs = 2,
    NotFound = 3,
    PermissionDenied = 4,
    Conflict = 5,
    Timeout = 6,
    UpstreamError = 7,
    PreconditionFailed = 8,
    DryRun = 9,
}

impl ExitCode {
    /// Convert to process exit code.
    pub fn code(self) -> i32 {
        self as i32
    }

    /// Get the string name of this exit code.
    pub fn name(&self) -> &'static str {
        match self {
            Self::Success => "SUCCESS",
            Self::GeneralError => "GENERAL_ERROR",
            Self::InvalidArgs => "INVALID_ARGS",
            Self::NotFound => "NOT_FOUND",
            Self::PermissionDenied => "PERMISSION_DENIED",
            Self::Conflict => "CONFLICT",
            Self::Timeout => "TIMEOUT",
            Self::UpstreamError => "UPSTREAM_ERROR",
            Self::PreconditionFailed => "PRECONDITION_FAILED",
            Self::DryRun => "DRY_RUN",
        }
    }
}

impl From<ExitCode> for std::process::ExitCode {
    fn from(code: ExitCode) -> Self {
        std::process::ExitCode::from(code.code() as u8)
    }
}
