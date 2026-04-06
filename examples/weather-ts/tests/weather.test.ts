import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const root = dirname(fileURLToPath(import.meta.url));
const bin = join(root, '../dist/weather.js');

function run(...args: string[]): string {
  return execFileSync('node', [bin, ...args], { encoding: 'utf-8' });
}

function runCode(...args: string[]): number {
  try {
    execFileSync('node', [bin, ...args], { encoding: 'utf-8' });
    return 0;
  } catch (e: unknown) {
    const err = e as { status?: number };
    return err.status ?? 1;
  }
}

describe('weather CLI', () => {
  it('get london json', () => {
    const out = run('get', '--city', 'london', '--output', 'json');
    expect(out).toContain('"ok": true');
    expect(out).toContain('london');
  });

  it('unknown city exit 3', () => {
    const code = runCode('get', '--city', 'mars', '--output', 'json');
    expect(code).toBe(3);
  });

  it('forecast invalid days exit 2', () => {
    const code = runCode('forecast', '--city', 'london', '--days', '9', '--output', 'json');
    expect(code).toBe(2);
  });

  it('favorite dry-run exit 9', () => {
    const code = runCode('favorite', '--city', 'london', '--dry-run', '--output', 'json');
    expect(code).toBe(9);
  });

  it('introspect', () => {
    const out = run('introspect', '--output', 'json');
    expect(out).toContain('weather');
    expect(out).toContain('get');
  });

  it('refresh ndjson', () => {
    const out = run('refresh', '--cities', 'london');
    expect(out).toContain('"type":"progress"');
    expect(out).toContain('"type":"result"');
  });
});
