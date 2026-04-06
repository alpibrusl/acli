/** Output format handling and JSON envelope per ACLI spec §2. */

import { ExitCode, exitCodeName } from './exit-codes.js';

export type OutputFormat = 'text' | 'json' | 'table';

export interface Meta {
  duration_ms: number;
  version: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  hint?: string;
  docs?: string;
}

export interface Envelope {
  ok: boolean;
  command: string;
  data?: unknown;
  dry_run?: boolean;
  planned_actions?: unknown[];
  error?: ErrorDetail;
  meta: Meta;
}

/** Build a success envelope per spec §2.2. */
export function successEnvelope(
  command: string,
  data: unknown,
  version: string,
  startTime?: number,
): Envelope {
  const durationMs = startTime ? Date.now() - startTime : 0;
  return {
    ok: true,
    command,
    data,
    meta: { duration_ms: durationMs, version },
  };
}

/** Build a dry-run success envelope. */
export function dryRunEnvelope(
  command: string,
  plannedActions: unknown[],
  version: string,
  startTime?: number,
): Envelope {
  const durationMs = startTime ? Date.now() - startTime : 0;
  return {
    ok: true,
    command,
    dry_run: true,
    planned_actions: plannedActions,
    meta: { duration_ms: durationMs, version },
  };
}

/** Build an error envelope per spec §2.2. */
export function errorEnvelope(
  command: string,
  code: ExitCode,
  message: string,
  options?: { hint?: string; docs?: string; version?: string; startTime?: number },
): Envelope {
  const durationMs = options?.startTime ? Date.now() - options.startTime : 0;
  const error: ErrorDetail = { code: exitCodeName(code), message };
  if (options?.hint) error.hint = options.hint;
  if (options?.docs) error.docs = options.docs;
  return {
    ok: false,
    command,
    error,
    meta: { duration_ms: durationMs, version: options?.version ?? '0.0.0' },
  };
}

/** Emit an envelope to stdout in the requested format. */
export function emit(envelope: Envelope, format: OutputFormat): void {
  switch (format) {
    case 'json':
      process.stdout.write(JSON.stringify(envelope, null, 2) + '\n');
      break;
    case 'table':
      emitTable(envelope);
      break;
    default:
      emitText(envelope);
  }
}

/** Emit a progress line as NDJSON per spec §2.3. */
export function emitProgress(
  step: string,
  status: string,
  detail?: string,
): void {
  const line: Record<string, string> = { type: 'progress', step, status };
  if (detail !== undefined) line.detail = detail;
  process.stdout.write(JSON.stringify(line) + '\n');
}

/** Emit a final result line as NDJSON per spec §2.3. */
export function emitResult(data: Record<string, unknown>, ok = true): void {
  const line = { type: 'result', ok, ...data };
  process.stdout.write(JSON.stringify(line) + '\n');
}

function emitText(envelope: Envelope): void {
  if (!envelope.ok && envelope.error) {
    process.stderr.write(`Error [${envelope.error.code}]: ${envelope.error.message}\n`);
    if (envelope.error.hint) process.stderr.write(`  ${envelope.error.hint}\n`);
    if (envelope.error.docs) process.stderr.write(`  Reference: ${envelope.error.docs}\n`);
  } else if (envelope.data && typeof envelope.data === 'object') {
    for (const [key, value] of Object.entries(envelope.data as Record<string, unknown>)) {
      process.stdout.write(`${key}: ${value}\n`);
    }
  }
}

function emitTable(envelope: Envelope): void {
  if (!envelope.data) return;
  if (Array.isArray(envelope.data) && envelope.data.length > 0) {
    const rows = envelope.data as Record<string, unknown>[];
    const headers = Object.keys(rows[0]);
    const widths = new Map<string, number>();
    for (const h of headers) widths.set(h, h.length);
    for (const row of rows) {
      for (const h of headers) {
        widths.set(h, Math.max(widths.get(h)!, String(row[h] ?? '').length));
      }
    }
    process.stdout.write(headers.map(h => h.padEnd(widths.get(h)!)).join('  ') + '\n');
    process.stdout.write(headers.map(h => '-'.repeat(widths.get(h)!)).join('  ') + '\n');
    for (const row of rows) {
      process.stdout.write(
        headers.map(h => String(row[h] ?? '').padEnd(widths.get(h)!)).join('  ') + '\n',
      );
    }
  } else if (typeof envelope.data === 'object') {
    for (const [key, value] of Object.entries(envelope.data as Record<string, unknown>)) {
      process.stdout.write(`${key}  ${value}\n`);
    }
  }
}
