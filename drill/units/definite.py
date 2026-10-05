"""単元「定積分」：問題の型と誤答パターン。答えは数（定数）。"""

import sympy as sp

from ..checker import X
from ..core import Built, Misconception, ProblemType, Unit, nonzero, to_latex

UNIT = Unit(
    id="definite",
    name="定積分",
    prompt="次の定積分を計算しなさい。",
    answer_prefix="=",
)

MISCONCEPTIONS = [
    Misconception(
        "dint_reversed",
        "上端と下端の引き算が逆",
        r"$\int_a^b f(x)\,dx = F(b) - F(a)$ です。上端 $b$ での値から、下端 $a$ での値を引きます。",
    ),
    Misconception(
        "dint_upper_only",
        "下端の値を引き忘れた",
        r"$\int_a^b f(x)\,dx = F(b) - F(a)$ です。下端での値 $F(a)$ も引く必要があります（$F(a) = 0$ とは限りません）。",
    ),
    Misconception(
        "dint_integrand_values",
        "原始関数を求めずに代入した",
        r"代入するのは元の関数 $f$ ではなく、原始関数 $F$ です。$\int_a^b f(x)\,dx = F(b) - F(a)$",
    ),
]


def _between(F: sp.Expr, lo, hi) -> sp.Expr:
    return sp.simplify(F.subs(X, hi) - F.subs(X, lo))


def _definite_latex(f: sp.Expr, lo, hi) -> str:
    body = to_latex(f)
    if isinstance(f, sp.Add) or body.startswith("-"):
        body = rf"\left({body}\right)"
    return rf"\int_{{{to_latex(lo)}}}^{{{to_latex(hi)}}} {body} \, dx"


def _common(f: sp.Expr, F: sp.Expr, lo, hi, extra_wrongs: list) -> Built:
    """原始関数 F と区間から、正解・共通の誤答・手順をまとめる。extra_wrongs は先に照合する。"""
    wrongs = extra_wrongs + [
        ("dint_reversed", _between(F, hi, lo)),
        ("dint_upper_only", sp.simplify(F.subs(X, hi))),
        ("dint_integrand_values", _between(f, lo, hi)),
    ]
    steps = [
        rf"原始関数は $F(x) = {to_latex(F)}$",
        rf"$F({to_latex(hi)}) - F({to_latex(lo)}) = {to_latex(sp.simplify(F.subs(X, hi)))} - \left({to_latex(sp.simplify(F.subs(X, lo)))}\right)$",
    ]
    return Built(
        f,
        wrongs,
        steps,
        latex=_definite_latex(f, lo, hi),
        answer=_between(F, lo, hi),
        meta={"lo": lo, "hi": hi},
    )


def _build_poly(rng):
    lo = rng.randint(-2, 2)
    hi = rng.randint(lo + 1, 3)
    a, b, c = nonzero(rng, -3, 3), nonzero(rng, -4, 4), rng.randint(-4, 4)
    n = rng.randint(2, 3)
    f = a * X**n + b * X + c
    F = sp.integrate(f, X)
    # 指数を増やしたが割り忘れた原始関数
    no_divide = a * X ** (n + 1) + b * X**2 + c * X
    return _common(f, F, lo, hi, [("int_no_divide", _between(no_divide, lo, hi))])


_TRIG_RANGES = [
    (0, sp.pi / 2),
    (0, sp.pi),
    (sp.pi / 2, sp.pi),
    (0, sp.pi / 3),
    (0, sp.pi / 6),
    (sp.pi / 6, sp.pi / 2),
    (sp.pi / 3, sp.pi),
]


def _build_trig(rng):
    lo, hi = rng.choice(_TRIG_RANGES)
    a = nonzero(rng, -4, 4)
    f = a * (sp.sin(X) if rng.random() < 0.5 else sp.cos(X))
    F = sp.integrate(f, X)
    # sin・cos の積分の符号を間違えると答え全体の符号が逆になり、「上端と下端が逆」と同じ値になる。
    # 三角関数の問題では符号の取り違えの方が多いので、こちらを先に照合する
    return _common(f, F, lo, hi, [("int_trig_sign", -_between(F, lo, hi))])


def _build_explog(rng):
    a = nonzero(rng, -4, 4)
    if rng.random() < 0.5:
        k = rng.choice([1, 2, 3])
        lo, hi = 0, 1
        f = a * sp.exp(k * X)
        F = sp.integrate(f, X)
        extra = [("int_chain_no_divide", _between(f, lo, hi))] if k != 1 else []
    else:
        lo, hi = rng.choice([(1, sp.E), (1, sp.E**2), (1, 2), (1, 3), (2, 4)])
        f = a / X
        F = a * sp.log(X)
        extra = [("int_differentiated", _between(sp.diff(f, X), lo, hi))]
    return _common(f, F, lo, hi, extra)


TYPES = [
    ProblemType("dint_poly", "definite", "多項式", r"$\int_a^b (ax^2 + bx + c)\,dx$", _build_poly),
    ProblemType("dint_trig", "definite", "三角関数", r"$\int_0^{\pi} \sin x\,dx$ など", _build_trig),
    ProblemType("dint_explog", "definite", "指数・対数関数", r"$\int_0^1 e^{kx}\,dx$、$\int_1^e \frac{1}{x}\,dx$ など", _build_explog),
]
