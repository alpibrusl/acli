using Xunit;

namespace Acli.Spec.Tests;

public class BasicTests
{
    [Fact]
    public void ExitCode_wire_name()
    {
        Assert.Equal("INVALID_ARGS", ExitCode.InvalidArgs.WireName());
    }

    [Fact]
    public void SuggestFlag_finds_pipeline()
    {
        Assert.Equal("pipeline", SuggestFlag.Suggest("pipline", new[] { "pipeline", "env" }));
    }

    [Fact]
    public void CliFolder_generates()
    {
        var dir = Path.Combine(Path.GetTempPath(), "acli-test-" + Guid.NewGuid());
        try
        {
            var tree = new CommandTree
            {
                Name = "t",
                Version = "1.0.0",
                Commands =
                {
                    new CommandInfo
                    {
                        Name = "greet",
                        Description = "hi",
                        Examples = new List<Example> { new() { Description = "a", Invocation = "t greet" } },
                    },
                },
            };
            var root = CliFolder.Generate(tree, dir);
            Assert.True(File.Exists(Path.Combine(root, "commands.json")));
        }
        finally
        {
            try { Directory.Delete(dir, true); } catch { /* ignore */ }
        }
    }

    [Fact]
    public void App_handle_error_returns_code()
    {
        var app = new AcliApp("x", "1.0.0");
        var code = app.HandleError(new AcliError("gone") { Code = ExitCode.NotFound, Command = "run" });
        Assert.Equal(3, code);
    }

    static CommandTree SampleSkillTree() => new()
    {
        Name = "noether",
        Version = "1.0.0",
        Commands =
        {
            new CommandInfo { Name = "run", Description = "Run a pipeline", Idempotent = false },
        },
    };

    [Fact]
    public void Skill_emits_default_frontmatter()
    {
        var content = Skill.Generate(SampleSkillTree(), null);
        Assert.StartsWith("---\n", content.ReplaceLineEndings("\n"));
        var lines = content.ReplaceLineEndings("\n").Split('\n');
        Assert.Equal("name: noether", lines[1]);
        Assert.StartsWith("description: ", lines[2]);
        var closing = Array.IndexOf(lines, "---", 1);
        Assert.True(closing > 0);
        for (int i = 0; i <= closing; i++)
            Assert.False(lines[i].StartsWith("when_to_use:"));
        Assert.Equal("", lines[closing + 1]);
        Assert.Equal("# noether", lines[closing + 2]);
    }

    [Fact]
    public void Skill_emits_explicit_frontmatter()
    {
        var opts = new SkillOptions
        {
            Description = "Run Noether pipelines.",
            WhenToUse = "Use when deploying.",
        };
        var content = Skill.Generate(SampleSkillTree(), null, opts);
        Assert.Contains("description: Run Noether pipelines.", content);
        Assert.Contains("when_to_use: Use when deploying.", content);
    }

    [Fact]
    public void Skill_collapses_newlines_in_frontmatter()
    {
        var opts = new SkillOptions { Description = "Line 1\nLine 2" };
        var content = Skill.Generate(SampleSkillTree(), null, opts);
        Assert.Contains("description: Line 1 Line 2", content);
    }

    [Fact]
    public void Skill_quotes_default_description()
    {
        // Default description contains ": " (colon-space); must be quoted.
        var content = Skill.Generate(SampleSkillTree(), null).ReplaceLineEndings("\n");
        var lines = content.Split('\n');
        Assert.StartsWith("description: \"", lines[2]);
        Assert.EndsWith("\"", lines[2]);
    }

    [Fact]
    public void Skill_escapes_user_yaml_specials()
    {
        var opts = new SkillOptions
        {
            Description = "Usage: foo; see \"bar\" --- for details",
            WhenToUse = "has # and : both",
        };
        var content = Skill.Generate(SampleSkillTree(), null, opts);
        Assert.Contains("description: \"Usage: foo; see \\\"bar\\\" --- for details\"", content);
        Assert.Contains("when_to_use: \"has # and : both\"", content);
    }

    [Fact]
    public void Skill_leaves_plain_values_unquoted()
    {
        var opts = new SkillOptions { Description = "Run Noether pipelines." };
        var content = Skill.Generate(SampleSkillTree(), null, opts);
        Assert.Contains("description: Run Noether pipelines.", content);
    }
}
