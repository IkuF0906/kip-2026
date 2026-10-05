"""単元「微分」：問題の型と誤答パターン。"""

import sympy as sp

from ..checker import X
from ..core import BASIC_FUNCS, Built, Misconception, ProblemType, T, Unit, apply_func, nonzero, to_latex

UNIT = Unit(
    id="derivative",
    name="微分",
    prompt="次の関数を微分しなさい。",
    answer_prefix="f'(x) =",
    solve=lambda f: sp.diff(f, X),
)

MISCONCEPTIONS = [
    Misconception(
        "power_no_coeff",
        "指数を係数として前に出し忘れ",
        r"$(x^n)' = n x^{n-1}$ です。指数 $n$ を係数として前に出すのを忘れています。",
    ),
    Misconception(
        "power_no_decrement",
        "指数を1減らし忘れ",
        r"$(x^n)' = n x^{n-1}$ です。指数を前に出したあと、指数を 1 減らす必要があります。",
    ),
    Misconception(
        "const_kept",
        "定数項を微分せずに残した",
        r"定数の微分は 0 です。定数項は微分すると消えます。",
    ),
    Misconception(
        "exponent_up",
        "指数を1増やした",
        r"微分では指数を 1 減らします（$n x^{n-1}$）。1 増やすのは積分です。"
        r"指数が負や分数のときに特に間違えやすいので注意しましょう。",
    ),
    Misconception(
        "reciprocal_naive",
        "分母だけを微分した",
        r"$\left(\frac{1}{x^n}\right)' \neq \frac{1}{(x^n)'}$ です。"
        r"$\frac{1}{x^n} = x^{-n}$ と書き直してから $(x^{-n})' = -n x^{-n-1}$ を使いましょう。",
    ),
    Misconception(
        "product_naive",
        "それぞれ微分して掛けた",
        r"積の微分は $(uv)' = u'v + uv'$ です。$(uv)' = u'v'$ ではありません。",
    ),
    Misconception(
        "product_missing_term",
        "積の微分の片方の項が抜けている",
        r"$(uv)' = u'v + uv'$ の2つの項のうち、1つしか書かれていません。",
    ),
    Misconception(
        "product_minus",
        "積の微分を引き算にした",
        r"$(uv)' = u'v + uv'$ は足し算です。引き算になるのは商の微分の分子です。",
    ),
    Misconception(
        "quotient_order",
        "商の微分の分子の順序が逆",
        r"$\left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^2}$ です。"
        r"分子は「分子の微分×分母」が先で、順序が逆だと符号が全体で反転します。",
    ),
    Misconception(
        "quotient_no_square",
        "商の微分で分母の2乗を忘れた",
        r"$\left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^2}$ です。分母は $v$ ではなく $v^2$ です。",
    ),
    Misconception(
        "quotient_naive",
        "分子と分母を別々に微分した",
        r"$\left(\frac{u}{v}\right)' \neq \frac{u'}{v'}$ です。"
        r"商の微分の公式 $\frac{u'v - uv'}{v^2}$ を使いましょう。",
    ),
    Misconception(
        "chain_no_inner",
        "内側の関数の微分を掛け忘れ",
        r"合成関数の微分は $\{g(h(x))\}' = g'(h(x)) \cdot h'(x)$ です。"
        r"外側を微分したあと、内側 $h(x)$ の微分を掛ける必要があります。",
    ),
    Misconception(
        "sqrt_no_half",
        r"$\sqrt{x}$ の微分で $\frac{1}{2}$ を忘れた",
        r"$\sqrt{x} = x^{\frac{1}{2}}$ なので $(\sqrt{x})' = \frac{1}{2} x^{-\frac{1}{2}} = \frac{1}{2\sqrt{x}}$ です。",
    ),
    Misconception(
        "cos_sign",
        "cos の微分の符号ミス",
        r"$(\cos x)' = -\sin x$ です。マイナスが付きます。",
    ),
    Misconception(
        "trig_sign_swapped",
        "sin と cos の微分の符号を逆に覚えている",
        r"$(\sin x)' = \cos x$、$(\cos x)' = -\sin x$ です。マイナスが付くのは cos の方です。",
    ),
    Misconception(
        "exp_base_no_ln",
        r"$a^x$ の微分で $\ln a$ を掛け忘れ",
        r"$(a^x)' = a^x \ln a$ です。微分しても形が変わらないのは、底が $e$ のときだけです。",
    ),
    Misconception(
        "exp_power_rule",
        "指数関数にべき関数の公式を使った",
        r"$n x^{n-1}$ の公式は、指数が定数のときだけ使えます。"
        r"指数に $x$ を含む関数は $(e^x)' = e^x$、$(a^x)' = a^x \ln a$ を使いましょう。",
    ),
]


