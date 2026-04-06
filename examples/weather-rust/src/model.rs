//! Simulated city data and weather generation (mirrors `weather.py`).

use rand::rngs::StdRng;
use rand::Rng;
use rand::SeedableRng;
use serde_json::{json, Value};

#[derive(Clone, Copy)]
pub struct CityInfo {
    pub lat: f64,
    pub lon: f64,
    pub country: &'static str,
}

pub static CITIES: &[(&str, CityInfo)] = &[
    ("london", CityInfo { lat: 51.5, lon: -0.1, country: "GB" }),
    ("paris", CityInfo { lat: 48.9, lon: 2.3, country: "FR" }),
    ("tokyo", CityInfo { lat: 35.7, lon: 139.7, country: "JP" }),
    ("new-york", CityInfo { lat: 40.7, lon: -74.0, country: "US" }),
    ("sydney", CityInfo { lat: -33.9, lon: 151.2, country: "AU" }),
];

pub struct Alert {
    pub city: &'static str,
    pub ty: &'static str,
    pub severity: &'static str,
    pub message: &'static str,
}

pub static ALERTS: &[Alert] = &[
    Alert {
        city: "tokyo",
        ty: "typhoon_warning",
        severity: "high",
        message: "Typhoon approaching",
    },
    Alert {
        city: "london",
        ty: "fog_advisory",
        severity: "low",
        message: "Dense fog expected",
    },
];

/// Mutable favorites (single-threaded CLI).
pub static FAVORITES: std::sync::Mutex<Vec<String>> = std::sync::Mutex::new(Vec::new());

pub fn city_meta(city: &str) -> Option<CityInfo> {
    CITIES
        .iter()
        .find(|(n, _)| *n == city)
        .map(|(_, info)| *info)
}

pub fn sorted_city_names() -> Vec<&'static str> {
    let mut v: Vec<_> = CITIES.iter().map(|(n, _)| *n).collect();
    v.sort();
    v
}

fn rng(city: &str) -> StdRng {
    let seed = city.as_bytes().iter().fold(0u64, |a, &b| {
        a.wrapping_mul(31).wrapping_add(b as u64)
    });
    StdRng::seed_from_u64(seed)
}

pub fn get_weather(city: &str) -> Value {
    let info = city_meta(city).expect("known city");
    let mut r = rng(city);
    let conditions = ["sunny", "cloudy", "rainy", "snowy", "windy"];
    json!({
        "city": city,
        "country": info.country,
        "temperature_c": ((r.gen_range(-5.0_f64..35.0_f64) * 10.0).round()) / 10.0,
        "humidity_pct": r.gen_range(30..96),
        "wind_kph": ((r.gen_range(0.0_f64..50.0_f64) * 10.0).round()) / 10.0,
        "condition": conditions[r.gen_range(0..5)],
        "coordinates": { "lat": info.lat, "lon": info.lon },
    })
}

pub fn add_imperial(mut v: Value) -> Value {
    let obj = v.as_object_mut().expect("object");
    let tc = obj.get("temperature_c").and_then(|x| x.as_f64()).unwrap_or(0.0);
    let wk = obj.get("wind_kph").and_then(|x| x.as_f64()).unwrap_or(0.0);
    obj.insert(
        "temperature_f".into(),
        json!(((tc * 9.0 / 5.0 + 32.0) * 10.0).round() / 10.0),
    );
    obj.insert(
        "wind_mph".into(),
        json!(((wk * 0.621) * 10.0).round() / 10.0),
    );
    v
}

pub fn forecast(city: &str, days: i32) -> Value {
    let info = city_meta(city).expect("known city");
    let mut r = rng(city);
    let conditions = ["sunny", "cloudy", "rainy", "snowy"];
    let mut daily = Vec::new();
    for day in 0..days {
        daily.push(json!({
            "day": day + 1,
            "high_c": ((r.gen_range(5.0_f64..35.0_f64) * 10.0).round()) / 10.0,
            "low_c": ((r.gen_range(-5.0_f64..20.0_f64) * 10.0).round()) / 10.0,
            "condition": conditions[r.gen_range(0..4)],
            "precipitation_pct": r.gen_range(0..101),
        }));
    }
    json!({
        "city": city,
        "country": info.country,
        "days": daily,
    })
}

pub fn alerts_json(filter: Option<&str>) -> Value {
    let filtered: Vec<&Alert> = match filter {
        None | Some("") => ALERTS.iter().collect(),
        Some(c) => ALERTS.iter().filter(|a| a.city == c).collect(),
    };
    let arr: Vec<Value> = filtered
        .iter()
        .map(|a| {
            json!({
                "city": a.city,
                "type": a.ty,
                "severity": a.severity,
                "message": a.message,
            })
        })
        .collect();
    json!({
        "alerts": arr,
        "count": filtered.len(),
    })
}

pub fn ensure_favorite(city: &str) {
    let mut g = FAVORITES.lock().unwrap();
    let s = city.to_string();
    if !g.contains(&s) {
        g.push(s);
    }
}

pub fn favorites_json(city: &str) -> Value {
    let g = FAVORITES.lock().unwrap();
    json!({
        "city": city,
        "favorites": g.clone(),
    })
}

pub fn has_favorite(city: &str) -> bool {
    FAVORITES.lock().unwrap().contains(&city.to_string())
}
