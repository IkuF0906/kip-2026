"""単元「不定積分」：問題の型と誤答パターン。

正解・誤答は原始関数で持ち、比べるときは両方を微分して比べる（積分定数の違いを無視するため）。
"""

import sympy as sp

from ..checker import X, equivalent
from ..core import Built, Misconception, ProblemType, Unit, apply_func, nonzero, to_latex


def same_up_to_constant(a: sp.Expr, b: sp.Expr) -> bool:
    return equivalent(sp.diff(a, X), sp.diff(b, X))


UNIT = Unit(
    id="integral",
    name="不定積分",
    prompt="次の不定積分を求めなさい。",
    answer_prefix="=",
    same=same_up_to_constant,
    solve=lambda f: sp.integrate(f, X),
    answer_suffix=" + C",
    needs_constant=True,
)

MISCONCEPTIONS = [
    Misconception(
        "int_no_divide",
        "指数を1増やしたが、その数で割り忘れた",
        r"$\int x^n\,dx = \frac{x^{n+1}}{n+1} + C$ です。指数を 1 増やしたら、増やした後の指数 $n+1$ で割ります。",
    ),
    Misconception(
        "int_divide_by_n",
        "元の指数で割った",
        r"割る数は、1 増やした後の指数 $n+1$ です。$\int x^n\,dx = \frac{x^{n+1}}{n+1} + C$",
    ),
    Misconception(
        "int_differentiated",
        "積分ではなく微分した",
        r"積分は微分の逆の操作です。求めた答えを微分して、元の関数に戻るかで確かめられます。",
    ),
    Misconception(
        "int_const_dropped",
        "定数項を積分し忘れた",
        r"定数 $c$ の積分は $cx$ です（$\int c\,dx = cx + C$）。",
    ),
    Misconception(
        "int_trig_sign",
        "sin・cos の積分の符号を逆にした",
        r"$\int \sin x\,dx = -\cos x + C$、$\int \cos x\,dx = \sin x + C$ です。"
        r"マイナスが付くのは $\sin$ の積分の方です。",
    ),
    Misconception(
        "int_chain_no_divide",
        "中身の x の係数で割り忘れた",
        r"$\int f(kx+b)\,dx = \frac{1}{k}F(kx+b) + C$ です。中身の $x$ の係数 $k$ で割る必要があります。",
    ),
    Misconception(
        "int_chain_multiply",
        "中身の x の係数で割らずに掛けた",
        r"微分では中身の微分 $k$ を掛けますが、積分では逆に $k$ で割ります。"
        r"$\int f(kx+b)\,dx = \frac{1}{k}F(kx+b) + C$",
    ),
    Misconception(
        "int_base_no_ln",
        r"$a^x$ の積分で $\ln a$ で割り忘れた",
        r"$\int a^x\,dx = \frac{a^x}{\ln a} + C$ です。形が変わらないのは底が $e$ のときだけです。",
    ),
    Misconception(
        "int_exp_power_rule",
        "指数関数にべき関数の積分の公式を使った",
        r"$\frac{x^{n+1}}{n+1}$ の公式は、指数が定数の $x^n$ のときだけ使えます。"
        r"$\int a^x\,dx = \frac{a^x}{\ln a} + C$ です。",
    ),
    Misconception(
        "int_parts_sign",
        "部分積分の符号ミス",
        r"部分積分は $\int u v'\,dx = uv - \int u'v\,dx$ です。後ろの項は引き算です。",
    ),
    Misconception(
        "int_parts_missing",
        "部分積分の後ろの項を忘れた",
        r"$\int u v'\,dx = uv - \int u'v\,dx$ のうち、$\int u'v\,dx$ の部分が抜けています。",
    ),
    Misconception(
        "int_parts_naive",
        "積の積分を、それぞれの積分の積にした",
        r"$\int uv\,dx \neq \int u\,dx \cdot \int v\,dx$ です。"
        r"積の積分には部分積分 $\int u v'\,dx = uv - \int u'v\,dx$ を使います。",
    ),
]


def integral_latex(f: sp.Expr) -> str:
    body = to_latex(f)
    if isinstance(f, sp.Add) or body.startswith("-"):
        body = rf"\left({body}\right)"
    return rf"\int {body} \, dx"


