/**
 * weather — ACLI weather CLI (TypeScript port of examples/weather/weather.py).
 */

import {
  AcliApp,
  AcliError,
  ExitCode,
  type OutputFormat,
  dryRunEnvelope,
  emit,
  emitProgress,
  emitResult,
  successEnvelope,
} from '@acli/sdk';

const VERSION = '1.0.0';

const CITIES: Record<string, { lat: number; lon: number; country: string }> = {
  london: { lat: 51.5, lon: -0.1, country: 'GB' },
  paris: { lat: 48.9, lon: 2.3, country: 'FR' },
  tokyo: { lat: 35.7, lon: 139.7, country: 'JP' },
  'new-york': { lat: 40.7, lon: -74.0, country: 'US' },
  sydney: { lat: -33.9, lon: 151.2, country: 'AU' },
};

const ALERTS = [
  { city: 'tokyo', type: 'typhoon_warning', severity: 'high', message: 'Typhoon approaching' },
  { city: 'london', type: 'fog_advisory', severity: 'low', message: 'Dense fog expected' },
];

const FAVORITES: string[] = [];

function sortedCities(): string[] {
  return Object.keys(CITIES).sort();
}

function rngForCity(city: string): () => number {
  let s = [...city].reduce((acc, c) => acc * 31 + c.charCodeAt(0), 0) >>> 0;
  return () => {
    s = (Math.imul(s, 1103515245) + 12345) >>> 0;
    return (s & 0x7fffffff) / 0x7fffffff;
  };
}

function getWeather(city: string): Record<string, unknown> {
  const r = rngForCity(city);
  const conditions = ['sunny', 'cloudy', 'rainy', 'snowy', 'windy'];
  const info = CITIES[city];
  return {
    city,
    country: info.country,
    temperature_c: Math.round((r() * 40 - 5) * 10) / 10,
    humidity_pct: Math.floor(r() * 66) + 30,
    wind_kph: Math.round(r() * 50 * 10) / 10,
    condition: conditions[Math.floor(r() * 5)],
    coordinates: { lat: info.lat, lon: info.lon },
  };
}

function addImperial(data: Record<string, unknown>): Record<string, unknown> {
  const tc = data.temperature_c as number;
  const wk = data.wind_kph as number;
  return {
    ...data,
    temperature_f: Math.round(((tc * 9) / 5 + 32) * 10) / 10,
    wind_mph: Math.round(wk * 0.621 * 10) / 10,
  };
}

function forecast(city: string, days: number): Record<string, unknown> {
  const r = rngForCity(city);
  const info = CITIES[city];
  const conditions = ['sunny', 'cloudy', 'rainy', 'snowy'];
  const daily = [];
  for (let d = 0; d < days; d++) {
    daily.push({
      day: d + 1,
      high_c: Math.round((r() * 30 + 5) * 10) / 10,
      low_c: Math.round((r() * 25 - 5) * 10) / 10,
      condition: conditions[Math.floor(r() * 4)],
      precipitation_pct: Math.floor(r() * 101),
    });
  }
  return { city, country: info.country, days: daily };
}

function alertsJson(filter: string | undefined): Record<string, unknown> {
  const filtered =
    filter === undefined || filter === ''
      ? ALERTS
      : ALERTS.filter(a => a.city === filter);
  return {
    alerts: filtered,
    count: filtered.length,
  };
}

