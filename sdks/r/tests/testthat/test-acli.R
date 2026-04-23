test_that("success envelope has ok", {
  e <- acli_success_envelope("run", list(x = 1), "1.0.0", NULL)
  expect_true(e$ok)
  expect_equal(e$command, "run")
})

test_that("suggest flag", {
  expect_equal(acli_suggest_flag("pipline", c("pipeline", "env")), "pipeline")
})

test_that("cli folder generates", {
  d <- tempfile("acli-r-")
  dir.create(d)
  on.exit(unlink(d, recursive = TRUE), add = TRUE)
  tree <- list(
    name = "t", version = "1.0.0", acli_version = "0.1.0",
    commands = list(
      list(name = "greet", description = "hi", examples = list(list(description = "a", invocation = "t greet")))
    )
  )
  root <- acli_cli_folder_generate(tree, d)
  expect_true(file.exists(file.path(root, "commands.json")))
})

test_that("handle error returns code", {
  app <- acli_new_app("x", "1.0.0", cli_dir = tempdir())
  code <- acli_handle_error(app, list(code = 3L, message = "gone", command = "run"))
  expect_equal(code, 3L)
})

sample_skill_tree <- function() {
  list(
    name = "noether", version = "1.0.0", acli_version = "0.1.0",
    commands = list(
      list(name = "run", description = "Run a pipeline", idempotent = FALSE),
      list(name = "introspect", description = "Introspect"),
      list(name = "version", description = "Version"),
      list(name = "skill", description = "Skill")
    )
  )
}

test_that("skill emits default frontmatter", {
  content <- acli_skill_generate(sample_skill_tree())
  expect_true(startsWith(content, "---\n"))
  lines <- strsplit(content, "\n", fixed = TRUE)[[1]]
  expect_equal(lines[2], "name: noether")
  expect_true(startsWith(lines[3], "description: "))
  expect_true(grepl("noether", lines[3], fixed = TRUE))
  # No when_to_use in the frontmatter block by default.
  closing_idx <- which(lines == "---")[2]
  expect_true(closing_idx > 0)
  fm_block <- lines[seq_len(closing_idx)]
  expect_false(any(startsWith(fm_block, "when_to_use:")))
})

test_that("skill emits explicit frontmatter", {
  content <- acli_skill_generate(
    sample_skill_tree(),
    description = "Run Noether pipelines.",
    when_to_use = "Use when deploying."
  )
  expect_true(grepl("description: Run Noether pipelines.", content, fixed = TRUE))
  expect_true(grepl("when_to_use: Use when deploying.", content, fixed = TRUE))
})

test_that("skill collapses newlines in frontmatter values", {
  content <- acli_skill_generate(
    sample_skill_tree(),
    description = "Line 1\nLine 2"
  )
  expect_true(grepl("description: Line 1 Line 2", content, fixed = TRUE))
})