def _I(f: sp.Expr) -> sp.Expr:
    return sp.integrate(f, X)


def _build_power(rng):
    n = rng.randint(2, 5)
    m = rng.randint(1, n - 1)
    a, b, c = nonzero(rng, -6, 6), nonzero(rng, -6, 6), nonzero(rng, -9, 9)
    f = a * X**n + b * X**m + c
    wrongs = [
        ("int_no_divide", a * X ** (n + 1) + b * X ** (m + 1) + c * X),
        ("int_divide_by_n", a * X ** (n + 1) / n + b * X ** (m + 1) / m + c * X),
        ("int_const_dropped", _I(f) - c * X),
        ("int_differentiated", sp.diff(f, X)),
    ]
    steps = [
        r"各項に $\int x^n\,dx = \frac{x^{n+1}}{n+1} + C$ を使い、定数 $c$ の積分は $cx$",
        rf"$\int {to_latex(a * X**n)}\,dx = {to_latex(_I(a * X**n))}$、"
        rf"$\int {to_latex(b * X**m)}\,dx = {to_latex(_I(b * X**m))}$、$\int {c}\,dx = {to_latex(c * X)}$",
    ]
    return Built(f, wrongs, steps, latex=integral_latex(f))


def _build_power_general(rng):
    p = rng.choice([sp.Integer(-2), sp.Integer(-3)] + [sp.Rational(n, d) for n, d in ((1, 2), (-1, 2), (3, 2), (1, 3))])
    a = nonzero(rng, -6, 6)
    f = a * X**p
    wrongs = [
        ("int_no_divide", a * X ** (p + 1)),
        ("int_divide_by_n", a * X ** (p + 1) / p),
        ("int_differentiated", sp.diff(f, X)),
    ]
    steps = [
        rf"$x^{{{to_latex(p)}}}$ の形に書き直して $\int x^n\,dx = \frac{{x^{{n+1}}}}{{n+1}} + C$ を使う",
        rf"$\int {to_latex(a)} x^{{{to_latex(p)}}}\,dx = {to_latex(a)} \cdot \frac{{x^{{{to_latex(p + 1)}}}}}{{{to_latex(p + 1)}}}$",
    ]
    return Built(f, wrongs, steps, latex=integral_latex(f))


def _build_trig(rng):
    a, b = nonzero(rng, -6, 6), nonzero(rng, -6, 6)
    k, m = rng.randint(1, 4), rng.randint(1, 4)
    f = a * sp.sin(k * X) + b * sp.cos(m * X)
    ans = _I(f)
    wrongs = [
        ("int_trig_sign", -ans),
        ("int_chain_no_divide", -a * sp.cos(k * X) + b * sp.sin(m * X)),
        ("int_chain_multiply", -a * k * sp.cos(k * X) + b * m * sp.sin(m * X)),
        ("int_differentiated", sp.diff(f, X)),
    ]
    steps = [
        r"$\int \sin kx\,dx = -\frac{1}{k}\cos kx + C$、$\int \cos kx\,dx = \frac{1}{k}\sin kx + C$",
        rf"$\int {to_latex(a * sp.sin(k * X))}\,dx = {to_latex(_I(a * sp.sin(k * X)))}$、"
        rf"$\int {to_latex(b * sp.cos(m * X))}\,dx = {to_latex(_I(b * sp.cos(m * X)))}$",
    ]
    return Built(f, wrongs, steps, latex=integral_latex(f))


def _build_explog(rng):
    variant = rng.choice(["exp", "recip", "base"])
    a = nonzero(rng, -5, 5)
    if variant == "exp":
        k = rng.choice([-3, -2, 2, 3, 4])
        f = a * sp.exp(k * X)
        wrongs = [
            ("int_chain_no_divide", f),
            ("int_chain_multiply", k * f),
        ]
        steps = [rf"$\int e^{{kx}}\,dx = \frac{{1}}{{k}} e^{{kx}} + C$ を $k = {k}$ で使う"]
    elif variant == "recip":
        k, b = rng.randint(2, 5), rng.randint(1, 5)
        inner = k * X + b
        f = a / inner
        wrongs = [
            ("int_chain_no_divide", a * sp.log(inner)),
            ("int_chain_multiply", a * k * sp.log(inner)),
            ("int_differentiated", sp.diff(f, X)),
        ]
        steps = [rf"$\int \frac{{1}}{{kx+b}}\,dx = \frac{{1}}{{k}} \ln|kx+b| + C$ を $k = {k}$ で使う"]
    else:
        c = rng.randint(2, 5)
        f = a * sp.Integer(c) ** X
        wrongs = [
            ("int_base_no_ln", f),
            ("int_exp_power_rule", a * sp.Integer(c) ** (X + 1) / (X + 1)),
            ("int_differentiated", sp.diff(f, X)),
        ]
        steps = [rf"$\int a^x\,dx = \frac{{a^x}}{{\ln a}} + C$ を $a = {c}$ で使う"]
    return Built(f, wrongs, steps, latex=integral_latex(f))


