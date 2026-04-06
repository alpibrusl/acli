//! weather — ACLI weather CLI (Rust port of `examples/weather/weather.py`).

mod model;

use acli::acli_args;
use acli::app::AcliApp;
use acli::command::{examples, AcliCommand, CommandMeta, Idempotency};
use acli::errors::{invalid_args, not_found};
use acli::errors::AcliError;
use acli::exit_codes::ExitCode;
use acli::output::{dry_run_envelope, emit, emit_progress, emit_result, success_envelope, OutputFormat};
use clap::{Parser, Subcommand};
use model::{
    add_imperial, alerts_json, city_meta, ensure_favorite, favorites_json, forecast, get_weather,
    has_favorite, sorted_city_names,
};
use serde_json::json;
use std::thread;
use std::time::Instant;

acli_args! {
    /// Get current weather for a city.
    pub struct GetArgs {
        #[arg(long)]
        pub city: String,
        #[arg(long, default_value = "metric")]
        pub units: String,
    }
}

impl AcliCommand for GetArgs {
    fn name() -> &'static str {
        "get"
    }
    fn description() -> &'static str {
        "Get current weather for a city."
    }
    fn meta() -> CommandMeta {
        CommandMeta {
            examples: examples(&[
                ("Get weather for London", "weather get --city london"),
                ("Get weather for Tokyo in JSON", "weather get --city tokyo --output json"),
            ]),
            idempotent: Idempotency::Yes,
            see_also: vec!["forecast".into(), "alerts".into()],
        }
    }
}

acli_args! {
    /// Get multi-day weather forecast for a city.
    pub struct ForecastArgs {
        #[arg(long)]
        pub city: String,
        #[arg(long, default_value_t = 3)]
        pub days: i32,
    }
}

impl AcliCommand for ForecastArgs {
    fn name() -> &'static str {
        "forecast"
    }
    fn description() -> &'static str {
        "Get multi-day weather forecast for a city."
    }
    fn meta() -> CommandMeta {
        CommandMeta {
            examples: examples(&[
                ("Get 3-day forecast for Paris", "weather forecast --city paris --days 3"),
                (
                    "Get 7-day forecast in JSON",
                    "weather forecast --city london --days 7 --output json",
                ),
            ]),
            idempotent: Idempotency::Yes,
            see_also: vec!["get".into(), "alerts".into()],
        }
    }
}

acli_args! {
    /// List active weather alerts.
    pub struct AlertsArgs {
        #[arg(long, default_value = "")]
        pub city: String,
    }
}

impl AcliCommand for AlertsArgs {
    fn name() -> &'static str {
        "alerts"
    }
    fn description() -> &'static str {
        "List active weather alerts."
    }
    fn meta() -> CommandMeta {
        CommandMeta {
            examples: examples(&[
                ("Check all active alerts", "weather alerts"),
                ("Check alerts for Tokyo", "weather alerts --city tokyo"),
            ]),
            idempotent: Idempotency::Yes,
            see_also: vec!["get".into(), "forecast".into()],
        }
    }
}

acli_args! {
    /// Add a city to your favorites list.
    pub struct FavoriteArgs {
        #[arg(long)]
        pub city: String,
    } with dry_run
}

impl AcliCommand for FavoriteArgs {
    fn name() -> &'static str {
        "favorite"
    }
    fn description() -> &'static str {
        "Add a city to your favorites list."
    }
    fn meta() -> CommandMeta {
        CommandMeta {
            examples: examples(&[
                ("Add London to favorites", "weather favorite --city london"),
                ("Dry-run adding Paris", "weather favorite --city paris --dry-run"),
            ]),
            idempotent: Idempotency::Conditional,
            see_also: vec!["get".into()],
        }
    }
}

acli_args! {
    /// Refresh cached weather data for cities.
    pub struct RefreshArgs {
        #[arg(long, default_value = "")]
        pub cities: String,
    } with dry_run
}

impl AcliCommand for RefreshArgs {
    fn name() -> &'static str {
        "refresh"
    }
    fn description() -> &'static str {
        "Refresh cached weather data for cities."
    }
    fn meta() -> CommandMeta {
        CommandMeta {
            examples: examples(&[
                ("Refresh all cities", "weather refresh"),
                ("Refresh specific cities", "weather refresh --cities london,paris"),
            ]),
            idempotent: Idempotency::No,
            see_also: vec!["get".into(), "forecast".into()],
        }
    }
}

#[derive(Parser)]
#[command(name = "weather", version = "1.0.0", about = "ACLI weather CLI for agent consumption.")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Get(GetArgs),
    Forecast(ForecastArgs),
    Alerts(AlertsArgs),
    Favorite(FavoriteArgs),
    Refresh(RefreshArgs),
    Introspect(IntrospectArgs),
    Version(VersionArgs),
    Skill(SkillArgs),
}

#[derive(Parser)]
struct IntrospectArgs {
    #[arg(long)]
    acli_version: bool,
    #[arg(long, default_value = "json")]
    output: OutputFormat,
}

#[derive(Parser)]
struct VersionArgs {
    #[arg(long, default_value = "text")]
    output: OutputFormat,
}

#[derive(Parser)]
struct SkillArgs {
    #[arg(long)]
    out: Option<String>,
    #[arg(long, default_value = "text")]
    output: OutputFormat,
}

