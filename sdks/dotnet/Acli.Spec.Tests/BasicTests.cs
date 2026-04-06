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
}
