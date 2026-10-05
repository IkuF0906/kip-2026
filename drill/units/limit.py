"""単元「極限」：問題の型と誤答パターン。答えは数、または ±∞。"""

import sympy as sp

from ..checker import X
from ..core import Built, Misconception, ProblemType, Unit, nonzero, to_latex

UNIT = Unit(
    id="limit",
    name="極限",
    prompt=r"次の極限を求めなさい（$\infty$ は oo と入力できます）。",
    answer_prefix="=",
)

MISCONCEPTIONS = [
    Misconception(
        "lim_leading_ratio",
        "次数が違うのに最高次の係数の比を答えた",
        r"$x \to \infty$ の分数式は、分子と分母の次数を比べます。係数の比になるのは次数が同じときだけで、"
        r"分母の次数が大きければ $0$、分子の次数が大きければ $\pm\infty$ です。",
    ),
    Misconception(
        "lim_constant_ratio",
        "定数項の比を答えた",
        r"$x \to \infty$ では、最も次数の高い項が全体の大きさを決めます。分子・分母を $x$ の最高次で割って考えましょう。",
    ),
    Misconception(
        "lim_inf_over_inf_one",
        r"$\frac{\infty}{\infty}$ を 1 とした",
        r"$\frac{\infty}{\infty}$ は不定形で、1 とは限りません。分子・分母を $x$ の最高次で割って調べます。",
    ),
    Misconception(
        "lim_zero_over_zero",
        r"$\frac{0}{0}$ を 0 とした",
        r"代入して $\frac{0}{0}$ になるのは不定形です。約分や公式で形を変えてから極限を求めます。",
    ),
    Misconception(
        "lim_zero_over_zero_one",
        r"$\frac{0}{0}$ を 1 とした",
        r"$\frac{0}{0}$ は不定形で、1 とは限りません。分子・分母を因数分解して、共通の因数を約分します。",
    ),
    Misconception(
        "lim_factor_sign",
        "因数分解の符号を間違えた",
        r"$x^2 - (a+b)x + ab = (x-a)(x-b)$ です。約分したあとの式に代入するときも符号に注意しましょう。",
    ),
    Misconception(
        "lim_sin_one",
        "sin の中の係数を無視して 1 とした",
        r"$\lim_{x \to 0} \frac{\sin x}{x} = 1$ は、sin の中と分母が同じときに使えます。"
        r"$\frac{\sin kx}{mx} = \frac{\sin kx}{kx} \cdot \frac{k}{m}$ と変形しましょう。",
    ),
    Misconception(
        "lim_sin_inverted",
        "係数の比が逆",
        r"$\frac{\sin kx}{mx} = \frac{\sin kx}{kx} \cdot \frac{k}{m} \to \frac{k}{m}$ です。",
    ),
    Misconception(
        "lim_one_power",
        r"$1^\infty$ を 1 とした",
        r"$1^\infty$ は不定形です。$\lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x = e$ を使います。",
    ),
    Misconception(
        "lim_e_no_k",
        "e の指数を付け忘れた",
        r"$\left(1 + \frac{k}{x}\right)^x = \left\{\left(1 + \frac{k}{x}\right)^{\frac{x}{k}}\right\}^k \to e^k$ です。",
    ),
    Misconception(
        "lim_inf_minus_inf",
        r"$\infty - \infty$ を 0 とした",
        r"$\infty - \infty$ は不定形です。$\sqrt{A} - B$ の形は、分子・分母に $\sqrt{A} + B$ を掛けて有理化します。",
    ),
    Misconception(
        "lim_rationalize_no_half",
        "有理化した後の分母の扱いを間違えた",
        r"有理化すると $\frac{px}{\sqrt{x^2 + px} + x}$ になり、分母は $x \to \infty$ でおよそ $2x$ です。答えは $\frac{p}{2}$ になります。",
    ),
]


def _lim_latex(expr_latex: str, to) -> str:
    # \limits で x → a を lim の真下に置く（文中の数式でも教科書と同じ見た目にする）
    return rf"\lim\limits_{{x \to {to_latex(to)}}} {expr_latex}"


def _frac(num: sp.Expr, den: sp.Expr) -> str:
    return rf"\frac{{{to_latex(num)}}}{{{to_latex(den)}}}"


def _build_rational(rng):
    case = rng.choice(["same", "lower", "higher"])
    if case == "same":
        n = m = rng.randint(1, 3)
    elif case == "lower":
        n = rng.randint(1, 2)
        m = rng.randint(n + 1, 3)
    else:
        m = rng.randint(1, 2)
        n = rng.randint(m + 1, 3)
    a, d = nonzero(rng, -6, 6), rng.randint(1, 6)
    b, e = nonzero(rng, -9, 9), nonzero(rng, -9, 9)
    num, den = a * X**n + b, d * X**m + e
    if n == m:
        answer = sp.Rational(a, d)
    elif n < m:
        answer = sp.Integer(0)
    else:
        answer = sp.oo if a > 0 else -sp.oo
    wrongs = [
        ("lim_leading_ratio", sp.Rational(a, d)),
        ("lim_constant_ratio", sp.Rational(b, e)),
        ("lim_inf_over_inf_one", sp.Integer(1)),
    ]
    steps = [
        rf"分子の次数は ${n}$、分母の次数は ${m}$",
        rf"分子・分母を $x^{{{max(n, m)}}}$ で割り、$x \to \infty$ で $\frac{{1}}{{x}} \to 0$ を使う",
    ]
    return Built(num / den, wrongs, steps, latex=_lim_latex(_frac(num, den), sp.oo), answer=answer, meta={"to": sp.oo})


