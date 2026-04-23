import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

import { ExitCode, exitCodeName } from '../src/exit-codes.js';
import {
  successEnvelope,
  errorEnvelope,
  dryRunEnvelope,
  type OutputFormat,
} from '../src/output.js';
import {
  AcliError,
  InvalidArgsError,
  NotFoundError,
  ConflictError,
  PreconditionError,
  suggestFlag,
} from '../src/errors.js';
import {
  createCommandTree,
  command,
  type CommandTree,
} from '../src/introspect.js';
import { generateCliFolder, needsUpdate } from '../src/cli-folder.js';
import { generateSkill } from '../src/skill.js';
import { AcliApp } from '../src/app.js';

// ── Exit Codes ───────────────────────────────────────────────────────────────

describe('ExitCode', () => {
  it('has correct values', () => {
    expect(ExitCode.Success).toBe(0);
    expect(ExitCode.GeneralError).toBe(1);
    expect(ExitCode.InvalidArgs).toBe(2);
    expect(ExitCode.NotFound).toBe(3);
    expect(ExitCode.DryRun).toBe(9);
  });

  it('exitCodeName returns name', () => {
    expect(exitCodeName(ExitCode.Success)).toBe('Success');
    expect(exitCodeName(ExitCode.InvalidArgs)).toBe('InvalidArgs');
  });
});

// ── Output / Envelopes ───────────────────────────────────────────────────────

describe('Envelopes', () => {
  it('builds success envelope', () => {
    const env = successEnvelope('run', { result: 42 }, '1.0.0');
    expect(env.ok).toBe(true);
    expect(env.command).toBe('run');
    expect(env.data).toEqual({ result: 42 });
    expect(env.meta.version).toBe('1.0.0');
  });

  it('builds success envelope with timing', () => {
    const start = Date.now() - 100;
    const env = successEnvelope('run', {}, '1.0.0', start);
    expect(env.meta.duration_ms).toBeGreaterThanOrEqual(100);
  });

  it('builds error envelope', () => {
    const env = errorEnvelope('run', ExitCode.InvalidArgs, 'Missing --pipeline', {
      hint: 'Run --help',
      docs: '.cli/examples/run.sh',
      version: '1.0.0',
    });
    expect(env.ok).toBe(false);
    expect(env.error!.code).toBe('InvalidArgs');
    expect(env.error!.message).toBe('Missing --pipeline');
    expect(env.error!.hint).toBe('Run --help');
    expect(env.error!.docs).toBe('.cli/examples/run.sh');
  });

  it('builds dry-run envelope', () => {
    const actions = [{ action: 'create', target: 'x' }];
    const env = dryRunEnvelope('deploy', actions, '1.0.0');
    expect(env.ok).toBe(true);
    expect(env.dry_run).toBe(true);
    expect(env.planned_actions).toEqual(actions);
    expect(env.data).toBeUndefined();
  });
});

// ── Errors ───────────────────────────────────────────────────────────────────

describe('Errors', () => {
  it('AcliError has defaults', () => {
    const err = new AcliError('broke');
    expect(err.message).toBe('broke');
    expect(err.code).toBe(ExitCode.GeneralError);
    expect(err.hint).toBeUndefined();
  });

  it('error subclasses have correct codes', () => {
    expect(new InvalidArgsError('bad').code).toBe(ExitCode.InvalidArgs);
    expect(new NotFoundError('gone').code).toBe(ExitCode.NotFound);
    expect(new ConflictError('locked').code).toBe(ExitCode.Conflict);
    expect(new PreconditionError('need setup').code).toBe(ExitCode.PreconditionFailed);
  });

  it('error with hint and docs', () => {
    const err = new InvalidArgsError('bad', { hint: 'try this', docs: 'readme.md' });
    expect(err.hint).toBe('try this');
    expect(err.docs).toBe('readme.md');
  });
});

describe('suggestFlag', () => {
  it('finds close match', () => {
    expect(suggestFlag('--pipline', ['--pipeline', '--env', '--dry-run'])).toBe('--pipeline');
  });

  it('returns null for no match', () => {
    expect(suggestFlag('--zzzzz', ['--pipeline', '--env'])).toBeNull();
  });

  it('finds exact match', () => {
    expect(suggestFlag('--env', ['--pipeline', '--env'])).toBe('--env');
  });
});

// ── Introspect ───────────────────────────────────────────────────────────────

