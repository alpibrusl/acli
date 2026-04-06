package dev.acli;

/** Supported output formats per ACLI spec §2.1. */
public enum OutputFormat {
    text,
    json,
    table;

    public static OutputFormat parse(String s) {
        if (s == null) {
            return text;
        }
        return switch (s.toLowerCase()) {
            case "json" -> json;
            case "table" -> table;
            default -> text;
        };
    }
}