def _build_factor(rng):
    a = rng.randint(1, 4)
    r, s = rng.sample([v for v in range(-4, 5) if v != a], 2)
    num = sp.expand((X - a) * (X - r))
    den = sp.expand((X - a) * (X - s))
    answer = sp.Rational(a - r, a - s)
    wrongs = [
        ("lim_zero_over_zero", sp.Integer(0)),
        ("lim_zero_over_zero_one", sp.Integer(1)),
        ("lim_factor_sign", sp.Rational(a + r, a + s) if a + s != 0 else sp.nan),
    ]
    wrongs = [(mid, w) for mid, w in wrongs if w is not sp.nan]
    steps = [
        rf"$x = {a}$ を代入すると $\frac{{0}}{{0}}$ になるので因数分解する",
        rf"$\frac{{(x - {a})({to_latex(X - r)})}}{{(x - {a})({to_latex(X - s)})}} = \frac{{{to_latex(X - r)}}}{{{to_latex(X - s)}}}$ に $x = {a}$ を代入",
    ]
    return Built(num / den, wrongs, steps, latex=_lim_latex(_frac(num, den), a), answer=answer, meta={"to": a})


def _build_sin(rng):
    k, m = rng.sample(range(1, 7), 2)
    func = rng.choice([sp.sin, sp.tan])
    num, den = func(k * X), m * X
    answer = sp.Rational(k, m)
    wrongs = [
        ("lim_sin_one", sp.Integer(1)),
        ("lim_sin_inverted", sp.Rational(m, k)),
        ("lim_zero_over_zero", sp.Integer(0)),
    ]
    name = to_latex(func(X)).split("{")[0]
    steps = [
        rf"$\lim_{{x \to 0}} \frac{{{name} x}}{{x}} = 1$ を使えるように変形する",
        rf"$\frac{{{to_latex(num)}}}{{{to_latex(den)}}} = \frac{{{to_latex(num)}}}{{{to_latex(k * X)}}} \cdot \frac{{{k}}}{{{m}}}$",
    ]
    return Built(num / den, wrongs, steps, latex=_lim_latex(_frac(num, den), 0), answer=answer, meta={"to": 0})


def _build_e(rng):
    k, m = rng.randint(2, 4), rng.randint(1, 3)
    base = 1 + sp.Integer(k) / X
    expr = base ** (m * X)
    answer = sp.exp(k * m)
    wrongs = [
        ("lim_one_power", sp.Integer(1)),
        ("lim_e_no_k", sp.exp(m)),
    ]
    shown = rf"\left(1 + \frac{{{k}}}{{x}}\right)^{{{to_latex(m * X)}}}"
    steps = [
        rf"$\lim_{{x \to \infty}} \left(1 + \frac{{1}}{{t}}\right)^t = e$ を使う（$t = \frac{{x}}{{{k}}}$）",
        rf"${shown} = \left\{{\left(1 + \frac{{{k}}}{{x}}\right)^{{\frac{{x}}{{{k}}}}}\right\}}^{{{k * m}}} \to e^{{{k * m}}}$",
    ]
    return Built(expr, wrongs, steps, latex=_lim_latex(shown, sp.oo), answer=answer, meta={"to": sp.oo})


def _build_sqrt(rng):
    p = nonzero(rng, -8, 8)
    expr = sp.sqrt(X**2 + p * X) - X
    answer = sp.Rational(p, 2)
    wrongs = [
        ("lim_inf_minus_inf", sp.Integer(0)),
        ("lim_rationalize_no_half", sp.Integer(p)),
    ]
    steps = [
        rf"分子・分母に $\sqrt{{{to_latex(X**2 + p * X)}}} + x$ を掛けて有理化する",
        rf"$\frac{{{to_latex(p * X)}}}{{\sqrt{{{to_latex(X**2 + p * X)}}} + x}}$ の分子・分母を $x$ で割ると $\frac{{{p}}}{{\sqrt{{1 + \frac{{{p}}}{{x}}}} + 1}} \to \frac{{{p}}}{{2}}$",
    ]
    # sympy は -x + √… の順に並べるので、√… - x の順で表示する
    shown = rf"\left(\sqrt{{{to_latex(X**2 + p * X)}}} - x\right)"
    return Built(expr, wrongs, steps, latex=_lim_latex(shown, sp.oo), answer=answer, meta={"to": sp.oo})


TYPES = [
    # 型の名前は選択肢にそのまま出すので LaTeX を使わない
    ProblemType("lim_rational", "limit", "分数式（x → ∞）", r"次数を比べる", _build_rational),
    ProblemType("lim_factor", "limit", "0/0 の約分", r"因数分解して約分する", _build_factor),
    ProblemType("lim_sin", "limit", "sin x / x の極限", r"$\lim_{x \to 0} \frac{\sin x}{x} = 1$", _build_sin),
    ProblemType("lim_e", "limit", "e の定義", r"$\lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x = e$", _build_e),
    ProblemType("lim_sqrt", "limit", "∞ − ∞ の有理化", r"$\sqrt{x^2 + px} - x$", _build_sqrt),
]
