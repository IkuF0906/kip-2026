import pytest
import sympy as sp

from drill.checker import X, AnswerParseError, equivalent, parse_answer


@pytest.mark.parametrize(
    "text, expected",
    [
        ("3x^2+2sin(x)", 3 * X**2 + 2 * sp.sin(X)),
        ("xsinx", X * sp.sin(X)),
        ("2 x cos x", 2 * X * sp.cos(X)),
        ("e^(2x)", sp.exp(2 * X)),
        ("xe^x", X * sp.exp(X)),
        ("(1)/(x)", 1 / X),
        ("sqrt(x)", sp.sqrt(X)),
        ("2^x ln 2", 2**X * sp.log(2)),
        ("3**x", 3**X),
        ("2·x − 1", 2 * X - 1),
    ],
)
def test_parse_answer(text, expected):
    assert sp.simplify(parse_answer(text) - expected) == 0


@pytest.mark.parametrize("text", ["", "   ", "(x+1", "y+1", "open(1)", "__import__", "x; 1", "'a'"])
def test_parse_answer_rejects(text):
    with pytest.raises(AnswerParseError):
        parse_answer(text)


def test_equivalent_different_forms():
    assert equivalent(sp.sin(2 * X), 2 * sp.sin(X) * sp.cos(X))
    assert equivalent(sp.log(X**2), 2 * sp.log(X))
    assert equivalent((X**2 - 1) / (X - 1), X + 1)


def test_not_equivalent():
    assert not equivalent(X**2, X**2 + 1e-3)
    assert not equivalent(sp.sin(X), sp.cos(X))
