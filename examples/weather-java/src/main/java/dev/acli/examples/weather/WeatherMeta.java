package dev.acli.examples.weather;

import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import dev.acli.AcliApp;
import dev.acli.CommandInfo;
import dev.acli.Example;
import dev.acli.ParamInfo;
import java.util.List;

/** Registers {@link CommandInfo} for introspection (mirrors @acli_command metadata in weather.py). */
public final class WeatherMeta {

    private WeatherMeta() {}

    public static void register(AcliApp app) {
        JsonNodeFactory nf = JsonNodeFactory.instance;

        CommandInfo get = new CommandInfo("get", firstLine(Help.GET));
        get.setIdempotent(nf.booleanNode(true));
        get.setSeeAlso(List.of("forecast", "alerts"));
        get.setExamples(
                List.of(
                        new Example("Get weather for London", "weather get --city london"),
                        new Example(
                                "Get weather for Tokyo in JSON",
                                "weather get --city tokyo --output json")));
        get.setOptions(
                List.of(
                        new ParamInfo("city", "string", "City name (lowercase, hyphenated). type:string", null, null),
                        new ParamInfo("units", "string", "Unit system. type:enum[metric|imperial]", null, null),
                        new ParamInfo(
                                "output",
                                "OutputFormat",
                                "Output format. type:enum[text|json|table]",
                                null,
                                null)));
        app.registerCommand(get);

        CommandInfo forecast = new CommandInfo("forecast", firstLine(Help.FORECAST));
        forecast.setIdempotent(nf.booleanNode(true));
        forecast.setSeeAlso(List.of("get", "alerts"));
        forecast.setExamples(
                List.of(
                        new Example(
                                "Get 3-day forecast for Paris", "weather forecast --city paris --days 3"),
                        new Example(
                                "Get 7-day forecast in JSON",
                                "weather forecast --city london --days 7 --output json")));
        forecast.setOptions(
                List.of(
                        new ParamInfo("city", "string", "City name (lowercase, hyphenated). type:string", null, null),
                        new ParamInfo("days", "int", "Number of forecast days (1-7). type:int", null, null),
                        new ParamInfo(
                                "output",
                                "OutputFormat",
                                "Output format. type:enum[text|json|table]",
                                null,
                                null)));
        app.registerCommand(forecast);

        CommandInfo alerts = new CommandInfo("alerts", firstLine(Help.ALERTS));
        alerts.setIdempotent(nf.booleanNode(true));
        alerts.setSeeAlso(List.of("get", "forecast"));
        alerts.setExamples(
                List.of(
                        new Example("Check all active alerts", "weather alerts"),
                        new Example("Check alerts for Tokyo", "weather alerts --city tokyo")));
        alerts.setOptions(
                List.of(
                        new ParamInfo(
                                "city",
                                "string",
                                "Filter alerts by city (optional). type:string",
                                null,
                                null),
                        new ParamInfo(
                                "output",
                                "OutputFormat",
                                "Output format. type:enum[text|json|table]",
                                null,
                                null)));
        app.registerCommand(alerts);

        CommandInfo favorite = new CommandInfo("favorite", firstLine(Help.FAVORITE));
        favorite.setIdempotent(nf.textNode("conditional"));
        favorite.setSeeAlso(List.of("get"));
        favorite.setExamples(
                List.of(
                        new Example("Add London to favorites", "weather favorite --city london"),
                        new Example(
                                "Dry-run adding Paris", "weather favorite --city paris --dry-run")));
        favorite.setOptions(
                List.of(
                        new ParamInfo("city", "string", "City to add to favorites. type:string", null, null),
                        new ParamInfo(
                                "dry_run",
                                "bool",
                                "Preview without saving. type:bool",
                                null,
                                null),
                        new ParamInfo(
                                "output",
                                "OutputFormat",
                                "Output format. type:enum[text|json|table]",
                                null,
                                null)));
        app.registerCommand(favorite);

        CommandInfo refresh = new CommandInfo("refresh", firstLine(Help.REFRESH));
        refresh.setIdempotent(nf.booleanNode(false));
        refresh.setSeeAlso(List.of("get", "forecast"));
        refresh.setExamples(
                List.of(
                        new Example("Refresh all cities", "weather refresh"),
                        new Example(
                                "Refresh specific cities",
                                "weather refresh --cities london,paris")));
        refresh.setOptions(
                List.of(
                        new ParamInfo(
                                "cities",
                                "string",
                                "Comma-separated city names to refresh (default: all). type:string",
                                null,
                                null),
                        new ParamInfo(
                                "dry_run",
                                "bool",
                                "Describe actions without executing. type:bool",
                                null,
                                null),
                        new ParamInfo(
                                "output",
                                "OutputFormat",
                                "Output format. type:enum[text|json|table]",
                                null,
                                null)));
        app.registerCommand(refresh);
    }

    private static String firstLine(String doc) {
        int n = doc.indexOf('\n');
        return n < 0 ? doc : doc.substring(0, n);
    }

    private static final class Help {
        static final String GET =
                """
                Get current weather for a city.

                Returns temperature, humidity, wind speed, and conditions for the
                specified city. Use --units imperial for Fahrenheit/mph.""";

        static final String FORECAST =
                """
                Get multi-day weather forecast for a city.

                Returns daily high/low temperatures and conditions for the next N days.""";

        static final String ALERTS =
                """
                List active weather alerts.

                Shows weather warnings and advisories. Optionally filter by city.""";

        static final String FAVORITE =
                """
                Add a city to your favorites list.

                Saves a city for quick access. Use --dry-run to preview without saving.
                Idempotent when the city is already in favorites (no error, no duplicate).""";

        static final String REFRESH =
                """
                Refresh cached weather data for cities.

                Demonstrates NDJSON streaming for long-running operations.""";
    }
}