def _build_power(rng):
    n = rng.randint(3, 6)
    m = rng.randint(2, n - 1)
    a, b, c = nonzero(rng, -5, 5), nonzero(rng, -6, 6), nonzero(rng, -9, 9)
    f = a * X**n + b * X**m + c
    ans = sp.diff(f, X)
    wrongs = [
        ("power_no_coeff", a * X ** (n - 1) + b * X ** (m - 1)),
        ("power_no_decrement", a * n * X**n + b * m * X**m),
        ("const_kept", ans + c),
    ]
    steps = [
        r"各項に $(x^n)' = n x^{n-1}$ を使い、定数項の微分は $0$",
        rf"$({to_latex(a * X**n)})' = {to_latex(a * n * X ** (n - 1))}$、$({to_latex(b * X**m)})' = {to_latex(b * m * X ** (m - 1))}$、$({c})' = 0$",
    ]
    return Built(f, wrongs, steps)


def _build_power_general(rng):
    p = rng.choice([sp.Integer(n) for n in (-3, -2, -1)] + [sp.Rational(n, d) for n, d in ((1, 2), (3, 2), (-1, 2), (1, 3))])
    a = nonzero(rng, -6, 6)
    f = a * X**p
    wrongs = [
        ("exponent_up", a * p * X ** (p + 1)),
        ("power_no_coeff", a * X ** (p - 1)),
    ]
    if p < 0 and p.is_integer:
        k = -p
        wrongs.append(("reciprocal_naive", a / (k * X ** (k - 1))))
    steps = [
        rf"$f(x) = {to_latex(a)} x^{{{to_latex(p)}}}$ と指数の形に書き直す",
        rf"$(x^n)' = n x^{{n-1}}$ より $f'(x) = {to_latex(a)} \cdot {to_latex(p)} \cdot x^{{{to_latex(p - 1)}}}$",
    ]
    return Built(f, wrongs, steps)


def _random_poly_factor(rng):
    if rng.random() < 0.5:
        return X ** rng.randint(1, 4)
    return nonzero(rng, -4, 4) * X + nonzero(rng, -5, 5)


def _build_product(rng):
    u = _random_poly_factor(rng)
    v, dv = apply_func(rng.choice(list(BASIC_FUNCS)), X)
    du = sp.diff(u, X)
    f = u * v
    wrongs = [
        ("product_naive", du * dv),
        ("product_missing_term", du * v),
        ("product_missing_term", u * dv),
        ("product_minus", du * v - u * dv),
    ]
    steps = [
        rf"$u = {to_latex(u)}$、$v = {to_latex(v)}$ とおく",
        rf"$u' = {to_latex(du)}$、$v' = {to_latex(dv)}$",
        rf"$(uv)' = u'v + uv' = {to_latex(du * v)} + {to_latex(u * dv)}$",
    ]
    return Built(f, wrongs, steps)


