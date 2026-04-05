#!/usr/bin/env python3
"""weather — an ACLI-compliant weather CLI for agent consumption.

A complete example showing how to build an agent-friendly CLI tool
using the ACLI Python SDK. Demonstrates:
- Auto-injected --output (no need to declare it on every command)
- Auto-injected --dry-run on non-idempotent commands
- NDJSON streaming for long-running operations
- Actionable error messages with hints
- Semantic exit codes
"""

from __future__ import annotations

import random
import time
from typing import Any

import typer

from acli import (
    ACLIApp,
    ExitCode,
    InvalidArgsError,
    NotFoundError,
    OutputFormat,
    acli_command,
    emit,
    emit_progress,
    emit_result,
    success_envelope,
)

app = ACLIApp(name="weather", version="1.0.0")

# ── Simulated data ────────────────────────────────────────────────────────────

CITIES: dict[str, dict[str, Any]] = {
    "london": {"lat": 51.5, "lon": -0.1, "country": "GB"},
    "paris": {"lat": 48.9, "lon": 2.3, "country": "FR"},
    "tokyo": {"lat": 35.7, "lon": 139.7, "country": "JP"},
    "new-york": {"lat": 40.7, "lon": -74.0, "country": "US"},
    "sydney": {"lat": -33.9, "lon": 151.2, "country": "AU"},
}

ALERTS: list[dict[str, Any]] = [
    {"city": "tokyo", "type": "typhoon_warning", "severity": "high", "message": "Typhoon approaching"},
    {"city": "london", "type": "fog_advisory", "severity": "low", "message": "Dense fog expected"},
]

FAVORITES: list[str] = []


def _get_weather(city: str) -> dict[str, Any]:
    """Generate simulated weather data for a city."""
    random.seed(hash(city))
    return {
        "city": city,
        "country": CITIES[city]["country"],
        "temperature_c": round(random.uniform(-5, 35), 1),
        "humidity_pct": random.randint(30, 95),
        "wind_kph": round(random.uniform(0, 50), 1),
        "condition": random.choice(["sunny", "cloudy", "rainy", "snowy", "windy"]),
        "coordinates": {"lat": CITIES[city]["lat"], "lon": CITIES[city]["lon"]},
    }


# ── Commands ──────────────────────────────────────────────────────────────────
# Note: --output is auto-injected by @acli_command — no need to declare it.
# Note: --dry-run is auto-injected on idempotent=False commands.


