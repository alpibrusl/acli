using System.Text.Json;

namespace Acli;

public static class Output
{
    private static readonly JsonSerializerOptions JsonOpts = new() { WriteIndented = true };

    public static Envelope SuccessEnvelope(string command, object? data, string version, DateTimeOffset? start)
    {
        var ms = start.HasValue ? (long)(DateTimeOffset.UtcNow - start.Value).TotalMilliseconds : 0;
        return new Envelope
        {
            Ok = true,
            Command = command,
            Data = data,
            Meta = new Meta { DurationMs = ms, Version = version },
        };
    }

    public static Envelope DryRunEnvelope(string command, object[] planned, string version, DateTimeOffset? start)
    {
        var ms = start.HasValue ? (long)(DateTimeOffset.UtcNow - start.Value).TotalMilliseconds : 0;
        return new Envelope
        {
            Ok = true,
            Command = command,
            DryRun = true,
            PlannedActions = planned,
            Meta = new Meta { DurationMs = ms, Version = version },
        };
    }

    public static Envelope ErrorEnvelope(
        string command,
        ExitCode code,
        string message,
        string? hint,
        string? docs,
        string version,
        DateTimeOffset? start)
    {
        var ms = start.HasValue ? (long)(DateTimeOffset.UtcNow - start.Value).TotalMilliseconds : 0;
        var ed = new ErrorDetail { Code = code.WireName(), Message = message };
        if (hint != null) ed.Hint = hint;
        if (docs != null) ed.Docs = docs;
        return new Envelope
        {
            Ok = false,
            Command = command,
            Error = ed,
            Meta = new Meta { DurationMs = ms, Version = version },
        };
    }

    public static void Emit(Envelope env, OutputFormat format, TextWriter stdout, TextWriter stderr)
    {
        if (format == OutputFormat.Json)
        {
            stdout.WriteLine(JsonSerializer.Serialize(env, JsonOpts));
            return;
        }
        if (!env.Ok && env.Error != null)
        {
            stderr.WriteLine($"Error [{env.Error.Code}]: {env.Error.Message}");
            if (env.Error.Hint != null) stderr.WriteLine($"  {env.Error.Hint}");
            if (env.Error.Docs != null) stderr.WriteLine($"  Reference: {env.Error.Docs}");
            return;
        }
        if (env.Data is Dictionary<string, object> map)
        {
            foreach (var kv in map)
                stdout.WriteLine($"{kv.Key}: {kv.Value}");
        }
    }

    public static void EmitProgress(TextWriter w, string step, string status, string? detail = null)
    {
        var line = new Dictionary<string, string>
        {
            ["type"] = "progress",
            ["step"] = step,
            ["status"] = status,
        };
        if (detail != null) line["detail"] = detail;
        w.WriteLine(JsonSerializer.Serialize(line));
    }

    public static void EmitResult(TextWriter w, Dictionary<string, object> data, bool ok = true)
    {
        var line = new Dictionary<string, object> { ["type"] = "result", ["ok"] = ok };
        foreach (var kv in data)
            line[kv.Key] = kv.Value;
        w.WriteLine(JsonSerializer.Serialize(line));
    }
}
