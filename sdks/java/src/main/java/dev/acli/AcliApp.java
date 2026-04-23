package dev.acli;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * ACLI application state: command tree, built-in handlers, and error emission.
 *
 * <p>Wire your CLI (e.g. Picocli) to call the {@code handle*} methods for built-ins, or use {@link
 * dev.acli.picocli.BuiltInCommands} to register default subcommands.
 */
public final class AcliApp {

    private final String name;
    private final String version;
    private final CommandTree tree;
    private java.nio.file.Path cliDir;
    private Skill.Options skillOptions = Skill.Options.empty();

    public AcliApp(String name, String version) {
        this.name = name;
        this.version = version;
        this.tree = new CommandTree(name, version);
    }

    /** Configure the SKILL.md frontmatter written by {@link #handleSkill}. */
    public AcliApp withSkillOptions(Skill.Options opts) {
        this.skillOptions = opts != null ? opts : Skill.Options.empty();
        return this;
    }

    public String getName() {
        return name;
    }

    public String getVersion() {
        return version;
    }

    public java.nio.file.Path getCliDir() {
        return cliDir;
    }

    public AcliApp withCliDir(java.nio.file.Path cliDir) {
        this.cliDir = cliDir;
        return this;
    }

    /** Register a command for introspection (call once per user command). */
    public void registerCommand(CommandInfo info) {
        tree.addCommand(info);
    }

    public CommandTree getCommandTree() {
        return tree;
    }

    /** Built-in: {@code introspect}. */
    public void handleIntrospect(OutputFormat output, boolean acliVersionOnly) {
        if (acliVersionOnly) {
            if (output == OutputFormat.json) {
                ObjectNode n = JsonNodeFactory.instance.objectNode();
                n.put("acli_version", "0.1.0");
                Output.emit(n, OutputFormat.json);
            } else {
                System.out.println("acli 0.1.0");
            }
            return;
        }

        try {
            if (CliFolder.needsUpdate(tree, cliDir)) {
                CliFolder.generateCliFolder(tree, cliDir);
            }
        } catch (java.io.IOException e) {
            throw new RuntimeException(e);
        }

        JsonNode data = Output.mapper().valueToTree(tree);
        JsonNode envelope = Output.successEnvelope("introspect", data, version, null);
        Output.emit(envelope, output);
    }

    /** Built-in: {@code version}. */
    public void handleVersion(OutputFormat output) {
        if (output == OutputFormat.json) {
            ObjectNode data = JsonNodeFactory.instance.objectNode();
            data.put("tool", name);
            data.put("version", version);
            data.put("acli_version", "0.1.0");
            JsonNode envelope = Output.successEnvelope("version", data, version, null);
            Output.emit(envelope, output);
        } else {
            System.out.println(name + " " + version);
            System.out.println("acli 0.1.0");
        }

        try {
            if (CliFolder.needsUpdate(tree, cliDir)) {
                CliFolder.generateCliFolder(tree, cliDir);
            }
        } catch (java.io.IOException e) {
            throw new RuntimeException(e);
        }
    }

    /** Built-in: {@code skill} — emits SKILL.md per agentskills.io. */
    public void handleSkill(java.nio.file.Path outPath, OutputFormat output) throws java.io.IOException {
        String content = Skill.generateSkill(tree, outPath, skillOptions);

        if (output == OutputFormat.json) {
            ObjectNode data = JsonNodeFactory.instance.objectNode();
            if (outPath != null) {
                data.put("path", outPath.toString());
            } else {
                data.putNull("path");
            }
            data.put("content", content);
            JsonNode envelope = Output.successEnvelope("skill", data, version, null);
            Output.emit(envelope, output);
        } else if (outPath != null) {
            System.out.println("Skill file written to " + outPath);
        } else {
            System.out.print(content);
        }
    }

    /** Emit JSON error envelope and return the process exit code. */
    public int handleError(AcliError err) {
        String cmd = err.getCommand() != null ? err.getCommand() : name;
        JsonNode envelope =
                Output.errorEnvelope(
                        cmd,
                        err.getCode(),
                        err.getMessage(),
                        err.getHint(),
                        err.getDocs(),
                        version,
                        null);
        Output.emit(envelope, OutputFormat.json);
        return err.getCode().code();
    }
}
