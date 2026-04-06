package dev.acli.examples.weather;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import dev.acli.AcliApp;
import dev.acli.AcliError;
import dev.acli.ExitCode;
import dev.acli.Output;
import dev.acli.OutputFormat;
import dev.acli.picocli.BuiltInCommands;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

/**
 * weather — ACLI-compliant weather CLI (Java port of {@code examples/weather/weather.py}).
 */
public final class WeatherMain {

    private WeatherMain() {}

    public static void main(String[] args) {
        System.exit(createCommandLine().execute(args));
    }

    /** Builds the full Picocli tree (used by tests). */
    public static CommandLine createCommandLine() {
        return createCommandLine(java.nio.file.Path.of(".").toAbsolutePath());
    }

    public static CommandLine createCommandLine(java.nio.file.Path cliDir) {
        AcliApp app = new AcliApp("weather", "1.0.0").withCliDir(cliDir);
        WeatherMeta.register(app);

        CommandLine root = new CommandLine(new WeatherTop());
        root.setCommandName("weather");
        root.addSubcommand("get", new GetCmd(app));
        root.addSubcommand("forecast", new ForecastCmd(app));
        root.addSubcommand("alerts", new AlertsCmd(app));
        root.addSubcommand("favorite", new FavoriteCmd(app));
        root.addSubcommand("refresh", new RefreshCmd(app));
        root.addSubcommand("introspect", new BuiltInCommands.Introspect(app));
        root.addSubcommand("version", new BuiltInCommands.Version(app));
        root.addSubcommand("skill", new BuiltInCommands.Skill(app));
        return root;
    }

    @Command(
            name = "weather",
            mixinStandardHelpOptions = true,
            version = "weather 1.0.0",
            description = "ACLI weather CLI for agent consumption.")
    static class WeatherTop implements Callable<Integer> {
        @Override
        public Integer call() {
            CommandLine.usage(this, System.out);
            return 0;
        }
    }

    @Command(name = "get", description = "Get current weather for a city.")
    static class GetCmd implements Callable<Integer> {

        private final AcliApp app;

        @Option(names = "--city", required = true, description = "City name (lowercase, hyphenated). type:string")
        private String city;

        @Option(
                names = "--units",
                defaultValue = "metric",
                description = "Unit system. type:enum[metric|imperial]")
        private String units;

        @Option(
                names = {"-o", "--output"},
                defaultValue = "text",
                description = "Output format. type:enum[text|json|table]")
        private String output;

        GetCmd(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() {
            try {
                long start = System.currentTimeMillis();
                city = WeatherModel.normalizeCity(city);
                WeatherModel.requireKnownCity(city, "get", ".cli/examples/get.sh");
                ObjectNode data = WeatherModel.getWeather(city);
                if ("imperial".equals(units)) {
                    data = WeatherModel.getWeatherImperial(data);
                }
                JsonNode env = Output.successEnvelope("get", data, "1.0.0", start);
                Output.emit(env, OutputFormat.parse(output));
                return 0;
            } catch (AcliError e) {
                return app.handleError(e);
            }
        }
    }

    @Command(name = "forecast")
    static class ForecastCmd implements Callable<Integer> {

        private final AcliApp app;

        @Option(names = "--city", required = true, description = "City name (lowercase, hyphenated). type:string")
        private String city;

        @Option(names = "--days", defaultValue = "3", description = "Number of forecast days (1-7). type:int")
        private int days;

        @Option(
                names = {"-o", "--output"},
                defaultValue = "text",
                description = "Output format. type:enum[text|json|table]")
        private String output;

        ForecastCmd(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() {
            try {
                long start = System.currentTimeMillis();
                city = WeatherModel.normalizeCity(city);
                WeatherModel.requireKnownCity(city, "forecast", null);
                if (days < 1 || days > 7) {
                    throw new AcliError(
                            "Days must be between 1 and 7, got " + days,
                            ExitCode.INVALID_ARGS,
                            "Use --days with a value from 1 to 7",
                            null,
                            "forecast");
                }
                JsonNode data = WeatherModel.forecast(city, days);
                JsonNode env = Output.successEnvelope("forecast", data, "1.0.0", start);
                Output.emit(env, OutputFormat.parse(output));
                return 0;
            } catch (AcliError e) {
                return app.handleError(e);
            }
        }
    }

    @Command(name = "alerts")
    static class AlertsCmd implements Callable<Integer> {

        private final AcliApp app;

        @Option(names = "--city", description = "Filter alerts by city (optional). type:string")
        private String city = "";

        @Option(
                names = {"-o", "--output"},
                defaultValue = "text",
                description = "Output format. type:enum[text|json|table]")
        private String output;

