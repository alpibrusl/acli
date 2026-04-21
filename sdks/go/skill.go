package acli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

var builtinCommands = map[string]struct{}{
	"introspect": {}, "version": {}, "skill": {},
}

// SkillOptions carries caller-supplied values for the SKILL.md frontmatter
// (agentskills.io).
type SkillOptions struct {
	Description string
	WhenToUse   string
}

// GenerateSkill builds SKILL.md content using default frontmatter; if path is
// non-empty, writes the file.
func GenerateSkill(tree *CommandTree, path string) (string, error) {
	return GenerateSkillWith(tree, path, SkillOptions{})
}

// GenerateSkillWith builds SKILL.md content with caller-supplied frontmatter
// options. Conforms to the agentskills.io open standard.
func GenerateSkillWith(tree *CommandTree, path string, opts SkillOptions) (string, error) {
	name := tree.Name
	ver := tree.Version

	var userCommands []CommandInfo
	for _, cmd := range tree.Commands {
		if _, skip := builtinCommands[cmd.Name]; skip {
			continue
		}
		userCommands = append(userCommands, cmd)
	}

	description := collapseWS(opts.Description)
	if description == "" {
		description = defaultSkillDescription(name, userCommands)
	}

	var b strings.Builder
	b.WriteString("---\n")
	fmt.Fprintf(&b, "name: %s\n", name)
	fmt.Fprintf(&b, "description: %s\n", description)
	if w := collapseWS(opts.WhenToUse); w != "" {
		fmt.Fprintf(&b, "when_to_use: %s\n", w)
	}
	b.WriteString("---\n\n")

	fmt.Fprintf(&b, "# %s\n\n", name)
	fmt.Fprintf(&b, "> Auto-generated skill file for `%s` v%s\n", name, ver)
	fmt.Fprintf(&b, "> Re-generate with: `%s skill` or `acli skill --bin %s`\n\n", name, name)
	b.WriteString("## Available commands\n\n")
	for _, cmd := range userCommands {
		tag := skillIdemTag(cmd)
		fmt.Fprintf(&b, "- `%s %s` — %s%s\n", name, cmd.Name, cmd.Description, tag)
	}
	b.WriteString("\n")
	for _, cmd := range userCommands {
		fmt.Fprintf(&b, "## `%s %s`\n\n", name, cmd.Name)
		if cmd.Description != "" {
			b.WriteString(cmd.Description + "\n\n")
		}
		if len(cmd.Options) > 0 {
			b.WriteString("### Options\n\n")
			for _, o := range cmd.Options {
				def := ""
				if o.Default != nil {
					def = fmt.Sprintf(" [default: %v]", o.Default)
				}
				on := strings.ReplaceAll(o.Name, "_", "-")
				fmt.Fprintf(&b, "- `--%s` (%s) — %s%s\n", on, o.Type, o.Description, def)
			}
			b.WriteString("\n")
		}
		if len(cmd.Arguments) > 0 {
			b.WriteString("### Arguments\n\n")
			for _, a := range cmd.Arguments {
				req := "optional"
				if a.Required != nil && *a.Required {
					req = "required"
				}
				fmt.Fprintf(&b, "- `%s` (%s, %s) — %s\n", a.Name, a.Type, req, a.Description)
			}
			b.WriteString("\n")
		}
		if len(cmd.Examples) > 0 {
			b.WriteString("### Examples\n\n")
			for _, ex := range cmd.Examples {
				b.WriteString("```bash\n# " + ex.Description + "\n" + ex.Invocation + "\n```\n\n")
			}
		}
		if len(cmd.SeeAlso) > 0 {
			var refs []string
			for _, s := range cmd.SeeAlso {
				refs = append(refs, fmt.Sprintf("`%s %s`", name, s))
			}
			fmt.Fprintf(&b, "**See also:** %s\n\n", strings.Join(refs, ", "))
		}
	}
	b.WriteString("## Output format\n\n")
	b.WriteString("All commands support `--output json|text|table`. When using `--output json`, " +
		"responses follow a standard envelope:\n\n```json\n" +
		`{"ok": true, "command": "...", "data": {...}, "meta": {"duration_ms": ..., "version": "..."}}` +
		"\n```\n\n")
	b.WriteString("## Exit codes\n\n")
	b.WriteString("| Code | Meaning | Action |\n|------|---------|--------|\n")
	b.WriteString("| 0 | Success | Proceed |\n| 2 | Invalid arguments | Correct and retry |\n")
	b.WriteString("| 3 | Not found | Check inputs |\n| 5 | Conflict | Resolve conflict |\n")
	b.WriteString("| 8 | Precondition failed | Fix precondition |\n| 9 | Dry-run completed | Review and confirm |\n\n")
	b.WriteString("## Further discovery\n\n")
	fmt.Fprintf(&b, "- `%s --help` — full help for any command\n", name)
	fmt.Fprintf(&b, "- `%s introspect` — machine-readable command tree (JSON)\n", name)
	b.WriteString("- `.cli/README.md` — persistent reference (survives context resets)\n\n")
	content := b.String()
	if path != "" {
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return content, err
		}
		if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
			return content, err
		}
	}
	return content, nil
}

func collapseWS(s string) string {
	return strings.Join(strings.Fields(s), " ")
}

func defaultSkillDescription(name string, userCommands []CommandInfo) string {
	if len(userCommands) == 0 {
		return fmt.Sprintf("Invoke the `%s` CLI.", name)
	}
	n := len(userCommands)
	if n > 4 {
		n = 4
	}
	names := make([]string, n)
	for i := 0; i < n; i++ {
		names[i] = userCommands[i].Name
	}
	suffix := ""
	if len(userCommands) > 4 {
		suffix = "…"
	}
	return fmt.Sprintf("Invoke the `%s` CLI. Commands: %s%s", name, strings.Join(names, ", "), suffix)
}

func skillIdemTag(cmd CommandInfo) string {
	if cmd.Idempotent == nil {
		return ""
	}
	switch v := cmd.Idempotent.(type) {
	case bool:
		if v {
			return " (idempotent)"
		}
	case string:
		if v == "conditional" {
			return " (conditionally idempotent)"
		}
	}
	return ""
}
