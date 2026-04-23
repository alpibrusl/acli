#' @importFrom jsonlite toJSON parse_json minify write_json
#' @importFrom utils adist
NULL

`%||%` <- function(x, y) if (is.null(x)) y else x

# Exit codes (spec section 3) -- integers 0..9
acli_exit_codes <- c(
  SUCCESS = 0L, GENERAL_ERROR = 1L, INVALID_ARGS = 2L, NOT_FOUND = 3L,
  PERMISSION_DENIED = 4L, CONFLICT = 5L, TIMEOUT = 6L, UPSTREAM_ERROR = 7L,
  PRECONDITION_FAILED = 8L, DRY_RUN = 9L
)

acli_exit_wire_name <- function(code) {
  n <- c(
    "SUCCESS", "GENERAL_ERROR", "INVALID_ARGS", "NOT_FOUND", "PERMISSION_DENIED",
    "CONFLICT", "TIMEOUT", "UPSTREAM_ERROR", "PRECONDITION_FAILED", "DRY_RUN"
  )
  if (is.numeric(code) && code >= 0 && code <= 9) n[code + 1] else "UNKNOWN"
}

#' @export
acli_success_envelope <- function(command, data, version, start_time = NULL) {
  ms <- if (!is.null(start_time)) {
    as.integer(max(0, (proc.time()[3] - start_time) * 1000))
  } else 0L
  list(ok = TRUE, command = command, data = data, meta = list(duration_ms = ms, version = version))
}

#' @export
acli_dry_run_envelope <- function(command, planned_actions, version, start_time = NULL) {
  ms <- if (!is.null(start_time)) as.integer(max(0, (proc.time()[3] - start_time) * 1000)) else 0L
  list(
    ok = TRUE, command = command, dry_run = TRUE, planned_actions = planned_actions,
    meta = list(duration_ms = ms, version = version)
  )
}

#' @export
acli_error_envelope <- function(command, code, message, hint = NULL, docs = NULL, version, start_time = NULL) {
  ms <- if (!is.null(start_time)) as.integer(max(0, (proc.time()[3] - start_time) * 1000)) else 0L
  err <- list(code = acli_exit_wire_name(code), message = message)
  if (!is.null(hint)) err$hint <- hint
  if (!is.null(docs)) err$docs <- docs
  list(ok = FALSE, command = command, error = err, meta = list(duration_ms = ms, version = version))
}

#' @export
acli_emit <- function(envelope, format = c("text", "json", "table"), con_out = stdout(), con_err = stderr()) {
  format <- match.arg(format)
  if (identical(format, "json")) {
    cat(jsonlite::toJSON(envelope, auto_unbox = TRUE, pretty = TRUE, null = "null"), file = con_out, sep = "\n")
    return(invisible(NULL))
  }
  if (isFALSE(envelope$ok) && !is.null(envelope$error)) {
    e <- envelope$error
    cat(sprintf("Error [%s]: %s\n", e$code, e$message), file = con_err)
    if (!is.null(e$hint)) cat(sprintf("  %s\n", e$hint), file = con_err)
    if (!is.null(e$docs)) cat(sprintf("  Reference: %s\n", e$docs), file = con_err)
    return(invisible(NULL))
  }
  if (!is.null(envelope$data) && is.list(envelope$data)) {
    for (nm in names(envelope$data)) {
      cat(sprintf("%s: %s\n", nm, format(envelope$data[[nm]])), file = con_out)
    }
  }
  invisible(NULL)
}

#' @export
acli_emit_progress <- function(step, status, detail = NULL, con = stdout()) {
  x <- list(type = "progress", step = step, status = status)
  if (!is.null(detail)) x$detail <- detail
  cat(jsonlite::toJSON(x, auto_unbox = TRUE), file = con, sep = "\n")
}

#' @export
acli_emit_result <- function(ok, data, con = stdout()) {
  x <- c(list(type = "result", ok = ok), data)
  cat(jsonlite::toJSON(x, auto_unbox = TRUE), file = con, sep = "\n")
}

