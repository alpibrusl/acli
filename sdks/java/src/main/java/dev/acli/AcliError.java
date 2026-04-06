package dev.acli;

/** Base error for ACLI commands — actionable per spec §4. */
public class AcliError extends RuntimeException {

    private final ExitCode code;
    private final String hint;
    private final String docs;
    private final String command;

    public AcliError(String message) {
        this(message, ExitCode.GENERAL_ERROR, null, null, null);
    }

    public AcliError(String message, ExitCode code) {
        this(message, code, null, null, null);
    }

    public AcliError(String message, ExitCode code, String hint, String docs, String command) {
        super(message);
        this.code = code != null ? code : ExitCode.GENERAL_ERROR;
        this.hint = hint;
        this.docs = docs;
        this.command = command;
    }

    public ExitCode getCode() {
        return code;
    }

    public String getHint() {
        return hint;
    }

    public String getDocs() {
        return docs;
    }

    public String getCommand() {
        return command;
    }

    public static final class InvalidArgsError extends AcliError {
        public InvalidArgsError(String message, String hint, String docs) {
            super(message, ExitCode.INVALID_ARGS, hint, docs, null);
        }
    }

    public static final class NotFoundError extends AcliError {
        public NotFoundError(String message, String hint, String docs) {
            super(message, ExitCode.NOT_FOUND, hint, docs, null);
        }
    }

    public static final class ConflictError extends AcliError {
        public ConflictError(String message, String hint, String docs) {
            super(message, ExitCode.CONFLICT, hint, docs, null);
        }
    }

    public static final class PreconditionError extends AcliError {
        public PreconditionError(String message, String hint, String docs) {
            super(message, ExitCode.PRECONDITION_FAILED, hint, docs, null);
        }
    }
}
