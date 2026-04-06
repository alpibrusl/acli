package acli

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// GenerateCliFolder writes .cli/ per spec §1.3.
func GenerateCliFolder(tree *CommandTree, targetDir string) (string, error) {
	root := filepath.Join(targetDir, ".cli")
	if targetDir == "" {
		root = ".cli"
	}
	if err := os.MkdirAll(filepath.Join(root, "examples"), 0o755); err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Join(root, "schemas"), 0o755); err != nil {
		return "", err
	}

	b, err := json.MarshalIndent(tree, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(filepath.Join(root, "commands.json"), append(b, '\n'), 0o644); err != nil {
		return "", err
	}
	if err := writeReadme(root, tree); err != nil {
		return "", err
	}
	if err := writeExamples(root, tree); err != nil {
		return "", err
	}
	changelog := filepath.Join(root, "changelog.md")
	if _, err := os.Stat(changelog); os.IsNotExist(err) {
		body := fmt.Sprintf("# Changelog\n\n## %s\n\n- Initial release\n", tree.Version)
		if err := os.WriteFile(changelog, []byte(body), 0o644); err != nil {
			return "", err
		}
	}
	return root, nil
}

func writeReadme(cliDir string, tree *CommandTree) error {
	var lines []string
	lines = append(lines, "# "+tree.Name, "")
	lines = append(lines, "Version: "+tree.Version)
	lines = append(lines, "ACLI version: "+tree.AcliVersion, "")
	lines = append(lines, "## Commands", "")
	for _, cmd := range tree.Commands {
		lines = append(lines, "### "+cmd.Name, "", cmd.Description, "")
		if cmd.Idempotent != nil {
			lines = append(lines, fmt.Sprintf("Idempotent: %v", cmd.Idempotent), "")
		}
	}
	return os.WriteFile(filepath.Join(cliDir, "README.md"), []byte(joinLines(lines)), 0o644)
}

func writeExamples(cliDir string, tree *CommandTree) error {
	for _, cmd := range tree.Commands {
		if len(cmd.Examples) == 0 {
			continue
		}
		var lines []string
		lines = append(lines, "#!/usr/bin/env bash", fmt.Sprintf("# Examples for: %s", cmd.Name), "")
		for _, ex := range cmd.Examples {
			lines = append(lines, "# "+ex.Description, ex.Invocation, "")
		}
		p := filepath.Join(cliDir, "examples", cmd.Name+".sh")
		if err := os.WriteFile(p, []byte(joinLines(lines)), 0o644); err != nil {
			return err
		}
	}
	return nil
}

func joinLines(lines []string) string {
	out := ""
	for i, l := range lines {
		if i > 0 {
			out += "\n"
		}
		out += l
	}
	return out + "\n"
}

// NeedsUpdate returns true if .cli/commands.json is missing or stale.
func NeedsUpdate(tree *CommandTree, targetDir string) bool {
	root := filepath.Join(targetDir, ".cli")
	if targetDir == "" {
		root = ".cli"
	}
	p := filepath.Join(root, "commands.json")
	data, err := os.ReadFile(p)
	if err != nil {
		return true
	}
	var existing map[string]any
	if err := json.Unmarshal(data, &existing); err != nil {
		return true
	}
	cur, err := json.Marshal(tree)
	if err != nil {
		return true
	}
	var curMap map[string]any
	if err := json.Unmarshal(cur, &curMap); err != nil {
		return true
	}
	b1, _ := json.Marshal(existing)
	b2, _ := json.Marshal(curMap)
	return string(b1) != string(b2)
}