#' @export
acli_cli_folder_generate <- function(tree, target_dir = getwd()) {
  root <- file.path(target_dir, ".cli")
  dir.create(file.path(root, "examples"), recursive = TRUE, showWarnings = FALSE)
  dir.create(file.path(root, "schemas"), recursive = TRUE, showWarnings = FALSE)
  jsonlite::write_json(tree, file.path(root, "commands.json"), pretty = TRUE, auto_unbox = TRUE)
  lines <- c(
    paste("#", tree$name), "",
    paste("Version:", tree$version),
    paste("ACLI version:", tree$acli_version), "",
    "## Commands", ""
  )
  for (cmd in tree$commands) {
    lines <- c(lines, paste("###", cmd$name), "", cmd$description, "")
    if (!is.null(cmd$idempotent)) lines <- c(lines, sprintf("Idempotent: %s", cmd$idempotent), "")
  }
  writeLines(lines, file.path(root, "README.md"))
  for (cmd in tree$commands) {
    ex <- cmd$examples
    if (length(ex)) {
      el <- c("#!/usr/bin/env bash", sprintf("# Examples for: %s", cmd$name), "")
      for (e in ex) {
        el <- c(el, paste("#", e$description), e$invocation, "")
      }
      writeLines(paste(el, collapse = "\n"), file.path(root, "examples", paste0(cmd$name, ".sh")))
    }
  }
  ch <- file.path(root, "changelog.md")
  if (!file.exists(ch)) {
    writeLines(c(
      "# Changelog", "",
      sprintf("## %s", tree$version), "",
      "- Initial release", ""
    ), ch)
  }
  invisible(root)
}

#' @export
acli_cli_folder_needs_update <- function(tree, target_dir = getwd()) {
  p <- file.path(target_dir, ".cli", "commands.json")
  if (!file.exists(p)) return(TRUE)
  cur <- jsonlite::toJSON(tree, auto_unbox = TRUE)
  old <- tryCatch(readChar(p, file.info(p)$size), error = function(e) "")
  if (!nzchar(old)) return(TRUE)
  identical(jsonlite::minify(cur), jsonlite::minify(jsonlite::toJSON(jsonlite::parse_json(old), auto_unbox = TRUE)))
}

#' Collapse whitespace in a single-line frontmatter value.
#' @keywords internal
acli__collapse_ws <- function(s) {
  if (is.null(s)) return("")
  gsub("\\s+", " ", trimws(s))
}

#' Render a scalar safe for a single-line YAML block mapping value.
#' @keywords internal
acli__yaml_scalar <- function(value) {
  if (is.null(value) || !nzchar(value)) return('""')
  reserved <- c("!", "&", "*", "?", "|", ">", "'", '"', "%", "@", "`", "#",
                ",", "[", "]", "{", "}", "-", ":")
  first <- substr(value, 1, 1)
  needs_quoting <- grepl(": ", value, fixed = TRUE) ||
    grepl(" #", value, fixed = TRUE) ||
    first %in% reserved ||
    endsWith(value, ":") ||
    !identical(trimws(value), value)
  if (!needs_quoting) return(value)
  escaped <- gsub("\\", "\\\\", value, fixed = TRUE)
  escaped <- gsub('"', '\\"', escaped, fixed = TRUE)
  paste0('"', escaped, '"')
}

#' @keywords internal
acli__default_skill_description <- function(name, user_commands) {
  if (length(user_commands) == 0) {
    return(sprintf("Invoke the `%s` CLI.", name))
  }
  n <- min(4L, length(user_commands))
  shown <- vapply(user_commands[seq_len(n)], function(c) c$name, character(1))
  suffix <- if (length(user_commands) > 4) "…" else ""
  sprintf(
    "Invoke the `%s` CLI. Commands: %s%s",
    name, paste(shown, collapse = ", "), suffix
  )
}

