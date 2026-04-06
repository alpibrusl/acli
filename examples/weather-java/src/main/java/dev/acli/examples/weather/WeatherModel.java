package dev.acli.examples.weather;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import dev.acli.Output;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

/** Simulated city data and weather generation (mirrors weather.py). */
public final class WeatherModel {

    public record CityInfo(double lat, double lon, String country) {}

    public record Alert(String city, String type, String severity, String message) {}

    public static final Map<String, CityInfo> CITIES =
            Map.of(
                    "london", new CityInfo(51.5, -0.1, "GB"),
                    "paris", new CityInfo(48.9, 2.3, "FR"),
                    "tokyo", new CityInfo(35.7, 139.7, "JP"),
                    "new-york", new CityInfo(40.7, -74.0, "US"),
                    "sydney", new CityInfo(-33.9, 151.2, "AU"));

    public static final List<Alert> ALERTS =
            List.of(
                    new Alert("tokyo", "typhoon_warning", "high", "Typhoon approaching"),
                    new Alert("london", "fog_advisory", "low", "Dense fog expected"));

    /** Mutable favorites list (single-threaded CLI). */
    public static final List<String> FAVORITES = new ArrayList<>();

    private WeatherModel() {}

    public static String normalizeCity(String city) {
        return city.toLowerCase();
    }

    /**
     * @param docs optional path for error envelope (e.g. {@code .cli/examples/get.sh} for {@code get}
     *     only)
     */
    public static void requireKnownCity(String city, String command, String docs) {
        if (!CITIES.containsKey(city)) {
            String hint = "Available cities: " + String.join(", ", sortedCities());
            throw new dev.acli.AcliError(
                    "Unknown city: '" + city + "'",
                    dev.acli.ExitCode.NOT_FOUND,
                    hint,
                    docs,
                    command);
        }
    }

    public static List<String> sortedCities() {
        return CITIES.keySet().stream().sorted().toList();
    }

    /** Deterministic pseudo-random per city (stable across JVM runs for a given city string). */
    private static Random rnd(String city) {
        return new Random(city.hashCode());
    }

    public static ObjectNode getWeather(String city) {
        Random r = rnd(city);
        CityInfo info = CITIES.get(city);
        ObjectNode o = Output.mapper().createObjectNode();
        o.put("city", city);
        o.put("country", info.country());
        o.put("temperature_c", round(r.nextDouble(-5, 35), 1));
        o.put("humidity_pct", r.nextInt(30, 96));
        o.put("wind_kph", round(r.nextDouble(0, 50), 1));
        o.put(
                "condition",
                List.of("sunny", "cloudy", "rainy", "snowy", "windy").get(r.nextInt(0, 5)));
        ObjectNode coords = Output.mapper().createObjectNode();
        coords.put("lat", info.lat());
        coords.put("lon", info.lon());
        o.set("coordinates", coords);
        return o;
    }

    public static ObjectNode getWeatherImperial(ObjectNode metric) {
        ObjectNode o = metric.deepCopy();
        double tc = metric.get("temperature_c").asDouble();
        double wk = metric.get("wind_kph").asDouble();
        o.put("temperature_f", round(tc * 9 / 5 + 32, 1));
        o.put("wind_mph", round(wk * 0.621, 1));
        return o;
    }

    public static ObjectNode forecast(String city, int days) {
        Random r = rnd(city);
        CityInfo info = CITIES.get(city);
        ArrayNode daily = Output.mapper().createArrayNode();
        for (int day = 0; day < days; day++) {
            ObjectNode d = Output.mapper().createObjectNode();
            d.put("day", day + 1);
            d.put("high_c", round(r.nextDouble(5, 35), 1));
            d.put("low_c", round(r.nextDouble(-5, 20), 1));
            d.put(
                    "condition",
                    List.of("sunny", "cloudy", "rainy", "snowy").get(r.nextInt(0, 4)));
            d.put("precipitation_pct", r.nextInt(0, 101));
            daily.add(d);
        }
        ObjectNode data = Output.mapper().createObjectNode();
        data.put("city", city);
        data.put("country", info.country());
        data.set("days", daily);
        return data;
    }

    public static ObjectNode alertsJson(String cityFilter) {
        List<Alert> filtered =
                cityFilter == null || cityFilter.isEmpty()
                        ? new ArrayList<>(ALERTS)
                        : ALERTS.stream()
                                .filter(a -> a.city().equals(cityFilter))
                                .toList();
        ArrayNode arr = Output.mapper().createArrayNode();
        for (Alert a : filtered) {
            ObjectNode o = Output.mapper().createObjectNode();
            o.put("city", a.city());
            o.put("type", a.type());
            o.put("severity", a.severity());
            o.put("message", a.message());
            arr.add(o);
        }
        ObjectNode data = Output.mapper().createObjectNode();
        data.set("alerts", arr);
        data.put("count", filtered.size());
        return data;
    }

    private static double round(double v, int decimals) {
        double p = Math.pow(10, decimals);
        return Math.round(v * p) / p;
    }
}
