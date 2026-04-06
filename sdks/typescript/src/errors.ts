/** ACLI error types with actionable messages per spec §4. */

import { ExitCode } from './exit-codes.js';

/** Base error for ACLI commands. Always actionable per spec §4.2. */
export class AcliError extends Error {
  code: ExitCode;
  hint?: string;
  docs?: string;
  command?: string;

  constructor(
    message: string,
    options?: {
      code?: ExitCode;
      hint?: string;
      docs?: string;
      command?: string;
    },
  ) {
    super(message);
    this.name = 'AcliError';
    this.code = options?.code ?? ExitCode.GeneralError;
    this.hint = options?.hint;
    this.docs = options?.docs;
    this.command = options?.command;
  }
}

/** Invalid arguments error (exit code 2). */
export class InvalidArgsError extends AcliError {
  constructor(message: string, options?: { hint?: string; docs?: string }) {
    super(message, { code: ExitCode.InvalidArgs, ...options });
    this.name = 'InvalidArgsError';
  }
}

/** Not found error (exit code 3). */
export class NotFoundError extends AcliError {
  constructor(message: string, options?: { hint?: string; docs?: string }) {
    super(message, { code: ExitCode.NotFound, ...options });
    this.name = 'NotFoundError';
  }
}

/** Conflict error (exit code 5). */
export class ConflictError extends AcliError {
  constructor(message: string, options?: { hint?: string; docs?: string }) {
    super(message, { code: ExitCode.Conflict, ...options });
    this.name = 'ConflictError';
  }
}

/** Precondition failed error (exit code 8). */
export class PreconditionError extends AcliError {
  constructor(message: string, options?: { hint?: string; docs?: string }) {
    super(message, { code: ExitCode.PreconditionFailed, ...options });
    this.name = 'PreconditionError';
  }
}

/** Suggest a close match for a mistyped flag per spec §4.1. */
export function suggestFlag(unknown: string, known: string[]): string | null {
  let best: string | null = null;
  let bestDist = 3;
  for (const k of known) {
    const d = levenshtein(unknown, k);
    if (d < bestDist) {
      bestDist = d;
      best = k;
    }
  }
  return best;
}

function levenshtein(a: string, b: string): number {
  const matrix: number[][] = [];
  for (let i = 0; i <= a.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= b.length; j++) {
    matrix[0][j] = j;
  }
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost,
      );
    }
  }
  return matrix[a.length][b.length];
}
