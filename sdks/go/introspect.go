package acli

// Example is a concrete invocation example.
type Example struct {
	Description string `json:"description"`
	Invocation  string `json:"invocation"`
}

// ParamInfo describes an argument or option.
type ParamInfo struct {
	Name        string `json:"name"`
	Type        string `json:"type"`
	Description string `json:"description"`
	Default     any    `json:"default,omitempty"`
	Required    *bool  `json:"required,omitempty"`
}

// CommandInfo is metadata for one command (spec §1.2).
type CommandInfo struct {
	Name         string        `json:"name"`
	Description  string        `json:"description"`
	Arguments    []ParamInfo   `json:"arguments,omitempty"`
	Options      []ParamInfo   `json:"options,omitempty"`
	Subcommands  []CommandInfo `json:"subcommands,omitempty"`
	Idempotent   any           `json:"idempotent,omitempty"`
	Examples     []Example     `json:"examples,omitempty"`
	SeeAlso      []string      `json:"see_also,omitempty"`
}

// CommandTree is the introspection JSON root.
type CommandTree struct {
	Name         string        `json:"name"`
	Version      string        `json:"version"`
	AcliVersion  string        `json:"acli_version"`
	Commands     []CommandInfo `json:"commands"`
}

// NewCommandTree creates a tree with default acli_version.
func NewCommandTree(name, version string) *CommandTree {
	return &CommandTree{
		Name:        name,
		Version:     version,
		AcliVersion: "0.1.0",
		Commands:    nil,
	}
}