def _build_linear(rng):
    k, b, n = rng.randint(2, 5), nonzero(rng, -5, 5), rng.randint(2, 5)
    inner = k * X + b
    f = inner**n
    wrongs = [
        ("int_chain_no_divide", inner ** (n + 1) / (n + 1)),
        ("int_chain_multiply", k * inner ** (n + 1) / (n + 1)),
        ("int_no_divide", inner ** (n + 1) / k),
        ("int_differentiated", sp.diff(f, X)),
    ]
    steps = [
        r"$\int (kx+b)^n\,dx = \frac{1}{k} \cdot \frac{(kx+b)^{n+1}}{n+1} + C$",
        rf"$k = {k}$、$n = {n}$ なので $\frac{{1}}{{{k}}} \cdot \frac{{({to_latex(inner)})^{{{n + 1}}}}}{{{n + 1}}}$",
    ]
    # sympy の積分は展開した形を返すので、(kx+b)^{n+1} の形の答えを直接渡す
    answer = inner ** (n + 1) / (k * (n + 1))
    return Built(f, wrongs, steps, latex=integral_latex(f), answer=answer)


def _build_parts(rng):
    if rng.random() < 0.7:
        # ∫ a x g(kx) dx（u = ax、v' = g(kx)）
        a = nonzero(rng, -4, 4)
        k = rng.randint(1, 3)
        u = a * X
        dv, _ = apply_func(rng.choice(["exp", "sin", "cos"]), k * X)
        v = _I(dv)
        du = sp.diff(u, X)
        rest = _I(du * v)
        wrongs = [
            ("int_parts_sign", u * v + rest),
            ("int_parts_missing", u * v),
            ("int_parts_naive", _I(u) * v),
        ]
    else:
        # ∫ x^m ln x dx（u = ln x、v' = x^m）
        m = rng.randint(0, 2)
        u, dv = sp.log(X), X**m
        v = _I(dv)
        du = sp.diff(u, X)
        rest = _I(du * v)
        wrongs = [
            ("int_parts_sign", u * v + rest),
            ("int_parts_missing", u * v),
        ]
    f = u * dv
    steps = [
        rf"$u = {to_latex(u)}$、$v' = {to_latex(dv)}$ とおくと $u' = {to_latex(du)}$、$v = {to_latex(v)}$",
        rf"$\int u v'\,dx = uv - \int u'v\,dx = {to_latex(u * v)} - \int {to_latex(sp.expand(du * v))}\,dx$",
    ]
    return Built(f, wrongs, steps, latex=integral_latex(f))


TYPES = [
    ProblemType("int_power", "integral", "多項式", r"$\int x^n\,dx = \frac{x^{n+1}}{n+1} + C$", _build_power),
    ProblemType("int_power_general", "integral", "負・分数の指数", r"$\int \frac{1}{x^2}\,dx$、$\int \sqrt{x}\,dx$ など", _build_power_general),
    ProblemType("int_trig", "integral", "三角関数", r"$\int \sin kx\,dx$、$\int \cos kx\,dx$", _build_trig),
    ProblemType("int_explog", "integral", "指数・対数関数", r"$\int e^{kx}\,dx$、$\int \frac{1}{kx+b}\,dx$、$\int a^x\,dx$", _build_explog),
    ProblemType("int_linear", "integral", "1次式の合成", r"$\int (kx+b)^n\,dx$", _build_linear),
    ProblemType("int_parts", "integral", "部分積分", r"$\int u v'\,dx = uv - \int u'v\,dx$", _build_parts),
]
