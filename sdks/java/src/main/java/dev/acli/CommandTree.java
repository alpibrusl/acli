package dev.acli;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;

/** Full command tree as specified in ACLI spec §1.2. */
public final class CommandTree {

    private String name;
    private String version;

    @JsonProperty("acli_version")
    private String acliVersion = "0.1.0";

    private List<CommandInfo> commands = new ArrayList<>();

    public CommandTree() {}

    public CommandTree(String name, String version) {
        this.name = name;
        this.version = version;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getAcliVersion() {
        return acliVersion;
    }

    public void setAcliVersion(String acliVersion) {
        this.acliVersion = acliVersion;
    }

    public List<CommandInfo> getCommands() {
        return commands;
    }

    public void setCommands(List<CommandInfo> commands) {
        this.commands = commands;
    }

    public void addCommand(CommandInfo cmd) {
        commands.add(cmd);
    }
}
