package acli

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

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