describe('Introspect', () => {
  it('creates command tree', () => {
    const tree = createCommandTree('noether', '1.0.0');
    expect(tree.name).toBe('noether');
    expect(tree.version).toBe('1.0.0');
    expect(tree.acli_version).toBe('0.1.0');
    expect(tree.commands).toEqual([]);
  });

  it('builds command info with builder', () => {
    const info = command('run', 'Execute a pipeline')
      .idempotent(false)
      .withExamples([
        ['Run basic', 'noether run --file x.yaml'],
        ['Dry run', 'noether run --file x.yaml --dry-run'],
      ])
      .withSeeAlso(['status'])
      .addOption('file', 'path', 'Pipeline file')
      .addOption('env', 'string', 'Environment', 'dev')
      .build();

    expect(info.name).toBe('run');
    expect(info.idempotent).toBe(false);
    expect(info.examples!.length).toBe(2);
    expect(info.see_also).toEqual(['status']);
    expect(info.options.length).toBe(2);
    expect(info.options[1].default).toBe('dev');
  });
});

// ── CLI Folder ───────────────────────────────────────────────────────────────

function sampleTree(): CommandTree {
  const tree = createCommandTree('noether', '1.0.0');
  tree.commands.push(
    command('run', 'Run a pipeline')
      .idempotent(false)
      .withExamples([
        ['Run basic', 'noether run --file x.yaml'],
        ['Dry run', 'noether run --file x.yaml --dry-run'],
      ])
      .build(),
  );
  return tree;
}

describe('CLI Folder', () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'acli-test-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('generates folder structure', () => {
    const cliDir = generateCliFolder(sampleTree(), tmpDir);
    expect(fs.existsSync(path.join(cliDir, 'commands.json'))).toBe(true);
    expect(fs.existsSync(path.join(cliDir, 'README.md'))).toBe(true);
    expect(fs.existsSync(path.join(cliDir, 'changelog.md'))).toBe(true);
    expect(fs.existsSync(path.join(cliDir, 'examples'))).toBe(true);
    expect(fs.existsSync(path.join(cliDir, 'schemas'))).toBe(true);
  });

  it('writes correct commands.json', () => {
    const cliDir = generateCliFolder(sampleTree(), tmpDir);
    const data = JSON.parse(fs.readFileSync(path.join(cliDir, 'commands.json'), 'utf-8'));
    expect(data.name).toBe('noether');
    expect(data.commands.length).toBe(1);
  });

  it('does not overwrite changelog', () => {
    const cliDir = generateCliFolder(sampleTree(), tmpDir);
    fs.writeFileSync(path.join(cliDir, 'changelog.md'), '# Custom');
    generateCliFolder(sampleTree(), tmpDir);
    expect(fs.readFileSync(path.join(cliDir, 'changelog.md'), 'utf-8')).toBe('# Custom');
  });

  it('needsUpdate detects changes', () => {
    expect(needsUpdate(sampleTree(), tmpDir)).toBe(true);
    generateCliFolder(sampleTree(), tmpDir);
    expect(needsUpdate(sampleTree(), tmpDir)).toBe(false);
  });

  it('writes example scripts', () => {
    const cliDir = generateCliFolder(sampleTree(), tmpDir);
    const script = fs.readFileSync(path.join(cliDir, 'examples', 'run.sh'), 'utf-8');
    expect(script).toContain('noether run --file x.yaml');
  });
});

// ── Skill ────────────────────────────────────────────────────────────────────

