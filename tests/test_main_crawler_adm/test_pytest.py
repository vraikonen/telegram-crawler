import pytest


def add_numbers(a, b):
    return a + b


def test_add_numbers():
    assert add_numbers(2, 3) == 5
    assert add_numbers(10, -5) == 5
    assert add_numbers(0, 0) == 0
    assert add_numbers(-1, -1) == -2
