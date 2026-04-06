/** Semantic exit codes as defined by ACLI spec §3. */
export enum ExitCode {
  Success = 0,
  GeneralError = 1,
  InvalidArgs = 2,
  NotFound = 3,
  PermissionDenied = 4,
  Conflict = 5,
  Timeout = 6,
  UpstreamError = 7,
  PreconditionFailed = 8,
  DryRun = 9,
}

/** Get the string name of an exit code. */
export function exitCodeName(code: ExitCode): string {
  return ExitCode[code] ?? 'UNKNOWN';
}
