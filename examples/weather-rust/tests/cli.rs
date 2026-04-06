//! Integration tests for the `weather` binary.

use assert_cmd::Command;
use predicates::str::contains;

fn weather() -> Command {
    Command::cargo_bin("weather").expect("weather binary")
}

#[test]
fn get_london_json() {
    weather()
        .args(["get", "--city", "london", "--output", "json"])
        .assert()
        .success()
        .stdout(contains("\"ok\": true"))
        .stdout(contains("london"));
}

#[test]
fn get_unknown_city() {
    weather()
        .args(["get", "--city", "mars", "--output", "json"])
        .assert()
        .code(3)
        .stdout(contains("NOT_FOUND"));
}

#[test]
fn forecast_invalid_days() {
    weather()
        .args([
            "forecast",
            "--city",
            "london",
            "--days",
            "9",
            "--output",
            "json",
        ])
        .assert()
        .code(2)
        .stdout(contains("INVALID_ARGS"));
}

#[test]
fn favorite_dry_run_exit_9() {
    weather()
        .args([
            "favorite",
            "--city",
            "london",
            "--dry-run",
            "--output",
            "json",
        ])
        .assert()
        .code(9)
        .stdout(contains("dry_run"))
        .stdout(contains("planned_actions"));
}

#[test]
fn introspect_has_weather() {
    weather()
        .args(["introspect", "--output", "json"])
        .assert()
        .success()
        .stdout(contains("weather"))
        .stdout(contains("get"));
}

#[test]
fn refresh_ndjson() {
    weather()
        .args(["refresh", "--cities", "london"])
        .assert()
        .success()
        .stdout(contains("\"type\":\"progress\""))
        .stdout(contains("\"type\":\"result\""));
}