#' Generate a SKILL.md file (agentskills.io) from an ACLI command tree.
#'
#' @param tree The command tree.
#' @param path Optional path to write the file to.
#' @param description Optional frontmatter description.
#' @param when_to_use Optional frontmatter when_to_use.
#' @export
acli_skill_generate <- function(tree, path = NULL, description = NULL, when_to_use = NULL) {
  builtin <- c("introspect", "version", "skill")
  name <- tree$name
  ver <- tree$version

  user_commands <- Filter(function(c) !(c$name %in% builtin), tree$commands)

  desc <- acli__collapse_ws(description)
  if (!nzchar(desc)) {
    desc <- acli__default_skill_description(name, user_commands)
  }

  b <- character()
  b <- c(b, "---\n")
  b <- c(b, sprintf("name: %s\n", acli__yaml_scalar(name)))
  b <- c(b, sprintf("description: %s\n", acli__yaml_scalar(desc)))
  wtu <- acli__collapse_ws(when_to_use)
  if (nzchar(wtu)) {
    b <- c(b, sprintf("when_to_use: %s\n", acli__yaml_scalar(wtu)))
  }
  b <- c(b, "---\n\n")

  b <- c(b, sprintf("# %s\n", name))
  b <- c(b, "\n")
  b <- c(b, sprintf("> Auto-generated skill file for `%s` v%s\n", name, ver))
  b <- c(b, sprintf("> Re-generate with: `%s skill` or `acli skill --bin %s`\n\n", name, name))
  b <- c(b, "## Available commands\n\n")
  for (cmd in user_commands) {
    tag <- ""
    if (isTRUE(cmd$idempotent)) tag <- " (idempotent)"
    if (identical(cmd$idempotent, "conditional")) tag <- " (conditionally idempotent)"
    b <- c(b, sprintf("- `%s %s` -- %s%s\n", name, cmd$name, cmd$description, tag))
  }
  b <- c(b, "\n")
  for (cmd in user_commands) {
    b <- c(b, sprintf("## `%s %s`\n\n", name, cmd$name))
    if (nzchar(cmd$description %||% "")) b <- c(b, cmd$description, "\n\n")
    if (length(cmd$options)) {
      b <- c(b, "### Options\n\n")
      for (o in cmd$options) {
        def <- if (!is.null(o$default)) sprintf(" [default: %s]", o$default) else ""
        on <- gsub("_", "-", o$name, fixed = TRUE)
        b <- c(b, sprintf("- `--%s` (%s) -- %s%s\n", on, o$type, o$description, def))
      }
      b <- c(b, "\n")
    }
  }
  b <- c(b, "## Output format\n\n", "All commands support `--output json|text|table`.\n\n")
  b <- c(b, "## Exit codes\n\n", "| Code | Meaning |\n|---|---|\n| 0 | Success |\n| 9 | Dry-run |\n\n")
  b <- c(b, "## Further discovery\n\n", sprintf("- `%s introspect`\n", name))
  content <- paste(b, collapse = "")
  if (!is.null(path)) {
    d <- dirname(path)
    if (!identical(d, ".") && !identical(d, "")) dir.create(d, recursive = TRUE, showWarnings = FALSE)
    writeLines(content, path)
  }
  content
}

#' @export
acli_suggest_flag <- function(unknown, known) {
  best <- NULL
  bestd <- 3
  for (k in known) {
    d <- adist(unknown, k)[[1]]
    if (d < bestd) {
      bestd <- d
      best <- k
    }
  }
  best
}

#' @export
acli_new_app <- function(name, version, cli_dir = getwd(),
                         skill_description = NULL, skill_when_to_use = NULL) {
  tree <- list(name = name, version = version, acli_version = "0.1.0", commands = list())
  list(
    name = name, version = version, cli_dir = cli_dir, tree = tree,
    skill_description = skill_description, skill_when_to_use = skill_when_to_use
  )
}

#' @export
acli_register_command <- function(app, cmd) {
  app$tree$commands <- c(app$tree$commands, list(cmd))
  app
}

#' @export
acli_handle_introspect <- function(app, format = "json") {
  if (acli_cli_folder_needs_update(app$tree, app$cli_dir)) {
    acli_cli_folder_generate(app$tree, app$cli_dir)
  }
  env <- acli_success_envelope("introspect", app$tree, app$version, NULL)
  acli_emit(env, format)
}

#' @export
acli_handle_version <- function(app, format = "text") {
  if (identical(format, "json")) {
    env <- acli_success_envelope("version", list(tool = app$name, version = app$version, acli_version = "0.1.0"), app$version, NULL)
    acli_emit(env, "json")
  } else {
    cat(sprintf("%s %s\n", app$name, app$version), file = stdout())
    cat("acli 0.1.0\n", file = stdout())
  }
  if (acli_cli_folder_needs_update(app$tree, app$cli_dir)) {
    acli_cli_folder_generate(app$tree, app$cli_dir)
  }
  invisible(NULL)
}

#' @export
acli_handle_skill <- function(app, out_path = NULL, format = "text") {
  content <- acli_skill_generate(
    app$tree, NULL,
    description = app$skill_description,
    when_to_use = app$skill_when_to_use
  )
  if (identical(format, "json")) {
    env <- acli_success_envelope("skill", list(path = out_path, content = content), app$version, NULL)
    acli_emit(env, "json")
  } else if (!is.null(out_path)) {
    writeLines(content, out_path)
    cat(sprintf("Skill file written to %s\n", out_path), file = stdout())
  } else {
    cat(content, file = stdout())
  }
  invisible(NULL)
}

#' @export
acli_handle_error <- function(app, err) {
  cmd <- err$command %||% app$name
  env <- acli_error_envelope(cmd, err$code, err$message, err$hint, err$docs, app$version, NULL)
  acli_emit(env, "json")
  err$code
}

#' @export
acli_handle_acli_version <- function(format = "json") {
  if (identical(format, "json")) {
    cat('{"acli_version":"0.1.0"}\n', file = stdout())
  } else {
    cat("acli 0.1.0\n", file = stdout())
  }
  invisible(NULL)
}