fn require_city(city: &str, cmd: &str, docs: Option<&str>) -> Result<(), AcliError> {
    if city_meta(city).is_none() {
        let hint = format!(
            "Available cities: {}",
            sorted_city_names().join(", ")
        );
        let mut e = not_found(format!("Unknown city: '{city}'"))
            .with_hint(hint)
            .with_command(cmd);
        if let Some(d) = docs {
            e = e.with_docs(d);
        }
        return Err(e);
    }
    Ok(())
}

fn run_get(app: &AcliApp, args: GetArgs) -> ExitCode {
    let start = Instant::now();
    let city = args.city.to_lowercase();
    if let Err(e) = require_city(&city, "get", Some(".cli/examples/get.sh")) {
        return app.handle_error(&e);
    }
    let mut data = get_weather(&city);
    if args.units == "imperial" {
        data = add_imperial(data);
    }
    let envelope = success_envelope("get", data, &app.version, Some(start), None);
    emit(&envelope, &args.output);
    ExitCode::Success
}

fn run_forecast(app: &AcliApp, args: ForecastArgs) -> ExitCode {
    let start = Instant::now();
    let city = args.city.to_lowercase();
    if let Err(e) = require_city(&city, "forecast", None) {
        return app.handle_error(&e);
    }
    if !(1..=7).contains(&args.days) {
        let e = invalid_args(format!("Days must be between 1 and 7, got {}", args.days))
            .with_hint("Use --days with a value from 1 to 7")
            .with_command("forecast");
        return app.handle_error(&e);
    }
    let data = forecast(&city, args.days);
    let envelope = success_envelope("forecast", data, &app.version, Some(start), None);
    emit(&envelope, &args.output);
    ExitCode::Success
}

fn run_alerts(app: &AcliApp, args: AlertsArgs) -> ExitCode {
    let start = Instant::now();
    let filter: Option<String> = if args.city.is_empty() {
        None
    } else {
        let c = args.city.to_lowercase();
        if city_meta(&c).is_none() {
            let e = not_found(format!("Unknown city: '{c}'")).with_command("alerts");
            return app.handle_error(&e);
        }
        Some(c)
    };
    let data = alerts_json(filter.as_deref());
    let envelope = success_envelope("alerts", data, &app.version, Some(start), None);
    emit(&envelope, &args.output);
    ExitCode::Success
}

fn run_favorite(app: &AcliApp, args: FavoriteArgs) -> ExitCode {
    let start = Instant::now();
    let city = args.city.to_lowercase();
    if let Err(e) = require_city(&city, "favorite", None) {
        return app.handle_error(&e);
    }

    if args.dry_run {
        let planned = vec![json!({
            "action": "add_favorite",
            "target": city,
            "reversible": true,
            "already_exists": has_favorite(&city),
        })];
        let envelope = dry_run_envelope("favorite", planned, &app.version, Some(start), None);
        emit(&envelope, &args.output);
        return ExitCode::DryRun;
    }

    ensure_favorite(&city);
    let data = favorites_json(&city);
    let envelope = success_envelope("favorite", data, &app.version, Some(start), None);
    emit(&envelope, &args.output);
    ExitCode::Success
}

fn run_refresh(app: &AcliApp, args: RefreshArgs) -> ExitCode {
    let target_cities: Vec<String> = if args.cities.is_empty() {
        sorted_city_names().into_iter().map(String::from).collect()
    } else {
        args.cities
            .split(',')
            .map(|s| s.trim().to_lowercase())
            .filter(|s| !s.is_empty())
            .collect()
    };

    for c in &target_cities {
        if city_meta(c).is_none() {
            let e = not_found(format!("Unknown city: '{c}'")).with_command("refresh");
            return app.handle_error(&e);
        }
    }

    for c in &target_cities {
        emit_progress(
            "refresh",
            "running",
            Some(&format!("Fetching data for {c}")),
        );
        thread::sleep(std::time::Duration::from_millis(10));
    }

    let result = json!({
        "cities_refreshed": target_cities,
        "count": target_cities.len(),
    });
    emit_result(result, true);
    ExitCode::Success
}

fn main() -> std::process::ExitCode {
    let cli = Cli::parse();
    let mut app = AcliApp::new("weather", "1.0.0");
    if let Ok(dir) = std::env::current_dir() {
        app = app.with_cli_dir(dir);
    }

    app.register::<GetArgs>();
    app.register::<ForecastArgs>();
    app.register::<AlertsArgs>();
    app.register::<FavoriteArgs>();
    app.register::<RefreshArgs>();

    let code = match cli.command {
        Commands::Get(args) => run_get(&app, args),
        Commands::Forecast(args) => run_forecast(&app, args),
        Commands::Alerts(args) => run_alerts(&app, args),
        Commands::Favorite(args) => run_favorite(&app, args),
        Commands::Refresh(args) => run_refresh(&app, args),
        Commands::Introspect(args) => {
            if args.acli_version {
                match args.output {
                    OutputFormat::Json => println!("{{\"acli_version\":\"0.1.0\"}}"),
                    _ => println!("acli 0.1.0"),
                }
                ExitCode::Success
            } else {
                app.handle_introspect(&args.output);
                ExitCode::Success
            }
        }
        Commands::Version(args) => {
            app.handle_version(&args.output);
            ExitCode::Success
        }
        Commands::Skill(args) => {
            app.handle_skill(args.out.as_deref(), &args.output);
            ExitCode::Success
        }
    };

    code.into()
}