def _build_quotient(rng):
    u = rng.choice([nonzero(rng, -4, 4) * X + nonzero(rng, -5, 5), X**2, sp.sin(X)])
    v = rng.choice([X**2 + rng.randint(1, 5), sp.exp(X), X + rng.randint(1, 5)])
    du, dv = sp.diff(u, X), sp.diff(v, X)
    f = u / v
    wrongs = [
        ("quotient_order", (u * dv - du * v) / v**2),
        ("quotient_no_square", (du * v - u * dv) / v),
        ("quotient_naive", du / dv),
    ]
    steps = [
        rf"$u = {to_latex(u)}$、$v = {to_latex(v)}$ とおく",
        rf"$u' = {to_latex(du)}$、$v' = {to_latex(dv)}$",
        rf"$\left(\frac{{u}}{{v}}\right)' = \frac{{u'v - uv'}}{{v^2}} = \frac{{{to_latex(du * v)} - ({to_latex(u * dv)})}}{{{to_latex(v**2)}}}$",
    ]
    # sympy は u/e^x を u e^{-x} に変形してしまうため、表示用に分数の形を渡す
    return Built(f, wrongs, steps, latex=rf"f(x) = \frac{{{to_latex(u)}}}{{{to_latex(v)}}}")


def _build_chain(rng):
    outer = rng.choice(["pow", "sin", "cos", "exp", "log", "sqrt"])
    k = rng.randint(1, 3)
    if outer in ("log", "sqrt"):
        # 定義域が正になるよう係数も正にする
        a = rng.randint(1, 5)
    else:
        a = nonzero(rng, -4, 4)
    if k == 1 and a == 1:
        # 内側が x + b だと内側の微分が 1 になり、「内側の微分を掛け忘れ」が診断できない
        a = 2
    b = rng.randint(1, 5) if outer in ("log", "sqrt") else nonzero(rng, -5, 5)
    inner = a * X**k + b
    d_inner = sp.diff(inner, X)

    if outer == "pow":
        n = rng.randint(2, 5)
        g, dg = T**n, n * T ** (n - 1)
    elif outer == "sqrt":
        g, dg = sp.sqrt(T), 1 / (2 * sp.sqrt(T))
    else:
        g, dg = BASIC_FUNCS[outer]
    f = g.subs(T, inner)
    outer_d = dg.subs(T, inner)
    wrongs = [("chain_no_inner", outer_d)]
    if outer == "pow":
        wrongs.append(("power_no_decrement", n * inner**n * d_inner))
    if outer == "sqrt":
        wrongs.append(("sqrt_no_half", d_inner / sp.sqrt(inner)))
    if outer == "sin":
        wrongs.append(("trig_sign_swapped", -sp.cos(inner) * d_inner))
    if outer == "cos":
        wrongs.append(("cos_sign", sp.sin(inner) * d_inner))
    if outer == "exp":
        wrongs.append(("exp_power_rule", inner * sp.exp(inner - 1) * d_inner))
    steps = [
        rf"外側 $g(t) = {to_latex(g)}$、内側 $t = h(x) = {to_latex(inner)}$ とおく",
        rf"$g'(t) = {to_latex(dg)}$、$h'(x) = {to_latex(d_inner)}$",
        rf"$f'(x) = g'(h(x)) \cdot h'(x) = {to_latex(outer_d)} \cdot ({to_latex(d_inner)})$",
    ]
    return Built(f, wrongs, steps)


def _build_trig(rng):
    a, b = nonzero(rng, -5, 5), nonzero(rng, -5, 5)
    k, m = rng.randint(1, 4), rng.randint(1, 4)
    f = a * sp.sin(k * X) + b * sp.cos(m * X)
    ans = sp.diff(f, X)
    wrongs = [
        ("cos_sign", a * k * sp.cos(k * X) + b * m * sp.sin(m * X)),
        ("trig_sign_swapped", -ans),
        ("chain_no_inner", a * sp.cos(k * X) - b * sp.sin(m * X)),
    ]
    steps = [
        r"$(\sin x)' = \cos x$、$(\cos x)' = -\sin x$。中身が $kx$ のときは $k$ を掛ける（合成関数の微分）",
        rf"$({to_latex(a * sp.sin(k * X))})' = {to_latex(a * k * sp.cos(k * X))}$、$({to_latex(b * sp.cos(m * X))})' = {to_latex(-b * m * sp.sin(m * X))}$",
    ]
    return Built(f, wrongs, steps)


