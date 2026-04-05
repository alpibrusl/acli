[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{name}}"
version = "{{version}}"
description = "An ACLI-compliant CLI tool"
requires-python = ">=3.10"
dependencies = ["acli-spec"]

[tool.hatch.build.targets.wheel]
packages = ["src/{{name}}"]
