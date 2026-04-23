package dev.acli;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/**
 * Generate SKILL.md files from ACLI command trees.
 *
 * <p>Emits a file conforming to the agentskills.io open standard
 * (<a href="https://agentskills.io">agentskills.io</a>): YAML frontmatter
 * ({@code name}, {@code description}, optional {@code when_to_use}) followed
 * by the ACLI command reference body.
 */
public final class Skill {

    private static final Set<String> BUILTIN =
            Set.of("introspect", "version", "skill");

    /** Options forwarded into the SKILL.md frontmatter. */
    public record Options(String description, String whenToUse) {
        public static Options empty() {
            return new Options(null, null);
        }
    }

    private Skill() {}

    public static String generateSkill(CommandTree tree) throws IOException {
        return generateSkill(tree, null, Options.empty());
    }

    public static String generateSkill(CommandTree tree, Path targetPath) throws IOException {
        return generateSkill(tree, targetPath, Options.empty());
    }

    /** Generate SKILL.md content with caller-supplied frontmatter options. */
    public static String generateSkill(CommandTree tree, Path targetPath, Options opts)
            throws IOException {
        String name = tree.getName();
        String version = tree.getVersion();
        List<String> lines = new ArrayList<>();

        List<CommandInfo> userCommands = new ArrayList<>();
        for (CommandInfo c : tree.getCommands()) {
            if (!BUILTIN.contains(c.getName())) {
                userCommands.add(c);
            }
        }

        String description =
                opts.description() != null && !opts.description().isEmpty()
                        ? collapseWs(opts.description())
                        : defaultDescription(name, userCommands);

        lines.add("---");
        lines.add("name: " + name);
        lines.add("description: " + description);
        if (opts.whenToUse() != null && !opts.whenToUse().isEmpty()) {
            lines.add("when_to_use: " + collapseWs(opts.whenToUse()));
        }
        lines.add("---");
        lines.add("");

        lines.add("# " + name);
        lines.add("");
        lines.add("> Auto-generated skill file for `" + name + "` v" + version);
        lines.add("> Re-generate with: `" + name + " skill` or `acli skill --bin " + name + "`");
        lines.add("");
        lines.add("## Available commands");
        lines.add("");

        for (CommandInfo cmd : userCommands) {
            String tag = idemTag(cmd);
            lines.add("- `" + name + " " + cmd.getName() + "` — " + cmd.getDescription() + tag);
        }
        lines.add("");

        for (CommandInfo cmd : userCommands) {
            lines.add("## `" + name + " " + cmd.getName() + "`");
            lines.add("");
            if (cmd.getDescription() != null && !cmd.getDescription().isEmpty()) {
                lines.add(cmd.getDescription());
                lines.add("");
            }
            if (cmd.getOptions() != null && !cmd.getOptions().isEmpty()) {
                lines.add("### Options");
                lines.add("");
                for (ParamInfo opt : cmd.getOptions()) {
                    String def =
                            opt.defaultValue() != null
                                    ? " [default: " + opt.defaultValue() + "]"
                                    : "";
                    String optName = opt.name().replace('_', '-');
                    lines.add(
                            "- `--"
                                    + optName
                                    + "` ("
                                    + opt.paramType()
                                    + ") — "
                                    + opt.description()
                                    + def);
                }
                lines.add("");
            }
            if (cmd.getArguments() != null && !cmd.getArguments().isEmpty()) {
                lines.add("### Arguments");
                lines.add("");
                for (ParamInfo arg : cmd.getArguments()) {
                    String req =
                            Boolean.TRUE.equals(arg.required()) ? "required" : "optional";
                    lines.add(
                            "- `"
                                    + arg.name()
                                    + "` ("
                                    + arg.paramType()
                                    + ", "
                                    + req
                                    + ") — "
                                    + arg.description());
                }
                lines.add("");
            }
            if (cmd.getExamples() != null && !cmd.getExamples().isEmpty()) {
                lines.add("### Examples");
                lines.add("");
                for (Example ex : cmd.getExamples()) {
                    lines.add("```bash");
                    lines.add("# " + ex.description());
                    lines.add(ex.invocation());
                    lines.add("```");
                    lines.add("");
                }
            }
            if (cmd.getSeeAlso() != null && !cmd.getSeeAlso().isEmpty()) {
                StringBuilder refs = new StringBuilder();
                for (String s : cmd.getSeeAlso()) {
                    if (refs.length() > 0) {
                        refs.append(", ");
                    }
                    refs.append("`").append(name).append(" ").append(s).append("`");
                }
                lines.add("**See also:** " + refs);
                lines.add("");
            }
        }

        lines.add("## Output format");
        lines.add("");
        lines.add(
                "All commands support `--output json|text|table`. When using `--output json`, "
                        + "responses follow a standard envelope:");
        lines.add("");
        lines.add("```json");
        lines.add(
                "{\"ok\": true, \"command\": \"...\", \"data\": {...}, \"meta\": {\"duration_ms\": ..., \"version\": \"...\"}}");
        lines.add("```");
        lines.add("");
        lines.add("## Exit codes");
        lines.add("");
        lines.add("| Code | Meaning | Action |");
        lines.add("|------|---------|--------|");
        lines.add("| 0 | Success | Proceed |");
        lines.add("| 2 | Invalid arguments | Correct and retry |");
        lines.add("| 3 | Not found | Check inputs |");
        lines.add("| 5 | Conflict | Resolve conflict |");
        lines.add("| 8 | Precondition failed | Fix precondition |");
        lines.add("| 9 | Dry-run completed | Review and confirm |");
        lines.add("");
        lines.add("## Further discovery");
        lines.add("");
        lines.add("- `" + name + " --help` — full help for any command");
        lines.add("- `" + name + " introspect` — machine-readable command tree (JSON)");
        lines.add("- `.cli/README.md` — persistent reference (survives context resets)");
        lines.add("");

        String content = String.join("\n", lines);

        if (targetPath != null) {
            Path parent = targetPath.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.writeString(targetPath, content, StandardCharsets.UTF_8);
        }

        return content;
    }

    private static String collapseWs(String s) {
        return s.trim().replaceAll("\\s+", " ");
    }

    private static String defaultDescription(String name, List<CommandInfo> userCommands) {
        if (userCommands.isEmpty()) {
            return "Invoke the `" + name + "` CLI.";
        }
        int shown = Math.min(4, userCommands.size());
        StringBuilder sb = new StringBuilder("Invoke the `").append(name).append("` CLI. Commands: ");
        for (int i = 0; i < shown; i++) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append(userCommands.get(i).getName());
        }
        if (userCommands.size() > 4) {
            sb.append("…");
        }
        return sb.toString();
    }

    private static String idemTag(CommandInfo cmd) {
        var id = cmd.getIdempotent();
        if (id == null) {
            return "";
        }
        if (id.isBoolean() && id.booleanValue()) {
            return " (idempotent)";
        }
        if (id.isTextual() && "conditional".equals(id.asText())) {
            return " (conditionally idempotent)";
        }
        return "";
    }
}
