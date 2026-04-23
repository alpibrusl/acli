using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace Acli;

/// <summary>
/// Options forwarded into the SKILL.md frontmatter (agentskills.io).
/// </summary>
public sealed record SkillOptions
{
    public string? Description { get; init; }
    public string? WhenToUse { get; init; }
}

public static class Skill
{
    static readonly HashSet<string> Builtin = new() { "introspect", "version", "skill" };

    static readonly HashSet<char> YamlReservedStart = new()
    {
        '!', '&', '*', '?', '|', '>', '\'', '"', '%', '@', '`', '#', ',',
        '[', ']', '{', '}', '-', ':',
    };

    /// <summary>Render a scalar safe for a single-line YAML block mapping value.</summary>
    internal static string YamlScalar(string value)
    {
        if (string.IsNullOrEmpty(value))
            return "\"\"";
        var needsQuoting =
            value.Contains(": ") ||
            value.Contains(" #") ||
            YamlReservedStart.Contains(value[0]) ||
            value.EndsWith(':') ||
            value.Trim() != value;
        if (!needsQuoting)
            return value;
        var escaped = value.Replace("\\", "\\\\").Replace("\"", "\\\"");
        return $"\"{escaped}\"";
    }

    public static string Generate(CommandTree tree, string? path) =>
        Generate(tree, path, new SkillOptions());

    /// <summary>
    /// Generate a SKILL.md file conforming to the agentskills.io open standard
    /// (https://agentskills.io): YAML frontmatter + ACLI body.
    /// </summary>
    public static string Generate(CommandTree tree, string? path, SkillOptions opts)
    {
        var name = tree.Name;
        var ver = tree.Version;

        var userCommands = tree.Commands.Where(c => !Builtin.Contains(c.Name)).ToList();

        var description = !string.IsNullOrEmpty(opts.Description)
            ? CollapseWs(opts.Description!)
            : DefaultDescription(name, userCommands);

        var b = new StringBuilder();
        b.Append("---\n");
        b.Append($"name: {YamlScalar(name)}\n");
        b.Append($"description: {YamlScalar(description)}\n");
        if (!string.IsNullOrEmpty(opts.WhenToUse))
        {
            b.Append($"when_to_use: {YamlScalar(CollapseWs(opts.WhenToUse!))}\n");
        }
        b.Append("---\n\n");

        b.AppendLine($"# {name}");
        b.AppendLine();
        b.AppendLine($"> Auto-generated skill file for `{name}` v{ver}");
        b.AppendLine($"> Re-generate with: `{name} skill` or `acli skill --bin {name}`");
        b.AppendLine();
        b.AppendLine("## Available commands");
        b.AppendLine();
        foreach (var cmd in userCommands)
        {
            var tag = IdemTag(cmd);
            b.AppendLine($"- `{name} {cmd.Name}` — {cmd.Description}{tag}");
        }
        b.AppendLine();
        foreach (var cmd in userCommands)
        {
            b.AppendLine($"## `{name} {cmd.Name}`");
            b.AppendLine();
            if (!string.IsNullOrEmpty(cmd.Description))
            {
                b.AppendLine(cmd.Description);
                b.AppendLine();
            }
            if (cmd.Options.Count > 0)
            {
                b.AppendLine("### Options");
                b.AppendLine();
                foreach (var o in cmd.Options)
                {
                    var def = o.Default != null ? $" [default: {o.Default}]" : "";
                    var on = o.Name.Replace("_", "-");
                    b.AppendLine($"- `--{on}` ({o.Type}) — {o.Description}{def}");
                }
                b.AppendLine();
            }
            if (cmd.Arguments.Count > 0)
            {
                b.AppendLine("### Arguments");
                b.AppendLine();
                foreach (var a in cmd.Arguments)
                {
                    var req = a.Required == true ? "required" : "optional";
                    b.AppendLine($"- `{a.Name}` ({a.Type}, {req}) — {a.Description}");
                }
                b.AppendLine();
            }
            if (cmd.Examples is { Count: > 0 })
            {
                b.AppendLine("### Examples");
                b.AppendLine();
                foreach (var ex in cmd.Examples)
                {
                    b.AppendLine("```bash");
                    b.AppendLine($"# {ex.Description}");
                    b.AppendLine(ex.Invocation);
                    b.AppendLine("```");
                    b.AppendLine();
                }
            }
            if (cmd.SeeAlso is { Count: > 0 })
            {
                var refs = string.Join(", ", cmd.SeeAlso.Select(s => $"`{name} {s}`"));
                b.AppendLine($"**See also:** {refs}");
                b.AppendLine();
            }
        }
        b.AppendLine("## Output format");
        b.AppendLine();
        b.AppendLine("All commands support `--output json|text|table`. When using `--output json`, responses follow a standard envelope:");
        b.AppendLine();
        b.AppendLine("```json");
        b.AppendLine(@"{""ok"": true, ""command"": ""..."", ""data"": {...}, ""meta"": {""duration_ms"": ..., ""version"": ""...""}}");
        b.AppendLine("```");
        b.AppendLine();
        b.AppendLine("## Exit codes");
        b.AppendLine();
        b.AppendLine("| Code | Meaning | Action |");
        b.AppendLine("|------|---------|--------|");
        b.AppendLine("| 0 | Success | Proceed |");
        b.AppendLine("| 2 | Invalid arguments | Correct and retry |");
        b.AppendLine("| 3 | Not found | Check inputs |");
        b.AppendLine("| 5 | Conflict | Resolve conflict |");
        b.AppendLine("| 8 | Precondition failed | Fix precondition |");
        b.AppendLine("| 9 | Dry-run completed | Review and confirm |");
        b.AppendLine();
        b.AppendLine("## Further discovery");
        b.AppendLine();
        b.AppendLine($"- `{name} --help` — full help for any command");
        b.AppendLine($"- `{name} introspect` — machine-readable command tree (JSON)");
        b.AppendLine("- `.cli/README.md` — persistent reference (survives context resets)");
        b.AppendLine();
        var content = b.ToString();
        if (!string.IsNullOrEmpty(path))
        {
            var dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir))
                Directory.CreateDirectory(dir);
            File.WriteAllText(path, content);
        }
        return content;
    }

    static string CollapseWs(string s) =>
        Regex.Replace(s.Trim(), @"\s+", " ");

    static string DefaultDescription(string name, List<CommandInfo> userCommands)
    {
        if (userCommands.Count == 0)
            return $"Invoke the `{name}` CLI.";
        var shown = userCommands.Take(4).Select(c => c.Name);
        var suffix = userCommands.Count > 4 ? "…" : "";
        return $"Invoke the `{name}` CLI. Commands: {string.Join(", ", shown)}{suffix}";
    }

    static string IdemTag(CommandInfo cmd)
    {
        if (cmd.Idempotent is bool b && b) return " (idempotent)";
        if (cmd.Idempotent is string s && s == "conditional") return " (conditionally idempotent)";
        return "";
    }
}
