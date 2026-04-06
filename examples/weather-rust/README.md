# weather (Rust)

Rust port of [`../weather/weather.py`](../weather/weather.py): same commands, JSON envelopes, NDJSON `refresh`, dry-run exit `9` for `favorite --dry-run`.

## Build & test

```bash
cargo test
cargo run -- get --city london --output json
```

## License

[EUPL-1.2](../../LICENSE)
