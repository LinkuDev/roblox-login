import pytest

from app.core.errors import AppError
from app.core.registry import Registry


def test_register_and_get():
    reg = Registry("thing")

    @reg.register("a")
    class A:
        pass

    assert reg.get("A") is A
    assert "a" in reg


def test_get_unknown_raises():
    reg = Registry("thing")
    with pytest.raises(AppError):
        reg.get("nope")


def test_duplicate_register_raises():
    reg = Registry("thing")

    @reg.register("x")
    class X:
        pass

    with pytest.raises(AppError):
        @reg.register("x")
        class Y:
            pass
