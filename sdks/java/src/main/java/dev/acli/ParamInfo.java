package dev.acli;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/** Parameter metadata (argument or option) per spec §1.2. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ParamInfo(
        String name,
        @JsonProperty("type") String paramType,
        String description,
        @JsonProperty("default") JsonNode defaultValue,
        Boolean required) {

    public ParamInfo(String name, String paramType, String description) {
        this(name, paramType, description, null, null);
    }
}