def _build_explog(rng):
    variant = rng.choice(["base", "exp", "log"])
    if variant == "base":
        a, c = nonzero(rng, -4, 4), rng.randint(2, 5)
        f = a * sp.Integer(c) ** X
        wrongs = [
            ("exp_base_no_ln", f),
            ("exp_power_rule", a * X * sp.Integer(c) ** (X - 1)),
        ]
        steps = [rf"$(a^x)' = a^x \ln a$ より $f'(x) = {to_latex(a)} \cdot {c}^x \ln {c}$"]
    elif variant == "exp":
        a, k = nonzero(rng, -4, 4), rng.choice([-3, -2, 2, 3, 4, 5])
        f = a * sp.exp(k * X)
        wrongs = [
            ("chain_no_inner", f),
            ("exp_power_rule", a * k * X * sp.exp(k * X - 1)),
        ]
        steps = [rf"$(e^{{kx}})' = k e^{{kx}}$（合成関数の微分）より $f'(x) = {to_latex(a)} \cdot {k} \cdot e^{{{to_latex(k * X)}}}$"]
    else:
        inner = rng.randint(2, 5) * X ** rng.randint(1, 3) + rng.randint(0, 5)
        d_inner = sp.diff(inner, X)
        f = sp.log(inner)
        wrongs = [("chain_no_inner", 1 / inner)]
        steps = [
            rf"$(\ln t)' = \frac{{1}}{{t}}$ と合成関数の微分を使う（$t = {to_latex(inner)}$）",
            rf"$f'(x) = \frac{{1}}{{{to_latex(inner)}}} \cdot {to_latex(d_inner)}$",
        ]
    return Built(f, wrongs, steps)


def _build_mixed(rng):
    u = X ** rng.randint(1, 3) if rng.random() < 0.6 else nonzero(rng, -4, 4) * X
    name = rng.choice(["sin", "cos", "exp"])
    k = rng.randint(2, 4)
    v, dv_outer = apply_func(name, k * X)
    dv = dv_outer * k
    du = sp.diff(u, X)
    f = u * v
    wrongs = [
        ("chain_no_inner", du * v + u * dv_outer),
        ("product_naive", du * dv),
        ("product_missing_term", du * v),
        ("product_missing_term", u * dv),
    ]
    steps = [
        rf"$u = {to_latex(u)}$、$v = {to_latex(v)}$ とおく（積の微分）",
        rf"$u' = {to_latex(du)}$、$v'$ は合成関数の微分で $v' = {to_latex(dv_outer)} \cdot {k}$",
        rf"$(uv)' = u'v + uv' = {to_latex(du * v)} + {to_latex(u * dv)}$",
    ]
    return Built(f, wrongs, steps)


TYPES = [
    ProblemType("power", "derivative", "多項式", r"$x^n$ の和の微分", _build_power),
    ProblemType("power_general", "derivative", "負・分数の指数", r"$\frac{1}{x^n}$ や $\sqrt{x}$ の微分", _build_power_general),
    ProblemType("product", "derivative", "積の微分", r"$(uv)' = u'v + uv'$", _build_product),
    ProblemType("quotient", "derivative", "商の微分", r"$\left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^2}$", _build_quotient),
    ProblemType("chain", "derivative", "合成関数の微分", r"$\{g(h(x))\}' = g'(h(x))\,h'(x)$", _build_chain),
    ProblemType("trig", "derivative", "三角関数", r"$\sin kx$、$\cos kx$ の微分", _build_trig),
    ProblemType("explog", "derivative", "指数・対数関数", r"$a^x$、$e^{kx}$、$\ln$ の微分", _build_explog),
    ProblemType("mixed", "derivative", "積＋合成関数", r"$x^n \sin kx$ などの組み合わせ", _build_mixed),
]
