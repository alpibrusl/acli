package dev.acli;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** Generate and maintain the {@code .cli/} reference folder per ACLI spec §1.3. */
public final class CliFolder {

    private static final ObjectMapper MAPPER = Output.mapper();

    private CliFolder() {}

    public static Path generateCliFolder(CommandTree tree, Path targetDir) throws IOException {
        Path root = (targetDir != null ? targetDir : Path.of(".")).resolve(".cli");
        Files.createDirectories(root.resolve("examples"));
        Files.createDirectories(root.resolve("schemas"));

        String json = MAPPER.writerWithDefaultPrettyPrinter().writeValueAsString(tree) + "\n";
        Files.writeString(root.resolve("commands.json"), json, StandardCharsets.UTF_8);

        writeReadme(root, tree);
        writeExamples(root, tree);

        Path changelog = root.resolve("changelog.md");
        if (!Files.exists(changelog)) {
            String v = tree.getVersion() != null ? tree.getVersion() : "0.0.0";
            Files.writeString(
                    changelog,
                    "# Changelog\n\n## " + v + "\n\n- Initial release\n",
                    StandardCharsets.UTF_8);
        }
        return root;
    }

    public static boolean needsUpdate(CommandTree tree, Path targetDir) {
        Path root = (targetDir != null ? targetDir : Path.of(".")).resolve(".cli");
        Path commandsFile = root.resolve("commands.json");
        if (!Files.exists(commandsFile)) {
            return true;
        }
        try {
            CommandTree existing =
                    MAPPER.readValue(commandsFile.toFile(), CommandTree.class);
            String a = MAPPER.writeValueAsString(existing);
            String b = MAPPER.writeValueAsString(tree);
            return !a.equals(b);
        } catch (IOException e) {
            return true;
        }
    }

    private static void writeReadme(Path cliDir, CommandTree tree) throws IOException {
        List<String> lines = new ArrayList<>();
        String name = tree.getName() != null ? tree.getName() : "tool";
        String version = tree.getVersion() != null ? tree.getVersion() : "0.0.0";
        lines.add("# " + name);
        lines.add("");
        lines.add("Version: " + version);
        lines.add("ACLI version: " + tree.getAcliVersion());
        lines.add("");
        lines.add("## Commands");
        lines.add("");
        for (CommandInfo cmd : tree.getCommands()) {
            lines.add("### " + cmd.getName());
            lines.add("");
            lines.add(cmd.getDescription() != null ? cmd.getDescription() : "");
            lines.add("");
            if (cmd.getIdempotent() != null) {
                lines.add("Idempotent: " + cmd.getIdempotent());
                lines.add("");
            }
        }
        Files.writeString(
                cliDir.resolve("README.md"), String.join("\n", lines) + "\n", StandardCharsets.UTF_8);
    }

    private static void writeExamples(Path cliDir, CommandTree tree) throws IOException {
        for (CommandInfo cmd : tree.getCommands()) {
            List<Example> examples = cmd.getExamples();
            if (examples == null || examples.isEmpty()) {
                continue;
            }
            List<String> lines = new ArrayList<>();
            lines.add("#!/usr/bin/env bash");
            lines.add("# Examples for: " + cmd.getName());
            lines.add("");
            for (Example ex : examples) {
                lines.add("# " + ex.description());
                lines.add(ex.invocation());
                lines.add("");
            }
            Files.writeString(
                    cliDir.resolve("examples").resolve(cmd.getName() + ".sh"),
                    String.join("\n", lines) + "\n",
                    StandardCharsets.UTF_8);
        }
    }
}
