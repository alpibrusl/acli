# acli-spec (Java SDK)

Java SDK for the [ACLI (Agent-friendly CLI) specification](../../ACLI_SPEC.md).

Build CLI tools that agents can discover via `--help` and `introspect`. Uses [Picocli](https://picocli.info/) for command parsing and Jackson for JSON.

## Requirements

- Java 17+
- Maven 3.9+

## Usage

```xml
<dependency>
    <groupId>dev.acli</groupId>
    <artifactId>acli-spec</artifactId>
    <version>0.4.0</version>
</dependency>
```

```java
import dev.acli.AcliApp;
import dev.acli.picocli.BuiltInCommands;
import picocli.CommandLine;

public class Main {
    public static void main(String[] args) {
        AcliApp app = new AcliApp("mytool", "1.0.0").withCliDir(java.nio.file.Path.of("."));
        // app.registerCommand(...) for each user command, then:
        CommandLine cli = new CommandLine(new MyRootCommand()); // your @Command root
        cli.addSubcommand("introspect", new BuiltInCommands.Introspect(app));
        cli.addSubcommand("version", new BuiltInCommands.Version(app));
        cli.addSubcommand("skill", new BuiltInCommands.Skill(app));
        System.exit(cli.execute(args));
    }
}
```

See Javadoc on `BuiltInCommands` for Picocli registration details.

## Build

```bash
cd sdks/java && mvn test
```

## License

[EUPL-1.2](../../LICENSE)
