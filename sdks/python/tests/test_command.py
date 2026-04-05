"""Tests for acli.command."""

import pytest

from acli.command import ACLI_META_ATTR, CommandExample, CommandMeta, acli_command


class TestAcliCommand:
    def test_attaches_metadata(self) -> None:
        @acli_command(
            examples=[
                ("Run basic", "tool run --file a.yaml"),
                ("Run with env", "tool run --file a.yaml --env prod"),
            ],
            idempotent=True,
            see_also=["status", "logs"],
        )
        def my_func() -> None:
            pass

        meta: CommandMeta = getattr(my_func, ACLI_META_ATTR)
        assert len(meta.examples) == 2
        assert meta.examples[0].description == "Run basic"
        assert meta.examples[0].invocation == "tool run --file a.yaml"
        assert meta.idempotent is True
        assert meta.see_also == ("status", "logs")

    def test_requires_two_examples(self) -> None:
        with pytest.raises(ValueError, match="at least 2 examples"):

            @acli_command(examples=[("Only one", "tool run")])
            def bad() -> None:
                pass

    def test_invalid_idempotent_string(self) -> None:
        with pytest.raises(ValueError, match="idempotent must be"):

            @acli_command(
                examples=[("A", "x"), ("B", "y")],
                idempotent="maybe",
            )
            def bad() -> None:
                pass

    def test_conditional_idempotent(self) -> None:
        @acli_command(
            examples=[("A", "x"), ("B", "y")],
            idempotent="conditional",
        )
        def my_func() -> None:
            pass

        meta: CommandMeta = getattr(my_func, ACLI_META_ATTR)
        assert meta.idempotent == "conditional"

    def test_default_see_also_empty(self) -> None:
        @acli_command(examples=[("A", "x"), ("B", "y")])
        def my_func() -> None:
            pass

        meta: CommandMeta = getattr(my_func, ACLI_META_ATTR)
        assert meta.see_also == ()


class TestCommandExample:
    def test_frozen(self) -> None:
        ex = CommandExample("desc", "inv")
        with pytest.raises(AttributeError):
            ex.description = "new"  # type: ignore[misc]


class TestCommandMeta:
    def test_frozen(self) -> None:
        meta = CommandMeta(
            examples=(CommandExample("a", "b"),),
            idempotent=False,
            see_also=(),
        )
        with pytest.raises(AttributeError):
            meta.idempotent = True  # type: ignore[misc]
