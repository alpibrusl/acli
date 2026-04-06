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
