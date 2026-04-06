package dev.acli.examples.weather;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import picocli.CommandLine;

class WeatherExampleTest {

    @BeforeEach
    void resetFavorites() {
        WeatherModel.FAVORITES.clear();
    }

    @Test
    void getLondonJson(@TempDir Path tmp) {
        CommandLine cli = WeatherMain.createCommandLine(tmp);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PrintStream prev = System.out;
        System.setOut(new PrintStream(out, true, StandardCharsets.UTF_8));
        try {
            int code = cli.execute("get", "--city", "london", "--output", "json");
            assertEquals(0, code);
            String s = out.toString(StandardCharsets.UTF_8);
            assertTrue(s.contains("\"ok\":true"), s);
            assertTrue(s.contains("\"command\":\"get\""), s);
            assertTrue(s.contains("london"), s);
        } finally {
            System.setOut(prev);
        }
    }

    @Test
    void getUnknownCityExit3(@TempDir Path tmp) {
        CommandLine cli = WeatherMain.createCommandLine(tmp);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PrintStream prev = System.out;
        System.setOut(new PrintStream(out, true, StandardCharsets.UTF_8));
        try {
            int code = cli.execute("get", "--city", "mars", "--output", "json");
            assertEquals(3, code);
            String s = out.toString(StandardCharsets.UTF_8);
            assertTrue(s.contains("\"ok\":false"), s);
            assertTrue(s.contains("NOT_FOUND"), s);
            assertTrue(s.contains("Unknown city"), s);
        } finally {
            System.setOut(prev);
        }
    }

    @Test
    void forecastInvalidDaysExit2(@TempDir Path tmp) {
        CommandLine cli = WeatherMain.createCommandLine(tmp);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PrintStream prev = System.out;
        System.setOut(new PrintStream(out, true, StandardCharsets.UTF_8));
        try {
            int code = cli.execute("forecast", "--city", "london", "--days", "9", "--output", "json");
            assertEquals(2, code);
            String s = out.toString(StandardCharsets.UTF_8);
            assertTrue(s.contains("INVALID_ARGS"), s);
        } finally {
            System.setOut(prev);
        }
    }

    @Test
    void favoriteDryRunExit9(@TempDir Path tmp) {
        CommandLine cli = WeatherMain.createCommandLine(tmp);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PrintStream prev = System.out;
        System.setOut(new PrintStream(out, true, StandardCharsets.UTF_8));
        try {
            int code =
                    cli.execute("favorite", "--city", "london", "--dry-run", "--output", "json");
            assertEquals(9, code);
            String s = out.toString(StandardCharsets.UTF_8);
            assertTrue(s.contains("\"dry_run\":true"), s);
            assertTrue(s.contains("planned_actions"), s);
        } finally {
            System.setOut(prev);
        }
    }

    @Test
    void introspectContainsToolName(@TempDir Path tmp) {
        CommandLine cli = WeatherMain.createCommandLine(tmp);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PrintStream prev = System.out;
        System.setOut(new PrintStream(out, true, StandardCharsets.UTF_8));
        try {
            int code = cli.execute("introspect", "--output", "json");
            assertEquals(0, code);
            String s = out.toString(StandardCharsets.UTF_8);
            assertTrue(s.contains("weather"), s);
            assertTrue(s.contains("get"), s);
        } finally {
            System.setOut(prev);
        }
    }

    @Test
    void refreshNdjson(@TempDir Path tmp) {
        CommandLine cli = WeatherMain.createCommandLine(tmp);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PrintStream prev = System.out;
        System.setOut(new PrintStream(out, true, StandardCharsets.UTF_8));
        try {
            int code = cli.execute("refresh", "--cities", "london");
            assertEquals(0, code);
            String s = out.toString(StandardCharsets.UTF_8);
            assertTrue(s.contains("\"type\":\"progress\""), s);
            assertTrue(s.contains("\"type\":\"result\""), s);
            assertTrue(s.contains("london"), s);
        } finally {
            System.setOut(prev);
        }
    }
}
