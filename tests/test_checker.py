import pytest
import sympy as sp

from drill.checker import C, N, X, AnswerParseError, equivalent, parse_answer


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
        # 不定積分・定積分・極限・接線で使う形
        ("(x^2)/(2)+C", X**2 / 2 + C),
        ("2pi", 2 * sp.pi),
        ("(sqrt(3))/(2)", sp.sqrt(3) / 2),
        ("4ln 2", 4 * sp.log(2)),
        ("e-1", sp.E - 1),
        ("y = 2x + 1", 2 * X + 1),
        ("F(x)=x^2", X**2),
        # 数列は n の式
        ("n(n+1)/2", N * (N + 1) / 2),
        ("3*2^(n-1)", 3 * 2 ** (N - 1)),
        ("a_n = 2n^2 + 3n", 2 * N**2 + 3 * N),
    ],
)
def test_parse_answer(text, expected):
    assert sp.simplify(parse_answer(text) - expected) == 0


@pytest.mark.parametrize("text, expected", [("oo", sp.oo), ("-oo", -sp.oo), ("∞", sp.oo), ("inf", sp.oo)])
def test_parse_infinity(text, expected):
    assert parse_answer(text) == expected


@pytest.mark.parametrize("text", ["", "   ", "(x+1", "y+1", "open(1)", "__import__", "x; 1", "'a'", "y ="])
def test_parse_answer_rejects(text):
    with pytest.raises(AnswerParseError):
        parse_answer(text)


def test_equivalent_different_forms():
    assert equivalent(sp.sin(2 * X), 2 * sp.sin(X) * sp.cos(X))
    assert equivalent(sp.log(X**2), 2 * sp.log(X))
    assert equivalent((X**2 - 1) / (X - 1), X + 1)
    assert equivalent(sp.log(16), 4 * sp.log(2))
    assert equivalent(sp.Float(1.5), sp.Rational(3, 2))


def test_equivalent_in_n():
    assert equivalent(5 * 2 ** (N - 1) - 3, sp.Rational(5, 2) * 2**N - 3)
    assert equivalent(N * (N + 1) * (2 * N + 1) / 6, N**3 / 3 + N**2 / 2 + N / 6)
    assert not equivalent(3 * 2 ** (N - 1), 3 * 2**N)


def test_not_equivalent():
    assert not equivalent(X**2, X**2 + 1e-3)
    assert not equivalent(sp.sin(X), sp.cos(X))


def test_equivalent_infinity():
    assert equivalent(sp.oo, sp.oo)
    assert not equivalent(sp.oo, -sp.oo)
    assert not equivalent(sp.oo, sp.Integer(10**9))