        AlertsCmd(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() {
            try {
                long start = System.currentTimeMillis();
                String filter = null;
                if (city != null && !city.isEmpty()) {
                    String c = WeatherModel.normalizeCity(city);
                    if (!WeatherModel.CITIES.containsKey(c)) {
                        throw new AcliError(
                                "Unknown city: '" + c + "'",
                                ExitCode.NOT_FOUND,
                                null,
                                null,
                                "alerts");
                    }
                    filter = c;
                }
                JsonNode data = WeatherModel.alertsJson(filter);
                JsonNode env = Output.successEnvelope("alerts", data, "1.0.0", start);
                Output.emit(env, OutputFormat.parse(output));
                return 0;
            } catch (AcliError e) {
                return app.handleError(e);
            }
        }
    }

    @Command(name = "favorite")
    static class FavoriteCmd implements Callable<Integer> {

        private final AcliApp app;

        @Option(names = "--city", required = true, description = "City to add to favorites. type:string")
        private String city;

        @Option(names = "--dry-run", description = "Preview without saving. type:bool")
        private boolean dryRun;

        @Option(
                names = {"-o", "--output"},
                defaultValue = "text",
                description = "Output format. type:enum[text|json|table]")
        private String output;

        FavoriteCmd(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() {
            try {
                long start = System.currentTimeMillis();
                city = WeatherModel.normalizeCity(city);
                WeatherModel.requireKnownCity(city, "favorite", null);

                if (dryRun) {
                    ArrayNode actions = Output.mapper().createArrayNode();
                    ObjectNode act = Output.mapper().createObjectNode();
                    act.put("action", "add_favorite");
                    act.put("target", city);
                    act.put("reversible", true);
                    act.put("already_exists", WeatherModel.FAVORITES.contains(city));
                    actions.add(act);
                    JsonNode env = Output.dryRunEnvelope("favorite", actions, "1.0.0", start);
                    Output.emit(env, OutputFormat.parse(output));
                    return ExitCode.DRY_RUN.code();
                }

                if (!WeatherModel.FAVORITES.contains(city)) {
                    WeatherModel.FAVORITES.add(city);
                }
                ObjectNode data = Output.mapper().createObjectNode();
                data.put("city", city);
                ArrayNode fav = Output.mapper().createArrayNode();
                for (String f : WeatherModel.FAVORITES) {
                    fav.add(f);
                }
                data.set("favorites", fav);
                JsonNode env = Output.successEnvelope("favorite", data, "1.0.0", start);
                Output.emit(env, OutputFormat.parse(output));
                return 0;
            } catch (AcliError e) {
                return app.handleError(e);
            }
        }
    }

    @Command(name = "refresh")
    static class RefreshCmd implements Callable<Integer> {

        private final AcliApp app;

        @Option(
                names = "--cities",
                description = "Comma-separated city names to refresh (default: all). type:string")
        private String cities = "";

        @Option(names = "--dry-run", description = "Describe actions without executing. type:bool", hidden = true)
        @SuppressWarnings("unused")
        private boolean dryRun;

        @Option(names = "--output", description = "Output format (not used for NDJSON stream).", hidden = true)
        @SuppressWarnings("unused")
        private String output = "text";

        RefreshCmd(AcliApp app) {
            this.app = app;
        }

        @Override
        public Integer call() throws InterruptedException {
            try {
                List<String> targetCities = new ArrayList<>();
                if (cities != null && !cities.isEmpty()) {
                    for (String part : cities.split(",")) {
                        String c = part.trim().toLowerCase();
                        if (!c.isEmpty()) {
                            targetCities.add(c);
                        }
                    }
                } else {
                    targetCities.addAll(WeatherModel.sortedCities());
                }

                for (String c : targetCities) {
                    if (!WeatherModel.CITIES.containsKey(c)) {
                        throw new AcliError(
                                "Unknown city: '" + c + "'", ExitCode.NOT_FOUND, null, null, "refresh");
                    }
                }

                for (String c : targetCities) {
                    Output.emitProgress(System.out, "refresh", "running", "Fetching data for " + c);
                    Thread.sleep(10);
                }
                ObjectNode result = Output.mapper().createObjectNode();
                ArrayNode arr = Output.mapper().createArrayNode();
                for (String c : targetCities) {
                    arr.add(c);
                }
                result.set("cities_refreshed", arr);
                result.put("count", targetCities.size());
                Output.emitResult(System.out, result, true);
                return 0;
            } catch (AcliError e) {
                return app.handleError(e);
            }
        }
    }
}
