package acli

// AcliError is an actionable error (spec §4).
type AcliError struct {
	Message string
	Code    ExitCode
	Hint    string
	Docs    string
	Command string
}

func (e *AcliError) Error() string {
	return e.Message
}

// Err returns a new AcliError with the given code.
func Err(message string, code ExitCode) *AcliError {
	return &AcliError{Message: message, Code: code}
}

// WithHint sets the hint.
func (e *AcliError) WithHint(h string) *AcliError {
	e.Hint = h
	return e
}

// WithDocs sets the docs path.
func (e *AcliError) WithDocs(d string) *AcliError {
	e.Docs = d
	return e
}

// WithCommand sets the command name for JSON envelopes.
func (e *AcliError) WithCommand(cmd string) *AcliError {
	e.Command = cmd
	return e
}