@app.command()
@acli_command(
    examples=[
        ("Get weather for London", "weather get --city london"),
        ("Get weather for Tokyo in JSON", "weather get --city tokyo --output json"),
    ],
    idempotent=True,
    see_also=["forecast", "alerts"],
)
def get(
    city: str = typer.Option(..., help="City name (lowercase, hyphenated). type:string"),
    units: str = typer.Option("metric", help="Unit system. type:enum[metric|imperial]"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Get current weather for a city.

    Returns temperature, humidity, wind speed, and conditions for the
    specified city. Use --units imperial for Fahrenheit/mph.
    """
    start = time.time()
    city = city.lower()
    if city not in CITIES:
        raise NotFoundError(
            f"Unknown city: '{city}'",
            hint=f"Available cities: {', '.join(sorted(CITIES))}",
            docs=".cli/examples/get.sh",
        )

    data = _get_weather(city)
    if units == "imperial":
        data["temperature_f"] = round(data["temperature_c"] * 9 / 5 + 32, 1)
        data["wind_mph"] = round(data["wind_kph"] * 0.621, 1)

    emit(success_envelope("get", data, version="1.0.0", start_time=start), output)


@app.command()
@acli_command(
    examples=[
        ("Get 3-day forecast for Paris", "weather forecast --city paris --days 3"),
        ("Get 7-day forecast in JSON", "weather forecast --city london --days 7 --output json"),
    ],
    idempotent=True,
    see_also=["get", "alerts"],
)
def forecast(
    city: str = typer.Option(..., help="City name (lowercase, hyphenated). type:string"),
    days: int = typer.Option(3, help="Number of forecast days (1-7). type:int"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Get multi-day weather forecast for a city.

    Returns daily high/low temperatures and conditions for the next N days.
    """
    start = time.time()
    city = city.lower()
    if city not in CITIES:
        raise NotFoundError(
            f"Unknown city: '{city}'",
            hint=f"Available cities: {', '.join(sorted(CITIES))}",
        )
    if not 1 <= days <= 7:
        raise InvalidArgsError(
            f"Days must be between 1 and 7, got {days}",
            hint="Use --days with a value from 1 to 7",
        )

    random.seed(hash(city))
    daily = []
    for day in range(days):
        daily.append({
            "day": day + 1,
            "high_c": round(random.uniform(5, 35), 1),
            "low_c": round(random.uniform(-5, 20), 1),
            "condition": random.choice(["sunny", "cloudy", "rainy", "snowy"]),
            "precipitation_pct": random.randint(0, 100),
        })

    data = {"city": city, "country": CITIES[city]["country"], "days": daily}
    emit(success_envelope("forecast", data, version="1.0.0", start_time=start), output)


@app.command()
@acli_command(
    examples=[
        ("Check all active alerts", "weather alerts"),
        ("Check alerts for Tokyo", "weather alerts --city tokyo"),
    ],
    idempotent=True,
    see_also=["get", "forecast"],
)
def alerts(
    city: str = typer.Option("", help="Filter alerts by city (optional). type:string"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """List active weather alerts.

    Shows weather warnings and advisories. Optionally filter by city.
    """
    start = time.time()
    filtered = ALERTS
    if city:
        city = city.lower()
        if city not in CITIES:
            raise NotFoundError(f"Unknown city: '{city}'")
        filtered = [a for a in ALERTS if a["city"] == city]

    data = {"alerts": filtered, "count": len(filtered)}
    emit(success_envelope("alerts", data, version="1.0.0", start_time=start), output)


@app.command()
@acli_command(
    examples=[
        ("Add London to favorites", "weather favorite --city london"),
        ("Dry-run adding Paris", "weather favorite --city paris --dry-run"),
    ],
    idempotent="conditional",
    see_also=["get"],
)
def favorite(
    city: str = typer.Option(..., help="City to add to favorites. type:string"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without saving. type:bool"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Add a city to your favorites list.

    Saves a city for quick access. Use --dry-run to preview without saving.
    Idempotent when the city is already in favorites (no error, no duplicate).
    """
    start = time.time()
    city = city.lower()
    if city not in CITIES:
        raise NotFoundError(f"Unknown city: '{city}'")

    if dry_run:
        already = city in FAVORITES
        actions = [{"action": "add_favorite", "target": city, "reversible": True, "already_exists": already}]
        envelope = success_envelope(
            "favorite", {}, version="1.0.0", start_time=start, dry_run=True, planned_actions=actions
        )
        emit(envelope, output)
        raise SystemExit(ExitCode.DRY_RUN)

    if city not in FAVORITES:
        FAVORITES.append(city)

    data = {"city": city, "favorites": FAVORITES}
    emit(success_envelope("favorite", data, version="1.0.0", start_time=start), output)


@app.command()
@acli_command(
    examples=[
        ("Refresh all cities", "weather refresh"),
        ("Refresh specific cities", "weather refresh --cities london,paris"),
    ],
    idempotent=False,
    see_also=["get", "forecast"],
)
def refresh(
    cities: str = typer.Option(
        "", help="Comma-separated city names to refresh (default: all). type:string"
    ),
) -> None:
    """Refresh cached weather data for cities.

    Demonstrates NDJSON streaming for long-running operations.
    The --dry-run flag is auto-injected because idempotent=False.
    The --output flag is auto-injected by @acli_command.
    """
    target_cities = [c.strip() for c in cities.split(",") if c.strip()] if cities else list(CITIES)

    for c in target_cities:
        if c not in CITIES:
            raise NotFoundError(f"Unknown city: '{c}'")

    # Stream progress as NDJSON
    for c in target_cities:
        emit_progress("refresh", "running", detail=f"Fetching data for {c}")
        time.sleep(0.01)  # Simulated work

    emit_result({"cities_refreshed": target_cities, "count": len(target_cities)})


def main() -> None:
    """Entry point."""
    app.run()


if __name__ == "__main__":
    main()
