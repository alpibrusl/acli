package dev.acli;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.PrintStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import java.util.Map;

/** Output format handling and JSON envelope per ACLI spec §2. */
public final class Output {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private Output() {}

    public static ObjectMapper mapper() {
        return MAPPER;
    }

    public static ObjectNode successEnvelope(
            String command, JsonNode data, String version, Long startTimeMs) {
        long duration = durationMs(startTimeMs);
        ObjectNode root = MAPPER.createObjectNode();
        root.put("ok", true);
        root.put("command", command);
        root.set("data", data);
        ObjectNode meta = MAPPER.createObjectNode();
        meta.put("duration_ms", duration);
        meta.put("version", version);
        root.set("meta", meta);
        return root;
    }

    public static ObjectNode dryRunEnvelope(
            String command,
            JsonNode plannedActions,
            String version,
            Long startTimeMs) {
        long duration = durationMs(startTimeMs);
        ObjectNode root = MAPPER.createObjectNode();
        root.put("ok", true);
        root.put("command", command);
        root.put("dry_run", true);
        root.set("planned_actions", plannedActions);
        ObjectNode meta = MAPPER.createObjectNode();
        meta.put("duration_ms", duration);
        meta.put("version", version);
        root.set("meta", meta);
        return root;
    }

    public static ObjectNode errorEnvelope(
            String command,
            ExitCode code,
            String message,
            String hint,
            String docs,
            String version,
            Long startTimeMs) {
        long duration = durationMs(startTimeMs);
        ObjectNode root = MAPPER.createObjectNode();
        root.put("ok", false);
        root.put("command", command);
        ObjectNode err = MAPPER.createObjectNode();
        err.put("code", code.wireName());
        err.put("message", message);
        if (hint != null) {
            err.put("hint", hint);
        }
        if (docs != null) {
            err.put("docs", docs);
        }
        root.set("error", err);
        ObjectNode meta = MAPPER.createObjectNode();
        meta.put("duration_ms", duration);
        meta.put("version", version);
        root.set("meta", meta);
        return root;
    }

    private static long durationMs(Long startTimeMs) {
        if (startTimeMs == null) {
            return 0;
        }
        return Math.max(0, System.currentTimeMillis() - startTimeMs);
    }

    /** Emit a progress line as NDJSON per spec §2.3. */
    public static void emitProgress(PrintStream out, String step, String status, String detail) {
        ObjectNode line = MAPPER.createObjectNode();
        line.put("type", "progress");
        line.put("step", step);
        line.put("status", status);
        if (detail != null) {
            line.put("detail", detail);
        }
        writeNdjson(out, line);
    }

    /** Emit a final result line as NDJSON per spec §2.3. */
    public static void emitResult(PrintStream out, JsonNode data, boolean ok) {
        ObjectNode line = MAPPER.createObjectNode();
        line.put("type", "result");
        line.put("ok", ok);
        if (data != null && data.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> fields = data.fields();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> e = fields.next();
                line.set(e.getKey(), e.getValue());
            }
        }
        writeNdjson(out, line);
    }

    private static void writeNdjson(PrintStream out, ObjectNode line) {
        try {
            out.write((MAPPER.writeValueAsString(line) + "\n").getBytes(StandardCharsets.UTF_8));
            out.flush();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public static void emit(JsonNode envelope, OutputFormat format) {
        emit(envelope, format, System.out, System.err);
    }

    public static void emit(
            JsonNode envelope, OutputFormat format, PrintStream stdout, PrintStream stderr) {
        switch (format) {
            case json -> writeJson(stdout, envelope);
            case table -> emitTable(stdout, envelope);
            case text -> emitText(envelope, stdout, stderr);
        }
    }

    private static void writeJson(PrintStream out, JsonNode envelope) {
        try {
            out.write((MAPPER.writeValueAsString(envelope) + "\n").getBytes(StandardCharsets.UTF_8));
            out.flush();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    private static void emitText(JsonNode envelope, PrintStream stdout, PrintStream stderr) {
        boolean ok = envelope.path("ok").asBoolean(true);
        if (!ok && envelope.has("error")) {
            JsonNode err = envelope.get("error");
            String code = err.path("code").asText("GENERAL_ERROR");
            String msg = err.path("message").asText("");
            stderr.println("Error [" + code + "]: " + msg);
            if (err.hasNonNull("hint")) {
                stderr.println("  " + err.get("hint").asText());
            }
            if (err.hasNonNull("docs")) {
                stderr.println("  Reference: " + err.get("docs").asText());
            }
            return;
        }
        if (envelope.has("data") && envelope.get("data").isObject()) {
            JsonNode data = envelope.get("data");
            Iterator<String> names = data.fieldNames();
            while (names.hasNext()) {
                String key = names.next();
                stdout.println(key + ": " + data.get(key).toString());
            }
        }
    }

    private static void emitTable(PrintStream out, JsonNode envelope) {
        if (!envelope.has("data")) {
            return;
        }
        JsonNode data = envelope.get("data");
        if (data.isArray() && data.size() > 0 && data.get(0).isObject()) {
            // simple table from array of objects
            JsonNode first = data.get(0);
            Iterator<String> headers = first.fieldNames();
            StringBuilder headerLine = new StringBuilder();
            while (headers.hasNext()) {
                if (headerLine.length() > 0) {
                    headerLine.append("  ");
                }
                headerLine.append(headers.next());
            }
            out.println(headerLine);
        } else if (data.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> it = data.fields();
            while (it.hasNext()) {
                Map.Entry<String, JsonNode> e = it.next();
                out.println(e.getKey() + "  " + e.getValue());
            }
        }
    }
}
