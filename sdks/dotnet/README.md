# Acli.Spec (.NET)

.NET 8 library for the [ACLI (Agent-friendly CLI) specification](../../ACLI_SPEC.md).

## Build & test

```bash
cd sdks/dotnet/Acli.Spec.Tests
dotnet test
```

## Usage

```csharp
using Acli;

var app = new AcliApp("mytool", "1.0.0") { CliDir = Environment.CurrentDirectory };
app.RegisterCommand(new CommandInfo { Name = "get", Description = "..." });
```

Pair with [System.CommandLine](https://learn.microsoft.com/en-us/dotnet/standard/commandline/) for full CLIs.

## License

[EUPL-1.2](../../LICENSE)