describe('Skill', () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'acli-test-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('generates skill content', () => {
    const content = generateSkill(sampleTree());
    expect(content).toContain('# noether');
    expect(content).toContain('v1.0.0');
    expect(content).toContain('## Available commands');
    expect(content).toContain('`noether run`');
    expect(content).toContain('## Exit codes');
  });

  it('writes to file', () => {
    const target = path.join(tmpDir, 'SKILL.md');
    const content = generateSkill(sampleTree(), target);
    expect(fs.existsSync(target)).toBe(true);
    expect(fs.readFileSync(target, 'utf-8')).toBe(content);
  });

  it('excludes builtins', () => {
    const tree = sampleTree();
    tree.commands.push({ name: 'introspect', description: 'Introspect', arguments: [], options: [], subcommands: [] });
    tree.commands.push({ name: 'version', description: 'Version', arguments: [], options: [], subcommands: [] });
    const content = generateSkill(tree);
    const available = content.split('## Available commands')[1].split('##')[0];
    expect(available).not.toContain('`noether introspect`');
    expect(available).toContain('`noether run`');
  });

  it('emits default frontmatter', () => {
    const content = generateSkill(sampleTree());
    expect(content.startsWith('---\n')).toBe(true);
    const lines = content.split('\n');
    expect(lines[1]).toBe('name: noether');
    expect(lines[2].startsWith('description: ')).toBe(true);
    expect(lines[2]).toContain('noether');
    const closing = lines.indexOf('---', 1);
    const block = lines.slice(0, closing + 1);
    expect(block.every(l => !l.startsWith('when_to_use:'))).toBe(true);
    expect(lines[closing + 1]).toBe('');
    expect(lines[closing + 2]).toBe('# noether');
  });

  it('emits explicit frontmatter', () => {
    const content = generateSkill(sampleTree(), undefined, {
      description: 'Run Noether pipelines.',
      whenToUse: 'Use when deploying.',
    });
    const lines = content.split('\n');
    expect(lines).toContain('description: Run Noether pipelines.');
    expect(lines).toContain('when_to_use: Use when deploying.');
  });

  it('collapses newlines in frontmatter values', () => {
    const content = generateSkill(sampleTree(), undefined, { description: 'A\nB' });
    const lines = content.split('\n');
    expect(lines).toContain('description: A B');
  });

  it('quotes default description (contains colon-space) for strict YAML parsers', () => {
    const content = generateSkill(sampleTree());
    const lines = content.split('\n');
    // Default description contains "Commands: " (colon-space) → must be quoted.
    expect(lines[2].startsWith('description: "')).toBe(true);
    expect(lines[2].endsWith('"')).toBe(true);
  });

  it('quotes and escapes user-supplied values that need it', () => {
    const content = generateSkill(sampleTree(), undefined, {
      description: 'Usage: foo; see "bar" --- for details',
      whenToUse: 'has # and : both',
    });
    expect(content).toContain('description: "Usage: foo; see \\"bar\\" --- for details"');
    expect(content).toContain('when_to_use: "has # and : both"');
  });

  it('leaves plain values unquoted', () => {
    const content = generateSkill(sampleTree(), undefined, {
      description: 'Run Noether pipelines.',
    });
    expect(content).toContain('description: Run Noether pipelines.');
  });
});

// ── AcliApp ──────────────────────────────────────────────────────────────────

describe('AcliApp', () => {
  it('creates app with name and version', () => {
    const app = new AcliApp('myapp', '1.0.0');
    expect(app.name).toBe('myapp');
    expect(app.version).toBe('1.0.0');
  });

  it('registers commands and builds tree', () => {
    const app = new AcliApp('myapp', '1.0.0');
    app.command('greet', 'Greet someone', {
      examples: [['Greet world', 'myapp greet --name world'], ['Greet Joe', 'myapp greet --name joe']],
      idempotent: true,
    }, () => {});

    const tree = app.commandTree();
    const userCmds = tree.commands.filter(c => !['introspect', 'version', 'skill'].includes(c.name));
    expect(userCmds.length).toBe(1);
    expect(userCmds[0].name).toBe('greet');
    expect(userCmds[0].idempotent).toBe(true);
  });

  it('auto-injects --output on commands', () => {
    const app = new AcliApp('myapp', '1.0.0');
    app.command('greet', 'Greet', {
      examples: [['A', 'x'], ['B', 'y']],
      idempotent: true,
    }, () => {});

    const cmd = app.commandTree().commands.find(c => c.name === 'greet')!;
    expect(cmd.options.some(o => o.name === 'output')).toBe(true);
  });

  it('auto-injects --dry-run on non-idempotent commands', () => {
    const app = new AcliApp('myapp', '1.0.0');
    app.command('deploy', 'Deploy', {
      examples: [['A', 'x'], ['B', 'y']],
      idempotent: false,
    }, () => {});

    const cmd = app.commandTree().commands.find(c => c.name === 'deploy')!;
    expect(cmd.options.some(o => o.name === 'dry_run')).toBe(true);
  });

  it('does NOT inject --dry-run on idempotent commands', () => {
    const app = new AcliApp('myapp', '1.0.0');
    app.command('get', 'Get data', {
      examples: [['A', 'x'], ['B', 'y']],
      idempotent: true,
    }, () => {});

    const cmd = app.commandTree().commands.find(c => c.name === 'get')!;
    expect(cmd.options.some(o => o.name === 'dry_run')).toBe(false);
  });

  it('chains .option() to add custom options', () => {
    const app = new AcliApp('myapp', '1.0.0');
    app
      .command('greet', 'Greet', {
        examples: [['A', 'x'], ['B', 'y']],
        idempotent: true,
      }, () => {})
      .option('--name <name>', 'Who to greet');

    const cmd = app.commandTree().commands.find(c => c.name === 'greet')!;
    expect(cmd.options.some(o => o.name === 'name')).toBe(true);
  });
});
