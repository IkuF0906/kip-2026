"""問題の型（ひな形）と誤答ルール。

各型は乱数から問題式 f(x)・正解 f'(x)・誤答の式・解き方の手順を作る。
誤答の式は「この間違いをするとこの答えになる」を表し、診断で利用者の解答と照合する。
問題IDは "<型ID>-<シード>" で、同じIDからは常に同じ問題が再生成される。
"""

import random
from dataclasses import dataclass, field
from typing import Callable

import sympy as sp

from .checker import X, equivalent


@dataclass(frozen=True)
class Misconception:
    id: str
    label: str
    explanation: str  # $...$ で囲んだ部分は LaTeX


MISCONCEPTIONS = {
    m.id: m
    for m in [
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
}


@dataclass
class Problem:
    problem_id: str
    type_id: str
    f: sp.Expr
    answer: sp.Expr
    wrongs: list[tuple[str, sp.Expr]]  # (誤答ルールID, その間違いをしたときの答え)
    latex: str  # 問題式 f(x) の表示用
    steps: list[str] = field(default_factory=list)  # 解き方の手順（$...$ は LaTeX）


@dataclass(frozen=True)
class ProblemType:
    id: str
    name: str
    description: str
    # (f, 誤答, 手順) または表示用 LaTeX を加えた4要素を返す
    build: Callable[[random.Random], tuple]


def to_latex(expr: sp.Expr) -> str:
    return sp.latex(expr, ln_notation=True)


def _nonzero(rng: random.Random, lo: int, hi: int) -> int:
    return rng.choice([n for n in range(lo, hi + 1) if n != 0])


# 合成・積で使う基本関数: (名前, g(t), g'(t))
_t = sp.Symbol("t")
_BASIC_FUNCS = {
    "sin": (sp.sin(_t), sp.cos(_t)),
    "cos": (sp.cos(_t), -sp.sin(_t)),
    "exp": (sp.exp(_t), sp.exp(_t)),
    "log": (sp.log(_t), 1 / _t),
}


def _apply(name: str, arg: sp.Expr) -> tuple[sp.Expr, sp.Expr]:
    g, dg = _BASIC_FUNCS[name]
    return g.subs(_t, arg), dg.subs(_t, arg)


def _build_power(rng):
    n = rng.randint(3, 6)
    m = rng.randint(2, n - 1)
    a, b, c = _nonzero(rng, -5, 5), _nonzero(rng, -6, 6), _nonzero(rng, -9, 9)
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
    return f, wrongs, steps


def _build_power_general(rng):
    p = rng.choice([sp.Integer(n) for n in (-3, -2, -1)] + [sp.Rational(n, d) for n, d in ((1, 2), (3, 2), (-1, 2), (1, 3))])
    a = _nonzero(rng, -6, 6)
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
    return f, wrongs, steps


def _random_poly_factor(rng):
    if rng.random() < 0.5:
        return X ** rng.randint(1, 4)
    return _nonzero(rng, -4, 4) * X + _nonzero(rng, -5, 5)


def _build_product(rng):
    u = _random_poly_factor(rng)
    v, dv = _apply(rng.choice(list(_BASIC_FUNCS)), X)
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
    return f, wrongs, steps


def _build_quotient(rng):
    u = rng.choice([_nonzero(rng, -4, 4) * X + _nonzero(rng, -5, 5), X**2, sp.sin(X)])
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
    return f, wrongs, steps, rf"\frac{{{to_latex(u)}}}{{{to_latex(v)}}}"


def _build_chain(rng):
    outer = rng.choice(["pow", "sin", "cos", "exp", "log", "sqrt"])
    k = rng.randint(1, 3)
    if outer in ("log", "sqrt"):
        # 定義域が正になるよう係数も正にする
        inner = rng.randint(1, 5) * X**k + rng.randint(1, 5)
    else:
        inner = _nonzero(rng, -4, 4) * X**k + _nonzero(rng, -5, 5)
    d_inner = sp.diff(inner, X)

    if outer == "pow":
        n = rng.randint(2, 5)
        g, dg = _t**n, n * _t ** (n - 1)
    elif outer == "sqrt":
        g, dg = sp.sqrt(_t), 1 / (2 * sp.sqrt(_t))
    else:
        g, dg = _BASIC_FUNCS[outer]
    f = g.subs(_t, inner)
    outer_d = dg.subs(_t, inner)
    wrongs = [("chain_no_inner", outer_d)]
    if outer == "cos":
        wrongs.append(("cos_sign", sp.sin(inner) * d_inner))
    if outer == "exp":
        wrongs.append(("exp_power_rule", inner * sp.exp(inner - 1) * d_inner))
    steps = [
        rf"外側 $g(t) = {to_latex(g)}$、内側 $t = h(x) = {to_latex(inner)}$ とおく",
        rf"$g'(t) = {to_latex(dg)}$、$h'(x) = {to_latex(d_inner)}$",
        rf"$f'(x) = g'(h(x)) \cdot h'(x) = {to_latex(outer_d)} \cdot ({to_latex(d_inner)})$",
    ]
    return f, wrongs, steps


def _build_trig(rng):
    a, b = _nonzero(rng, -5, 5), _nonzero(rng, -5, 5)
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
    return f, wrongs, steps


def _build_explog(rng):
    variant = rng.choice(["base", "exp", "log"])
    if variant == "base":
        a, c = _nonzero(rng, -4, 4), rng.randint(2, 5)
        f = a * sp.Integer(c) ** X
        wrongs = [
            ("exp_base_no_ln", f),
            ("exp_power_rule", a * X * sp.Integer(c) ** (X - 1)),
        ]
        steps = [rf"$(a^x)' = a^x \ln a$ より $f'(x) = {to_latex(a)} \cdot {c}^x \ln {c}$"]
    elif variant == "exp":
        a, k = _nonzero(rng, -4, 4), rng.choice([-3, -2, 2, 3, 4, 5])
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
    return f, wrongs, steps


def _build_mixed(rng):
    u = X ** rng.randint(1, 3) if rng.random() < 0.6 else _nonzero(rng, -4, 4) * X
    name = rng.choice(["sin", "cos", "exp"])
    k = rng.randint(2, 4)
    v, dv_outer = _apply(name, k * X)
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
    return f, wrongs, steps


PROBLEM_TYPES = {
    t.id: t
    for t in [
        ProblemType("power", "多項式", r"$x^n$ の和の微分", _build_power),
        ProblemType("power_general", "負・分数の指数", r"$\frac{1}{x^n}$ や $\sqrt{x}$ の微分", _build_power_general),
        ProblemType("product", "積の微分", r"$(uv)' = u'v + uv'$", _build_product),
        ProblemType("quotient", "商の微分", r"$\left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^2}$", _build_quotient),
        ProblemType("chain", "合成関数の微分", r"$\{g(h(x))\}' = g'(h(x))\,h'(x)$", _build_chain),
        ProblemType("trig", "三角関数", r"$\sin kx$、$\cos kx$ の微分", _build_trig),
        ProblemType("explog", "指数・対数関数", r"$a^x$、$e^{kx}$、$\ln$ の微分", _build_explog),
        ProblemType("mixed", "積＋合成関数", r"$x^n \sin kx$ などの組み合わせ", _build_mixed),
    ]
}


def _drop_collisions(answer: sp.Expr, wrongs: list[tuple[str, sp.Expr]]) -> list[tuple[str, sp.Expr]]:
    """正解と同じになる誤答、先に出た誤答と同じになる誤答を除く。

    例えば x^1 の積では「指数を減らし忘れ」が正解と一致するため、診断に使えない。
    """
    kept: list[tuple[str, sp.Expr]] = []
    for mid, expr in wrongs:
        if equivalent(expr, answer):
            continue
        if any(equivalent(expr, other) for _, other in kept):
            continue
        kept.append((mid, expr))
    return kept


def tidy(expr: sp.Expr) -> sp.Expr:
    """答えを読みやすい形にする。

    simplify は sin x + cos x を √2 cos(x - π/4) にするなど、教科書と違う形にすることがあるため、
    π を新たに持ち込まない候補のうち最も短いものを選ぶ。
    """
    candidates = [expr, sp.factor_terms(expr), sp.factor_terms(sp.together(expr)), sp.simplify(expr)]
    if not expr.has(sp.pi):
        candidates = [c for c in candidates if not c.has(sp.pi)]
    return min(candidates, key=sp.count_ops)


def generate(type_id: str, seed: int) -> Problem:
    ptype = PROBLEM_TYPES[type_id]
    rng = random.Random(f"{type_id}-{seed}")
    # 係数の組み合わせによっては f が定数になる（例: (2x+4)/(x+2)）ので作り直す
    for _ in range(10):
        f, wrongs, steps, *display = ptype.build(rng)
        answer = sp.diff(f, X)
        if not equivalent(answer, sp.Integer(0)):
            break
    steps = steps + [rf"$f'(x) = {to_latex(tidy(answer))}$"]
    return Problem(
        problem_id=f"{type_id}-{seed}",
        type_id=type_id,
        f=f,
        answer=answer,
        wrongs=_drop_collisions(answer, wrongs),
        latex=display[0] if display else to_latex(f),
        steps=steps,
    )


def from_id(problem_id: str) -> Problem:
    type_id, _, seed = problem_id.rpartition("-")
    if type_id not in PROBLEM_TYPES or not seed.isdigit():
        raise KeyError(problem_id)
    return generate(type_id, int(seed))
