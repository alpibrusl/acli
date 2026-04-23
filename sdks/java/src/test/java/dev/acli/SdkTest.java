package dev.acli;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import dev.acli.picocli.BuiltInCommands;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import picocli.CommandLine;
import picocli.CommandLine.Command;

class SdkTest {

    @Test
    void exitCodesMatchSpec() {
        assertEquals(0, ExitCode.SUCCESS.code());
        assertEquals(9, ExitCode.DRY_RUN.code());
        assertEquals("INVALID_ARGS", ExitCode.INVALID_ARGS.wireName());
    }

    @Test
    void suggestFlagFindsCloseMatch() {
        assertEquals("pipeline", SuggestFlag.suggest("pipline", List.of("pipeline", "env")));
    }

    @Test
    void successEnvelopeHasShape() {
        JsonNode data = Output.mapper().createObjectNode().put("x", 1);
        JsonNode env = Output.successEnvelope("run", data, "1.0.0", null);
        assertTrue(env.path("ok").asBoolean());
        assertEquals("run", env.path("command").asText());
        assertEquals(1, env.path("data").path("x").asInt());
        assertEquals("1.0.0", env.path("meta").path("version").asText());
    }

    @Test
    void errorEnvelopeHasShape() {
        JsonNode env =
                Output.errorEnvelope(
                        "run",
                        ExitCode.INVALID_ARGS,
                        "bad",
                        "hint",
                        "docs",
                        "1.0.0",
                        null);
        assertFalse(env.path("ok").asBoolean());
        assertEquals("INVALID_ARGS", env.path("error").path("code").asText());
    }

    @Test
    void cliFolderGenerated(@TempDir Path tmp) throws Exception {
        CommandTree tree = new CommandTree("t", "1.0.0");
        CommandInfo c = new CommandInfo("greet", "Hi");
        c.setExamples(
                List.of(new Example("one", "t greet"), new Example("two", "t greet --x")));
        tree.addCommand(c);

        Path root = CliFolder.generateCliFolder(tree, tmp);
        assertTrue(Files.exists(root.resolve("commands.json")));
        assertTrue(Files.exists(root.resolve("README.md")));
        assertTrue(Files.exists(root.resolve("examples/greet.sh")));
    }

    @Test
    void skillExcludesBuiltins() throws Exception {
        CommandTree tree = new CommandTree("n", "1.0.0");
        tree.addCommand(new CommandInfo("run", "Run things"));
        tree.addCommand(new CommandInfo("introspect", "Tree"));
        String md = Skill.generateSkill(tree);
        assertTrue(md.contains("`n run`"));
        String afterAvailable = md.split("## Available commands", 2)[1];
        String availableSection = afterAvailable.split("##", 2)[0];
        assertFalse(availableSection.contains("`n introspect`"));
    }

    @Test
    void skillEmitsDefaultFrontmatter() throws Exception {
        CommandTree tree = new CommandTree("noether", "1.0.0");
        tree.addCommand(new CommandInfo("run", "Run a pipeline"));
        String md = Skill.generateSkill(tree);
        assertTrue(md.startsWith("---\n"), "expected frontmatter, got: " + md.substring(0, 40));
        String[] lines = md.split("\n");
        assertEquals("name: noether", lines[1]);
        assertTrue(lines[2].startsWith("description: "), "got: " + lines[2]);
        int closing = -1;
        for (int i = 1; i < lines.length; i++) {
            if ("---".equals(lines[i])) {
                closing = i;
                break;
            }
        }
        assertTrue(closing > 0, "no closing ---");
        for (int i = 0; i <= closing; i++) {
            assertFalse(lines[i].startsWith("when_to_use:"), "unexpected when_to_use");
        }
        assertEquals("", lines[closing + 1]);
        assertEquals("# noether", lines[closing + 2]);
    }

