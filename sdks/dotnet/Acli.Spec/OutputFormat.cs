namespace Acli;

public enum OutputFormat
{
    Text,
    Json,
    Table,
}

public static class OutputFormatParser
{
    public static OutputFormat Parse(string? s) => s?.ToLowerInvariant() switch
    {
        "json" => OutputFormat.Json,
        "table" => OutputFormat.Table,
        _ => OutputFormat.Text,
    };
}
