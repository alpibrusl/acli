package dev.acli.picocli;

import dev.acli.AcliApp;
import dev.acli.OutputFormat;
import java.nio.file.Path;
import java.util.concurrent.Callable;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

/**
 * Picocli callables for ACLI built-in commands. Register with your root {@link
 * picocli.CommandLine}, for example:
 *
 * <pre>{@code
 * AcliApp app = new AcliApp("mytool", "1.0.0").withCliDir(Path.of("."));
 * new CommandLine(new MyRoot())
 *     .addSubcommand("introspect", new BuiltInCommands.Introspect(app))
 *     .addSubcommand("version", new BuiltInCommands.Version(app))
 *     .addSubcommand("skill", new BuiltInCommands.Skill(app));
 * }</pre>
 */
public final class BuiltInCommands {

    private BuiltInCommands() {}

    @Command(name = "introspect", description = "Output the full command tree as JSON for agent consumption.")
    public static final class Introspect implements Callable<Integer> {

        private final AcliApp app;

        @Option(names = "--acli-version", description = "Show only the ACLI spec version")
        private boolean acliVersion;

        @Option(
                names = {"-o", "--output"},
                description = "Output format. type:enum[text|json|table]",
                defaultValue = "json")
        private String output;

        public Introspect(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() {
            app.handleIntrospect(OutputFormat.parse(output), acliVersion);
            return 0;
        }
    }

    @Command(name = "version", description = "Show version information.")
    public static final class Version implements Callable<Integer> {

        private final AcliApp app;

        @Option(
                names = {"-o", "--output"},
                description = "Output format. type:enum[text|json|table]",
                defaultValue = "text")
        private String output;

        public Version(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() {
            app.handleVersion(OutputFormat.parse(output));
            return 0;
        }
    }

    @Command(name = "skill", description = "Generate a SKILLS.md file for agent bootstrapping.")
    public static final class Skill implements Callable<Integer> {

        private final AcliApp app;

        @Option(names = "--out", description = "Write skill file to this path instead of stdout")
        private Path out;

        @Option(
                names = {"-o", "--output"},
                description = "Output format. type:enum[text|json|table]",
                defaultValue = "text")
        private String output;

        public Skill(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() throws Exception {
            app.handleSkill(out, OutputFormat.parse(output));
            return 0;
        }
    }
}
