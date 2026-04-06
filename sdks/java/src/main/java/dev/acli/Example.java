package dev.acli;

import com.fasterxml.jackson.annotation.JsonInclude;

/** A concrete usage example in the introspection tree. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Example(String description, String invocation) {}
