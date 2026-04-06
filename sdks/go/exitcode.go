package acli

// ExitCode is the ACLI semantic exit code schema (spec §3).
type ExitCode int

const (
	Success ExitCode = iota
	GeneralError
	InvalidArgs
	NotFound
	PermissionDenied
	Conflict
	Timeout
	UpstreamError
	PreconditionFailed
	DryRun
)

// WireName returns the JSON error code string (e.g. INVALID_ARGS).
func (e ExitCode) WireName() string {
	switch e {
	case Success:
		return "SUCCESS"
	case GeneralError:
		return "GENERAL_ERROR"
	case InvalidArgs:
		return "INVALID_ARGS"
	case NotFound:
		return "NOT_FOUND"
	case PermissionDenied:
		return "PERMISSION_DENIED"
	case Conflict:
		return "CONFLICT"
	case Timeout:
		return "TIMEOUT"
	case UpstreamError:
		return "UPSTREAM_ERROR"
	case PreconditionFailed:
		return "PRECONDITION_FAILED"
	case DryRun:
		return "DRY_RUN"
	default:
		return "UNKNOWN"
	}
}

// Int returns the numeric exit code.
func (e ExitCode) Int() int {
	return int(e)
}
