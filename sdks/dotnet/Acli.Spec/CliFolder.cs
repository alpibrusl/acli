using System.Text.Json;

namespace Acli;

public static class CliFolder
{
    public static string Generate(CommandTree tree, string? targetDir)
    {
        var root = string.IsNullOrEmpty(targetDir)
            ? Path.Combine(".cli")
            : Path.Combine(targetDir, ".cli");
        Directory.CreateDirectory(Path.Combine(root, "examples"));
        Directory.CreateDirectory(Path.Combine(root, "schemas"));

        var json = JsonSerializer.Serialize(tree, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(Path.Combine(root, "commands.json"), json + "\n");
        WriteReadme(root, tree);
        WriteExamples(root, tree);
        var changelog = Path.Combine(root, "changelog.md");
        if (!File.Exists(changelog))
            File.WriteAllText(changelog, $"# Changelog\n\n## {tree.Version}\n\n- Initial release\n");
        return root;
    }

    public static bool NeedsUpdate(CommandTree tree, string? targetDir)
    {
        var root = string.IsNullOrEmpty(targetDir)
            ? ".cli"
            : Path.Combine(targetDir, ".cli");
        var p = Path.Combine(root, "commands.json");
        if (!File.Exists(p)) return true;
        try
        {
            var existing = File.ReadAllText(p);
            var cur = JsonSerializer.Serialize(tree, new JsonSerializerOptions { WriteIndented = false });
            var round = JsonSerializer.Serialize(
                JsonSerializer.Deserialize<CommandTree>(existing),
                new JsonSerializerOptions { WriteIndented = false });
            return cur != round;
        }
        catch
        {
            return true;
        }
    }

    static void WriteReadme(string cliDir, CommandTree tree)
    {
        var lines = new List<string> { $"# {tree.Name}", "", $"Version: {tree.Version}", $"ACLI version: {tree.AcliVersion}", "", "## Commands", "" };
        foreach (var cmd in tree.Commands)
        {
            lines.Add($"### {cmd.Name}");
            lines.Add("");
            lines.Add(cmd.Description);
            lines.Add("");
            if (cmd.Idempotent != null)
            {
                lines.Add($"Idempotent: {cmd.Idempotent}");
                lines.Add("");
            }
        }
        File.WriteAllText(Path.Combine(cliDir, "README.md"), string.Join("\n", lines) + "\n");
    }

    static void WriteExamples(string cliDir, CommandTree tree)
    {
        foreach (var cmd in tree.Commands)
        {
            if (cmd.Examples == null || cmd.Examples.Count == 0) continue;
            var lines = new List<string> { "#!/usr/bin/env bash", $"# Examples for: {cmd.Name}", "" };
            foreach (var ex in cmd.Examples)
            {
                lines.Add($"# {ex.Description}");
                lines.Add(ex.Invocation);
                lines.Add("");
            }
            File.WriteAllText(Path.Combine(cliDir, "examples", cmd.Name + ".sh"), string.Join("\n", lines) + "\n");
        }
    }
}
