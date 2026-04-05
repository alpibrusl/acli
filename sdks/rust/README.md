# acli (Rust SDK)

Rust SDK for the [ACLI (Agent-friendly CLI) specification](../../ACLI_SPEC.md).

Build CLI tools that AI agents can discover, learn, and use autonomously. Wraps [clap](https://docs.rs/clap) with ACLI spec enforcement.

## Usage

```toml
[dependencies]
acli = "0.1"
clap = { version = "4", features = ["derive"] }
```

```rust
use acli::{AcliApp, acli_command, OutputFormat, Envelope};
use clap::Parser;

#[derive(Parser)]
struct GetArgs {
    #[arg(long, help = "City name. type:string")]
    city: String,

    #[arg(long, default_value = "text", help = "Output format. type:enum[text|json|table]")]
    output: OutputFormat,
}

fn main() {
    let app = AcliApp::new("weather", "1.0.0");
    // ...
}
```

## License

[EUPL-1.2](../../LICENSE)
