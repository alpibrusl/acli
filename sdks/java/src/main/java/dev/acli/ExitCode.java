package dev.acli;

/** Semantic exit codes as defined by ACLI spec §3. */
public enum ExitCode {
    SUCCESS(0, "SUCCESS"),
    GENERAL_ERROR(1, "GENERAL_ERROR"),
    INVALID_ARGS(2, "INVALID_ARGS"),
    NOT_FOUND(3, "NOT_FOUND"),
    PERMISSION_DENIED(4, "PERMISSION_DENIED"),
    CONFLICT(5, "CONFLICT"),
    TIMEOUT(6, "TIMEOUT"),
    UPSTREAM_ERROR(7, "UPSTREAM_ERROR"),
    PRECONDITION_FAILED(8, "PRECONDITION_FAILED"),
    DRY_RUN(9, "DRY_RUN");

    private final int code;
    private final String wireName;

    ExitCode(int code, String wireName) {
        this.code = code;
        this.wireName = wireName;
    }

    public int code() {
        return code;
    }

    /** Name used in JSON error envelopes (e.g. {@code INVALID_ARGS}). */
    public String wireName() {
        return wireName;
    }
}
