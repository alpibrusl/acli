package acli

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"
)

// OutputFormat is spec §2.1.
type OutputFormat string

const (
	OutputText  OutputFormat = "text"
	OutputJSON  OutputFormat = "json"
	OutputTable OutputFormat = "table"
)

// ParseOutput parses text/json/table (case-insensitive).
func ParseOutput(s string) OutputFormat {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "json":
		return OutputJSON
	case "table":
		return OutputTable
	default:
		return OutputText
	}
}

// Meta is envelope metadata.
type Meta struct {
	DurationMs int64  `json:"duration_ms"`
	Version    string `json:"version"`
}

// ErrorDetail is the error object in JSON envelopes.
type ErrorDetail struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Hint    string `json:"hint,omitempty"`
	Docs    string `json:"docs,omitempty"`
}

// Envelope is the standard JSON envelope (spec §2.2).
type Envelope struct {
	OK              bool           `json:"ok"`
	Command         string         `json:"command"`
	Data            any            `json:"data,omitempty"`
	DryRun          *bool          `json:"dry_run,omitempty"`
	PlannedActions  []any          `json:"planned_actions,omitempty"`
	Error           *ErrorDetail   `json:"error,omitempty"`
	Meta            Meta           `json:"meta"`
}

// SuccessEnvelope builds a success envelope.
func SuccessEnvelope(command string, data any, version string, start *time.Time) Envelope {
	var ms int64
	if start != nil {
		ms = time.Since(*start).Milliseconds()
	}
	return Envelope{
		OK:      true,
		Command: command,
		Data:    data,
		Meta:    Meta{DurationMs: ms, Version: version},
	}
}

// DryRunEnvelope builds a dry-run success envelope.
func DryRunEnvelope(command string, planned []any, version string, start *time.Time) Envelope {
	t := true
	var ms int64
	if start != nil {
		ms = time.Since(*start).Milliseconds()
	}
	return Envelope{
		OK:             true,
		Command:        command,
		DryRun:         &t,
		PlannedActions: planned,
		Meta:           Meta{DurationMs: ms, Version: version},
	}
}

// ErrorEnvelope builds an error envelope.
func ErrorEnvelope(command string, code ExitCode, message, hint, docs, version string, start *time.Time) Envelope {
	var ms int64
	if start != nil {
		ms = time.Since(*start).Milliseconds()
	}
	ed := &ErrorDetail{Code: code.WireName(), Message: message}
	if hint != "" {
		ed.Hint = hint
	}
	if docs != "" {
		ed.Docs = docs
	}
	return Envelope{
		OK:      false,
		Command: command,
		Error:   ed,
		Meta:    Meta{DurationMs: ms, Version: version},
	}
}

// Emit writes an envelope to w in the requested format.
func Emit(env Envelope, fmt OutputFormat, w io.Writer, errOut io.Writer) error {
	switch fmt {
	case OutputJSON:
		b, err := json.MarshalIndent(env, "", "  ")
		if err != nil {
			return err
		}
		_, err = w.Write(append(b, '\n'))
		return err
	case OutputTable:
		return emitTable(env, w)
	default:
		return emitText(env, w, errOut)
	}
}

// EmitStdout emits to os.Stdout / os.Stderr.
func EmitStdout(env Envelope, fmt OutputFormat) error {
	return Emit(env, fmt, os.Stdout, os.Stderr)
}

func emitText(env Envelope, out, errOut io.Writer) error {
	if !env.OK && env.Error != nil {
		fmt.Fprintf(errOut, "Error [%s]: %s\n", env.Error.Code, env.Error.Message)
		if env.Error.Hint != "" {
			fmt.Fprintf(errOut, "  %s\n", env.Error.Hint)
		}
		if env.Error.Docs != "" {
			fmt.Fprintf(errOut, "  Reference: %s\n", env.Error.Docs)
		}
		return nil
	}
	if m, ok := env.Data.(map[string]any); ok {
		for k, v := range m {
			fmt.Fprintf(out, "%s: %v\n", k, v)
		}
	}
	return nil
}

func emitTable(env Envelope, out io.Writer) error {
	if m, ok := env.Data.(map[string]any); ok {
		for k, v := range m {
			fmt.Fprintf(out, "%s  %v\n", k, v)
		}
	}
	return nil
}

// EmitProgress writes one NDJSON progress line (spec §2.3).
func EmitProgress(w io.Writer, step, status, detail string) error {
	m := map[string]string{"type": "progress", "step": step, "status": status}
	if detail != "" {
		m["detail"] = detail
	}
	b, err := json.Marshal(m)
	if err != nil {
		return err
	}
	_, err = w.Write(append(b, '\n'))
	return err
}

// EmitResult writes one NDJSON result line (spec §2.3).
func EmitResult(w io.Writer, ok bool, data map[string]any) error {
	line := map[string]any{"type": "result", "ok": ok}
	for k, v := range data {
		line[k] = v
	}
	b, err := json.Marshal(line)
	if err != nil {
		return err
	}
	_, err = w.Write(append(b, '\n'))
	return err
}
