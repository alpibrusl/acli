/** ACLI — Agent-friendly CLI TypeScript SDK. */

export { AcliApp, type AcliCommandMeta } from './app.js';
export { generateCliFolder, needsUpdate } from './cli-folder.js';
export {
  AcliError,
  ConflictError,
  InvalidArgsError,
  NotFoundError,
  PreconditionError,
  suggestFlag,
} from './errors.js';
export { ExitCode, exitCodeName } from './exit-codes.js';
export {
  CommandInfoBuilder,
  command,
  createCommandTree,
  type CommandInfo,
  type CommandTree,
  type Example,
  type ParamInfo,
} from './introspect.js';
export {
  emit,
  emitProgress,
  emitResult,
  errorEnvelope,
  successEnvelope,
  dryRunEnvelope,
  type Envelope,
  type ErrorDetail,
  type Meta,
  type OutputFormat,
} from './output.js';
export { generateSkill } from './skill.js';
