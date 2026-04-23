# acli-go

Go module for the [ACLI (Agent-friendly CLI) specification](../../ACLI_SPEC.md).

Core types: JSON envelopes, semantic exit codes, `.cli/` generation, `SKILL.md` ([agentskills.io](https://agentskills.io)), `App` helpers. Pair with [Cobra](https://github.com/spf13/cobra) (or any CLI router) for commands.

## Usage

```bash
cd sdks/go && go test ./...
```

```go
import "github.com/alpibrusl/acli-go"

app := acli.NewApp("mytool", "1.0.0").WithCliDir(".")
app.RegisterCommand(acli.CommandInfo{Name: "get", Description: "..."})
// Dispatch to app.HandleIntrospect, HandleVersion, HandleSkill, HandleError as needed.
```

## License

[EUPL-1.2](../../LICENSE)
