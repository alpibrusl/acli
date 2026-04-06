namespace Acli;

/// <summary>ACLI semantic exit codes (spec §3).</summary>
public enum ExitCode
{
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

public static class ExitCodeExtensions
{
    public static string WireName(this ExitCode code) => code switch
    {
        ExitCode.Success => "SUCCESS",
        ExitCode.GeneralError => "GENERAL_ERROR",
        ExitCode.InvalidArgs => "INVALID_ARGS",
        ExitCode.NotFound => "NOT_FOUND",
        ExitCode.PermissionDenied => "PERMISSION_DENIED",
        ExitCode.Conflict => "CONFLICT",
        ExitCode.Timeout => "TIMEOUT",
        ExitCode.UpstreamError => "UPSTREAM_ERROR",
        ExitCode.PreconditionFailed => "PRECONDITION_FAILED",
        ExitCode.DryRun => "DRY_RUN",
        _ => "UNKNOWN",
    };
}
