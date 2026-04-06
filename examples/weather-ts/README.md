# weather (TypeScript)

TypeScript port of [`../weather/weather.py`](../weather/weather.py): same commands, JSON envelopes, NDJSON `refresh`, dry-run exit `9` for `favorite --dry-run`.

## Build & test

Build the SDK first (local `file:` dependency), then this package:

```bash
npm install && npm run build --prefix ../../sdks/typescript
npm install && npm run build && npm test
```

## Run

```bash
node dist/weather.js get --city london --output json
```

## License

[EUPL-1.2](../../LICENSE)
