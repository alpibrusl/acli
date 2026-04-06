/** Introspection and command-tree builder per ACLI spec §1.2. */

export interface Example {
  description: string;
  invocation: string;
}

export interface ParamInfo {
  name: string;
  type: string;
  description: string;
  default?: unknown;
  required?: boolean;
}

export interface CommandInfo {
  name: string;
  description: string;
  arguments: ParamInfo[];
  options: ParamInfo[];
  subcommands: CommandInfo[];
  idempotent?: boolean | 'conditional';
  examples?: Example[];
  see_also?: string[];
}

export interface CommandTree {
  name: string;
  version: string;
  acli_version: string;
  commands: CommandInfo[];
}

/** Create a new command tree. */
export function createCommandTree(name: string, version: string): CommandTree {
  return { name, version, acli_version: '0.1.0', commands: [] };
}

/** Builder for CommandInfo with fluent API. */
export class CommandInfoBuilder {
  private info: CommandInfo;

  constructor(name: string, description: string) {
    this.info = {
      name,
      description,
      arguments: [],
      options: [],
      subcommands: [],
    };
  }

  idempotent(value: boolean | 'conditional'): this {
    this.info.idempotent = value;
    return this;
  }

  withExamples(pairs: [string, string][]): this {
    this.info.examples = pairs.map(([description, invocation]) => ({
      description,
      invocation,
    }));
    return this;
  }

  withSeeAlso(refs: string[]): this {
    this.info.see_also = refs;
    return this;
  }

  addOption(
    name: string,
    type: string,
    description: string,
    defaultValue?: unknown,
  ): this {
    this.info.options.push({
      name,
      type,
      description,
      default: defaultValue,
    });
    return this;
  }

  addArgument(
    name: string,
    type: string,
    description: string,
    required = true,
  ): this {
    this.info.arguments.push({ name, type, description, required });
    return this;
  }

  build(): CommandInfo {
    return { ...this.info };
  }
}

/** Shorthand to create a CommandInfoBuilder. */
export function command(name: string, description: string): CommandInfoBuilder {
  return new CommandInfoBuilder(name, description);
}
