namespace Acli;

/// <summary>Actionable error (spec §4).</summary>
public sealed class AcliError : Exception
{
    public ExitCode Code { get; set; }
    public string? Hint { get; set; }
    public string? Docs { get; set; }
    public string? Command { get; set; }

    public AcliError(string message, ExitCode code = ExitCode.GeneralError) : base(message) =>
        Code = code;
}
