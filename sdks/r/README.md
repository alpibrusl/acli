# acli.spec (R)

R package implementing the [ACLI (Agent-friendly CLI) specification](../../ACLI_SPEC.md).

## Install (local)

```r
install.packages("jsonlite")
# From repo root:
install.packages("sdks/r", repos = NULL, type = "source")
```

Or in shell from `sdks/r`:

```bash
R CMD INSTALL .
```

## Test

From the repository root (recommended; runs `testthat` from the package source):

```bash
Rscript -e 'install.packages(c("jsonlite","testthat"), repos="https://cloud.r-project.org")'
R CMD check --no-manual sdks/r
```

Or install locally and run checks the same way from `sdks/r`.

## Usage

```r
library(acli.spec)
app <- acli_new_app("mytool", "1.0.0", cli_dir = getwd())
app <- acli_register_command(app, list(name = "get", description = "Fetch data"))
```

Pair with `argparse` or `optparse` for full CLIs.

## License

[EUPL-1.2](../../LICENSE)
