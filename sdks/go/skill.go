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

// GenerateSkill builds SKILLS.md content; if path is non-empty, writes the file.
func GenerateSkill(tree *CommandTree, path string) (string, error) {
	name := tree.Name
	ver := tree.Version
	var b strings.Builder
	fmt.Fprintf(&b, "# %s\n\n", name)
	fmt.Fprintf(&b, "> Auto-generated skill file for `%s` v%s\n", name, ver)
	fmt.Fprintf(&b, "> Re-generate with: `%s skill` or `acli skill --bin %s`\n\n", name, name)
	b.WriteString("## Available commands\n\n")
	for _, cmd := range tree.Commands {
		if _, skip := builtinCommands[cmd.Name]; skip {
			continue
		}
		tag := skillIdemTag(cmd)
		fmt.Fprintf(&b, "- `%s %s` — %s%s\n", name, cmd.Name, cmd.Description, tag)
	}
	b.WriteString("\n")
	for _, cmd := range tree.Commands {
		if _, skip := builtinCommands[cmd.Name]; skip {
			continue
		}
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
