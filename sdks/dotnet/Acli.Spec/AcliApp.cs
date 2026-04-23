using System.Text.Json;

namespace Acli;

/// <summary>Application state and built-in handlers (Rust-style).</summary>
public sealed class AcliApp
{
    public string Name { get; }
    public string Version { get; }
    public CommandTree Tree { get; }
    public string? CliDir { get; set; }
    public SkillOptions SkillOptions { get; set; } = new();

    public AcliApp(string name, string version)
    {
        Name = name;
        Version = version;
        Tree = new CommandTree { Name = name, Version = version, AcliVersion = "0.1.0" };
    }

    public void RegisterCommand(CommandInfo info) => Tree.Commands.Add(info);

    public void HandleIntrospect(OutputFormat output)
    {
        if (CliFolder.NeedsUpdate(Tree, CliDir))
            CliFolder.Generate(Tree, CliDir);
        var env = Output.SuccessEnvelope("introspect", Tree, Version, null);
        Output.Emit(env, output, Console.Out, Console.Error);
    }

    public void HandleVersion(OutputFormat output)
    {
        if (output == OutputFormat.Json)
        {
            var data = new Dictionary<string, object>
            {
                ["tool"] = Name,
                ["version"] = Version,
                ["acli_version"] = "0.1.0",
            };
            var env = Output.SuccessEnvelope("version", data, Version, null);
            Output.Emit(env, output, Console.Out, Console.Error);
        }
        else
        {
            Console.WriteLine($"{Name} {Version}");
            Console.WriteLine("acli 0.1.0");
        }
        if (CliFolder.NeedsUpdate(Tree, CliDir))
            CliFolder.Generate(Tree, CliDir);
    }

    public void HandleSkill(string? outPath, OutputFormat output)
    {
        var content = Skill.Generate(Tree, null, SkillOptions);
        if (output == OutputFormat.Json)
        {
            var data = new Dictionary<string, object?> { ["content"] = content, ["path"] = outPath };
            var env = Output.SuccessEnvelope("skill", data, Version, null);
            Output.Emit(env, output, Console.Out, Console.Error);
        }
        else if (!string.IsNullOrEmpty(outPath))
        {
            Skill.Generate(Tree, outPath, SkillOptions);
            Console.WriteLine($"Skill file written to {outPath}");
        }
        else
            Console.Write(content);
    }

    public int HandleError(AcliError err)
    {
        var cmd = err.Command ?? Name;
        var env = Output.ErrorEnvelope(cmd, err.Code, err.Message, err.Hint, err.Docs, Version, null);
        Output.Emit(env, OutputFormat.Json, Console.Out, Console.Error);
        return (int)err.Code;
    }

    public static void HandleAcliVersion(OutputFormat output)
    {
        if (output == OutputFormat.Json)
            Console.WriteLine("{\"acli_version\":\"0.1.0\"}");
        else
            Console.WriteLine("acli 0.1.0");
    }
}
