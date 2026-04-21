package acli

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func sampleSkillTree() *CommandTree {
	tree := NewCommandTree("noether", "1.0.0")
	tree.Commands = []CommandInfo{
		{
			Name: "run", Description: "Run a pipeline",
			Idempotent: false,
			Examples:   []Example{{"Run basic", "noether run --file x.yaml"}},
		},
		{Name: "introspect", Description: "Introspect"},
		{Name: "version", Description: "Version"},
		{Name: "skill", Description: "Skill"},
	}
	return tree
}

func TestExitCodeWireName(t *testing.T) {
	if InvalidArgs.WireName() != "INVALID_ARGS" {
		t.Fatal(InvalidArgs.WireName())
	}
}

func TestSuccessEnvelope(t *testing.T) {
	start := time.Now()
	env := SuccessEnvelope("run", map[string]any{"x": 1}, "1.0.0", &start)
	if !env.OK || env.Command != "run" {
		t.Fatal(env)
	}
}

func TestSuggestFlag(t *testing.T) {
	if got := SuggestFlag("pipline", []string{"pipeline", "env"}); got != "pipeline" {
		t.Fatal(got)
	}
}

func TestCliFolder(t *testing.T) {
	dir := t.TempDir()
	tree := NewCommandTree("t", "1.0.0")
	tree.Commands = []CommandInfo{
		{Name: "greet", Description: "hi", Examples: []Example{{"a", "t greet"}}},
	}
	root, err := GenerateCliFolder(tree, dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(root, "commands.json")); err != nil {
		t.Fatal(err)
	}
}

func TestAppHandleError(t *testing.T) {
	a := NewApp("x", "1.0.0")
	code := a.HandleError(Err("bad", NotFound).WithCommand("run"))
	if code != 3 {
		t.Fatal(code)
	}
}

func TestSkillEmitsDefaultFrontmatter(t *testing.T) {
	content, err := GenerateSkill(sampleSkillTree(), "")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(content, "---\n") {
		t.Fatalf("no frontmatter: %q", content[:40])
	}
	lines := strings.Split(content, "\n")
	if lines[1] != "name: noether" {
		t.Errorf("want name line, got %q", lines[1])
	}
	if !strings.HasPrefix(lines[2], "description: ") {
		t.Errorf("want description line, got %q", lines[2])
	}
	closing := 0
	for i := 1; i < len(lines); i++ {
		if lines[i] == "---" {
			closing = i
			break
		}
	}
	if closing == 0 {
		t.Fatal("no closing ---")
	}
	for _, l := range lines[:closing+1] {
		if strings.HasPrefix(l, "when_to_use:") {
			t.Errorf("unexpected when_to_use: %q", l)
		}
	}
	if lines[closing+1] != "" {
		t.Errorf("expected blank line, got %q", lines[closing+1])
	}
	if lines[closing+2] != "# noether" {
		t.Errorf("expected # noether, got %q", lines[closing+2])
	}
}

func TestSkillEmitsExplicitFrontmatter(t *testing.T) {
	content, err := GenerateSkillWith(sampleSkillTree(), "", SkillOptions{
		Description: "Run Noether pipelines.",
		WhenToUse:   "Use when deploying.",
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(content, "description: Run Noether pipelines.") {
		t.Error("missing description")
	}
	if !strings.Contains(content, "when_to_use: Use when deploying.") {
		t.Error("missing when_to_use")
	}
}

func TestSkillCollapsesNewlines(t *testing.T) {
	content, err := GenerateSkillWith(sampleSkillTree(), "", SkillOptions{
		Description: "Line 1\nLine 2",
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(content, "description: Line 1 Line 2") {
		t.Errorf("newlines not collapsed: %s", content[:200])
	}
}
