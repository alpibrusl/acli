import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/weather.ts'],
  format: ['esm'],
  platform: 'node',
  target: 'node20',
  clean: true,
});
