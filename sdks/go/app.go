package acli

import (
	"encoding/json"
	"fmt"
	"os"
)

// App holds ACLI application state (Rust-style handlers).
type App struct {
	Name    string
	Version string
	Tree    *CommandTree
	CliDir  string
}

// NewApp creates an app with an empty command tree.
func NewApp(name, version string) *App {
	return &App{
		Name:    name,
		Version: version,
		Tree:    NewCommandTree(name, version),
	}
}

// WithCliDir sets the directory used as parent for `.cli/`.
func (a *App) WithCliDir(dir string) *App {
	a.CliDir = dir
	return a
}

// RegisterCommand appends command metadata for introspection.
func (a *App) RegisterCommand(info CommandInfo) {
	a.Tree.Commands = append(a.Tree.Commands, info)
}

// HandleIntrospect writes the command tree (and updates .cli/ when needed).
func (a *App) HandleIntrospect(output OutputFormat) error {
	if NeedsUpdate(a.Tree, a.CliDir) {
		if _, err := GenerateCliFolder(a.Tree, a.CliDir); err != nil {
			return err
		}
	}
	env := SuccessEnvelope("introspect", a.Tree, a.Version, nil)
	return EmitStdout(env, output)
}

// HandleVersion prints version info.
func (a *App) HandleVersion(output OutputFormat) error {
	if output == OutputJSON {
		data := map[string]any{
			"tool": a.Name, "version": a.Version, "acli_version": "0.1.0",
		}
		env := SuccessEnvelope("version", data, a.Version, nil)
		return EmitStdout(env, output)
	}
	_, _ = os.Stdout.WriteString(a.Name + " " + a.Version + "\nacli 0.1.0\n")
	if NeedsUpdate(a.Tree, a.CliDir) {
		_, _ = GenerateCliFolder(a.Tree, a.CliDir)
	}
	return nil
}

// HandleSkill writes SKILLS.md content or JSON envelope.
func (a *App) HandleSkill(outPath string, output OutputFormat) error {
	content, err := GenerateSkill(a.Tree, "")
	if err != nil {
		return err
	}
	if output == OutputJSON {
		data := map[string]any{"content": content}
		if outPath != "" {
			data["path"] = outPath
		} else {
			data["path"] = nil
		}
		env := SuccessEnvelope("skill", data, a.Version, nil)
		return EmitStdout(env, output)
	}
	if outPath != "" {
		if err := os.WriteFile(outPath, []byte(content), 0o644); err != nil {
			return err
		}
		_, err = fmt.Fprintf(os.Stdout, "Skill file written to %s\n", outPath)
		return err
	}
	_, err = os.Stdout.WriteString(content)
	return err
}

// HandleError emits a JSON error envelope and returns the exit code.
func (a *App) HandleError(err *AcliError) int {
	cmd := err.Command
	if cmd == "" {
		cmd = a.Name
	}
	env := ErrorEnvelope(cmd, err.Code, err.Message, err.Hint, err.Docs, a.Version, nil)
	_ = EmitStdout(env, OutputJSON)
	return err.Code.Int()
}

// HandleAcliVersion prints only the ACLI spec version (introspect --acli-version).
func HandleAcliVersion(output OutputFormat) error {
	if output == OutputJSON {
		m := map[string]string{"acli_version": "0.1.0"}
		b, err := json.Marshal(m)
		if err != nil {
			return err
		}
		_, err = os.Stdout.Write(append(b, '\n'))
		return err
	}
	_, err := os.Stdout.WriteString("acli 0.1.0\n")
	return err
}