    @Test
    void skillEmitsExplicitFrontmatter() throws Exception {
        CommandTree tree = new CommandTree("noether", "1.0.0");
        tree.addCommand(new CommandInfo("run", "Run"));
        Skill.Options opts = new Skill.Options("Run Noether pipelines.", "Use when deploying.");
        String md = Skill.generateSkill(tree, null, opts);
        assertTrue(md.contains("description: Run Noether pipelines."), md);
        assertTrue(md.contains("when_to_use: Use when deploying."), md);
    }

    @Test
    void skillCollapsesNewlines() throws Exception {
        CommandTree tree = new CommandTree("noether", "1.0.0");
        tree.addCommand(new CommandInfo("run", "Run"));
        Skill.Options opts = new Skill.Options("Line 1\nLine 2", null);
        String md = Skill.generateSkill(tree, null, opts);
        assertTrue(md.contains("description: Line 1 Line 2"), md);
    }

    @Test
    void skillQuotesDefaultDescription() throws Exception {
        // Default description contains ": " (colon-space); must be quoted.
        CommandTree tree = new CommandTree("noether", "1.0.0");
        tree.addCommand(new CommandInfo("run", "Run"));
        String md = Skill.generateSkill(tree);
        String[] lines = md.split("\n");
        assertTrue(lines[2].startsWith("description: \""), lines[2]);
        assertTrue(lines[2].endsWith("\""), lines[2]);
    }

    @Test
    void skillEscapesUserYamlSpecials() throws Exception {
        CommandTree tree = new CommandTree("noether", "1.0.0");
        tree.addCommand(new CommandInfo("run", "Run"));
        Skill.Options opts = new Skill.Options(
                "Usage: foo; see \"bar\" --- for details",
                "has # and : both");
        String md = Skill.generateSkill(tree, null, opts);
        assertTrue(md.contains("description: \"Usage: foo; see \\\"bar\\\" --- for details\""), md);
        assertTrue(md.contains("when_to_use: \"has # and : both\""), md);
    }

    @Test
    void skillLeavesPlainValuesUnquoted() throws Exception {
        CommandTree tree = new CommandTree("noether", "1.0.0");
        tree.addCommand(new CommandInfo("run", "Run"));
        Skill.Options opts = new Skill.Options("Run Noether pipelines.", null);
        String md = Skill.generateSkill(tree, null, opts);
        assertTrue(md.contains("description: Run Noether pipelines."), md);
    }

    @Test
    void acliAppHandleIntrospectWritesJson(@TempDir Path tmp) {
        AcliApp app = new AcliApp("myapp", "0.1.0").withCliDir(tmp);
        CommandInfo greet = new CommandInfo("greet", "Say hi");
        greet.setOptions(
                List.of(
                        new ParamInfo("output", "string", "format", null, null)));
        app.registerCommand(greet);

        ByteArrayOutputStream bout = new ByteArrayOutputStream();
        PrintStream orig = System.out;
        System.setOut(new PrintStream(bout, true, StandardCharsets.UTF_8));
        try {
            app.handleIntrospect(OutputFormat.json, false);
        } finally {
            System.setOut(orig);
        }

        String out = bout.toString(StandardCharsets.UTF_8);
        assertTrue(out.contains("myapp"), out);
    }

    @Command(name = "testcli", description = "test")
    static class TestRoot implements java.util.concurrent.Callable<Integer> {
        @Override
        public Integer call() {
            return 0;
        }
    }

    @Test
    void picocliIntrospectSubcommand(@TempDir Path tmp) {
        AcliApp app = new AcliApp("cli", "1.0.0").withCliDir(tmp);
        CommandLine root = new CommandLine(new TestRoot());
        root.addSubcommand("introspect", new BuiltInCommands.Introspect(app));
        PrintStream orig = System.out;
        System.setOut(new PrintStream(OutputStream.nullOutputStream(), true, StandardCharsets.UTF_8));
        try {
            int exit = root.execute("introspect", "--output", "json");
            assertEquals(0, exit);
        } finally {
            System.setOut(orig);
        }
    }
}