function buildApp(): AcliApp {
  const app = new AcliApp('weather', VERSION, { cliDir: process.cwd() });

  app
    .command(
      'get',
      `Get current weather for a city.

Returns temperature, humidity, wind speed, and conditions for the
specified city. Use --units imperial for Fahrenheit/mph.`,
      {
        examples: [
          ['Get weather for London', 'weather get --city london'],
          ['Get weather for Tokyo in JSON', 'weather get --city tokyo --output json'],
        ],
        idempotent: true,
        seeAlso: ['forecast', 'alerts'],
      },
      opts => {
        const output = opts.output as OutputFormat;
        const start = Date.now();
        const city = String(opts.city ?? '').toLowerCase();
        if (!CITIES[city]) {
          throw new AcliError(`Unknown city: '${city}'`, {
            code: ExitCode.NotFound,
            hint: `Available cities: ${sortedCities().join(', ')}`,
            docs: '.cli/examples/get.sh',
            command: 'get',
          });
        }
        let data: Record<string, unknown> = getWeather(city);
        if (String(opts.units ?? 'metric') === 'imperial') {
          data = addImperial(data);
        }
        emit(successEnvelope('get', data, VERSION, start), output);
      },
    )
    .option('--city <city>', 'City name (lowercase, hyphenated). type:string')
    .option('--units <units>', 'Unit system. type:enum[metric|imperial]', 'metric');

  app
    .command(
      'forecast',
      `Get multi-day weather forecast for a city.

Returns daily high/low temperatures and conditions for the next N days.`,
      {
        examples: [
          ['Get 3-day forecast for Paris', 'weather forecast --city paris --days 3'],
          [
            'Get 7-day forecast in JSON',
            'weather forecast --city london --days 7 --output json',
          ],
        ],
        idempotent: true,
        seeAlso: ['get', 'alerts'],
      },
      opts => {
        const output = opts.output as OutputFormat;
        const start = Date.now();
        const city = String(opts.city ?? '').toLowerCase();
        const days = Number(opts.days ?? 3);
        if (!CITIES[city]) {
          throw new AcliError(`Unknown city: '${city}'`, {
            code: ExitCode.NotFound,
            hint: `Available cities: ${sortedCities().join(', ')}`,
            command: 'forecast',
          });
        }
        if (days < 1 || days > 7) {
          throw new AcliError(`Days must be between 1 and 7, got ${days}`, {
            code: ExitCode.InvalidArgs,
            hint: 'Use --days with a value from 1 to 7',
            command: 'forecast',
          });
        }
        emit(successEnvelope('forecast', forecast(city, days), VERSION, start), output);
      },
    )
    .option('--city <city>', 'City name (lowercase, hyphenated). type:string')
    .option('--days <n>', 'Number of forecast days (1-7). type:int', '3');

  app
    .command(
      'alerts',
      `List active weather alerts.

Shows weather warnings and advisories. Optionally filter by city.`,
      {
        examples: [
          ['Check all active alerts', 'weather alerts'],
          ['Check alerts for Tokyo', 'weather alerts --city tokyo'],
        ],
        idempotent: true,
        seeAlso: ['get', 'forecast'],
      },
      opts => {
        const output = opts.output as OutputFormat;
        const start = Date.now();
        let filter: string | undefined;
        const raw = String(opts.city ?? '');
        if (raw !== '') {
          const c = raw.toLowerCase();
          if (!CITIES[c]) {
            throw new AcliError(`Unknown city: '${c}'`, {
              code: ExitCode.NotFound,
              command: 'alerts',
            });
          }
          filter = c;
        }
        emit(successEnvelope('alerts', alertsJson(filter), VERSION, start), output);
      },
    )
    .option('--city <city>', 'Filter alerts by city (optional). type:string', '');

  app
    .command(
      'favorite',
      `Add a city to your favorites list.

Saves a city for quick access. Use --dry-run to preview without saving.`,
      {
        examples: [
          ['Add London to favorites', 'weather favorite --city london'],
          ['Dry-run adding Paris', 'weather favorite --city paris --dry-run'],
        ],
        idempotent: 'conditional',
        seeAlso: ['get'],
      },
      opts => {
        const output = opts.output as OutputFormat;
        const start = Date.now();
        const city = String(opts.city ?? '').toLowerCase();
        if (!CITIES[city]) {
          throw new AcliError(`Unknown city: '${city}'`, {
            code: ExitCode.NotFound,
            command: 'favorite',
          });
        }
        if (opts.dryRun === true) {
          const planned = [
            {
              action: 'add_favorite',
              target: city,
              reversible: true,
              already_exists: FAVORITES.includes(city),
            },
          ];
          emit(dryRunEnvelope('favorite', planned, VERSION, start), output);
          process.exitCode = ExitCode.DryRun;
          return;
        }
        if (!FAVORITES.includes(city)) {
          FAVORITES.push(city);
        }
        emit(
          successEnvelope('favorite', { city, favorites: [...FAVORITES] }, VERSION, start),
          output,
        );
      },
    )
    .option('--city <city>', 'City to add to favorites. type:string')
    .option('--dry-run', 'Preview without saving. type:bool', false);

  app
    .command(
      'refresh',
      `Refresh cached weather data for cities.

Demonstrates NDJSON streaming for long-running operations.`,
      {
        examples: [
          ['Refresh all cities', 'weather refresh'],
          ['Refresh specific cities', 'weather refresh --cities london,paris'],
        ],
        idempotent: false,
        seeAlso: ['get', 'forecast'],
      },
      async opts => {
        const raw = String(opts.cities ?? '');
        const targetCities =
          raw === ''
            ? sortedCities()
            : raw
                .split(',')
                .map(s => s.trim().toLowerCase())
                .filter(Boolean);
        for (const c of targetCities) {
          if (!CITIES[c]) {
            throw new AcliError(`Unknown city: '${c}'`, {
              code: ExitCode.NotFound,
              command: 'refresh',
            });
          }
        }
        for (const c of targetCities) {
          emitProgress('refresh', 'running', `Fetching data for ${c}`);
          await new Promise(r => setTimeout(r, 10));
        }
        emitResult({ cities_refreshed: targetCities, count: targetCities.length }, true);
      },
    )
    .option(
      '--cities <cities>',
      'Comma-separated city names to refresh (default: all). type:string',
      '',
    );

  return app;
}

async function main(): Promise<void> {
  const app = buildApp();
  await app.run();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
