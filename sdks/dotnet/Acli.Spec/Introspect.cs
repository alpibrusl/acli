using System.Text.Json.Serialization;

namespace Acli;

public sealed class Example
{
    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("invocation")]
    public string Invocation { get; set; } = "";
}

public sealed class ParamInfo
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("type")]
    public string Type { get; set; } = "";

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("default")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Default { get; set; }

    [JsonPropertyName("required")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? Required { get; set; }
}

public sealed class CommandInfo
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("arguments")]
    public List<ParamInfo> Arguments { get; set; } = [];

    [JsonPropertyName("options")]
    public List<ParamInfo> Options { get; set; } = [];

    [JsonPropertyName("subcommands")]
    public List<CommandInfo> Subcommands { get; set; } = [];

    [JsonPropertyName("idempotent")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Idempotent { get; set; }

    [JsonPropertyName("examples")]
    public List<Example>? Examples { get; set; }

    [JsonPropertyName("see_also")]
    public List<string>? SeeAlso { get; set; }
}

public sealed class CommandTree
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("version")]
    public string Version { get; set; } = "";

    [JsonPropertyName("acli_version")]
    public string AcliVersion { get; set; } = "0.1.0";

    [JsonPropertyName("commands")]
    public List<CommandInfo> Commands { get; set; } = [];
}
