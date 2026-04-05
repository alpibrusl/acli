"""Entry point for {{name}}."""

import typer

from acli import ACLIApp, OutputFormat, acli_command, emit, success_envelope

app = ACLIApp(name="{{name}}", version="{{version}}")


@app.command()
@acli_command(
    examples=[
        ("Run hello", "{{name}} hello --name world"),
        ("Run hello formally", "{{name}} hello --name world --formal"),
    ],
    idempotent=True,
)
def hello(
    name: str = typer.Option(..., help="Who to greet. type:string"),
    formal: bool = typer.Option(False, help="Use formal greeting. type:bool"),
    output: OutputFormat = typer.Option(OutputFormat.text),
) -> None:
    """Greet someone."""
    greeting = f"Good day, {name}." if formal else f"Hello, {name}!"
    data = {"greeting": greeting}
    emit(success_envelope("hello", data, version="{{version}}"), output)


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
