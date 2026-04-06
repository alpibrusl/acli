package dev.acli;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;

/** Metadata for a single command in the introspection tree. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public final class CommandInfo {

    private String name;
    private String description;
    private List<ParamInfo> arguments = new ArrayList<>();
    private List<ParamInfo> options = new ArrayList<>();
    private List<CommandInfo> subcommands = new ArrayList<>();
    private JsonNode idempotent;
    private List<Example> examples;
    @JsonProperty("see_also")
    private List<String> seeAlso;

    public CommandInfo() {}

    public CommandInfo(String name, String description) {
        this.name = name;
        this.description = description;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<ParamInfo> getArguments() {
        return arguments;
    }

    public void setArguments(List<ParamInfo> arguments) {
        this.arguments = arguments;
    }

    public List<ParamInfo> getOptions() {
        return options;
    }

    public void setOptions(List<ParamInfo> options) {
        this.options = options;
    }

    public List<CommandInfo> getSubcommands() {
        return subcommands;
    }

    public void setSubcommands(List<CommandInfo> subcommands) {
        this.subcommands = subcommands;
    }

    public JsonNode getIdempotent() {
        return idempotent;
    }

    public void setIdempotent(JsonNode idempotent) {
        this.idempotent = idempotent;
    }

    public List<Example> getExamples() {
        return examples;
    }

    public void setExamples(List<Example> examples) {
        this.examples = examples;
    }

    public List<String> getSeeAlso() {
        return seeAlso;
    }

    public void setSeeAlso(List<String> seeAlso) {
        this.seeAlso = seeAlso;
    }
}
