"""単元「微分の応用」：接線・法線・極値。"""

import sympy as sp

from ..checker import X
from ..core import Built, Misconception, ProblemType, Unit, nonzero, to_latex

UNIT = Unit(
    id="application",
    name="微分の応用",
    prompt="",  # 問題ごとに決める
    answer_prefix="y =",
)

MISCONCEPTIONS = [
    Misconception(
        "tangent_slope_function",
        r"傾きに $f'(a)$ ではなく $f'(x)$ を使った",
        r"接線 $y = f'(a)(x - a) + f(a)$ の傾き $f'(a)$ は数です。$f'(x)$ に $x = a$ を代入した値を使います。",
    ),
    Misconception(
        "tangent_sign",
        r"$(x - a)$ の符号を間違えた",
        r"点 $(a, b)$ を通る傾き $m$ の直線は $y - b = m(x - a)$ です。$x + a$ ではなく $x - a$ です。",
    ),
    Misconception(
        "tangent_no_fa",
        r"$f(a)$ を足し忘れた",
        r"$y = f'(a)(x - a) + f(a)$ です。$+f(a)$ が抜けると、点 $(a, f(a))$ を通らない直線になります。",
    ),
    Misconception(
        "tangent_value_as_slope",
        r"傾きに $f(a)$ を使った",
        r"接線の傾きは関数の値 $f(a)$ ではなく、微分係数 $f'(a)$ です。",
    ),
    Misconception(
        "normal_as_tangent",
        "法線ではなく接線を答えた",
        r"法線は接線に垂直な直線で、傾きは $-\frac{1}{f'(a)}$ です。",
    ),
    Misconception(
        "normal_no_negative",
        "法線の傾きのマイナスを忘れた",
        r"垂直な2直線の傾きの積は $-1$ なので、法線の傾きは $-\frac{1}{f'(a)}$ です。",
    ),
    Misconception(
        "normal_negative_only",
        r"法線の傾きを $-f'(a)$ にした",
        r"法線の傾きは $-f'(a)$ ではなく、逆数にしてマイナスを付けた $-\frac{1}{f'(a)}$ です。",
    ),
    Misconception(
        "extremum_swapped",
        "極大値と極小値を取り違えた",
        r"$f'(x)$ の符号が $+$ から $-$ に変わる点が極大、$-$ から $+$ に変わる点が極小です。増減表を書いて確かめましょう。",
    ),
    Misconception(
        "extremum_x_value",
        r"極値をとる $x$ の値を答えた",
        r"極値は、その点での関数の値です。$f'(a) = 0$ となる $a$ を求めたら、$f(a)$ を計算します。",
    ),
    Misconception(
        "app_box_one_side",
        "切り取る正方形が両端にあることを忘れた",
        r"厚紙の 1 辺の両端から $x$ ずつ切り取るので、箱の底面の 1 辺は $a - x$ ではなく $a - 2x$ です。",
    ),
]


def _random_curve(rng) -> sp.Expr:
    if rng.random() < 0.5:
        return nonzero(rng, -3, 3) * X**2 + rng.randint(-5, 5) * X + rng.randint(-5, 5)
    return nonzero(rng, -2, 2) * X**3 + rng.randint(-4, 4) * X**2 + rng.randint(-5, 5) * X + rng.randint(-3, 3)


def _point(rng, f):
    """接点の x 座標。法線の問題でも使えるよう f'(a) ≠ 0 となる点を選ぶ。"""
    df = sp.diff(f, X)
    candidates = [a for a in range(-2, 4) if df.subs(X, a) != 0]
    return rng.choice(candidates) if candidates else 1


def _build_tangent(rng):
    f = _random_curve(rng)
    a = _point(rng, f)
    fa, dfa = f.subs(X, a), sp.diff(f, X).subs(X, a)
    answer = sp.expand(dfa * (X - a) + fa)
    wrongs = [
        ("tangent_slope_function", sp.diff(f, X) * (X - a) + fa),
        ("tangent_sign", dfa * (X + a) + fa),
        ("tangent_no_fa", dfa * (X - a)),
        ("tangent_value_as_slope", fa * (X - a) + fa),
    ]
    steps = [
        rf"$f'(x) = {to_latex(sp.diff(f, X))}$ より、接線の傾きは $f'({a}) = {dfa}$",
        rf"$f({a}) = {fa}$ なので $y = {dfa}(x - ({a})) + ({fa})$",
    ]
    prompt = rf"曲線 $y = f(x)$ 上の点 $({a}, {fa})$ における接線の方程式を求めなさい。"
    return Built(f, wrongs, steps, answer=answer, prompt=prompt, meta={"a": a})


def _build_normal(rng):
    f = _random_curve(rng)
    a = _point(rng, f)
    fa, dfa = f.subs(X, a), sp.diff(f, X).subs(X, a)
    answer = sp.expand(-(X - a) / dfa + fa)
    wrongs = [
        ("normal_as_tangent", dfa * (X - a) + fa),
        ("normal_no_negative", (X - a) / dfa + fa),
        ("normal_negative_only", -dfa * (X - a) + fa),
        ("tangent_no_fa", -(X - a) / dfa),
    ]
    steps = [
        rf"$f'({a}) = {dfa}$ なので、法線の傾きは $-\frac{{1}}{{f'({a})}} = {to_latex(-sp.Integer(1) / dfa)}$",
        rf"$f({a}) = {fa}$ なので $y = {to_latex(-sp.Integer(1) / dfa)}(x - ({a})) + ({fa})$",
    ]
    prompt = rf"曲線 $y = f(x)$ 上の点 $({a}, {fa})$ における法線の方程式を求めなさい。"
    return Built(f, wrongs, steps, answer=answer, prompt=prompt, meta={"a": a})


def _build_extremum(rng):
    # f'(x) = 3k(x - r1)(x - r2) となる3次関数。係数が整数になるよう r1 + r2 を偶数にする
    while True:
        r1, r2 = sorted(rng.sample(range(-3, 4), 2))
        if (r1 + r2) % 2 == 0:
            break
    k = nonzero(rng, -2, 2)
    c = rng.randint(-5, 5)
    f = sp.expand(k * (X**3 - sp.Rational(3, 2) * (r1 + r2) * X**2 + 3 * r1 * r2 * X) + c)
    # k > 0 なら r1 で極大・r2 で極小、k < 0 なら逆
    max_x, min_x = (r1, r2) if k > 0 else (r2, r1)
    want_max = rng.random() < 0.5
    x0, other = (max_x, min_x) if want_max else (min_x, max_x)
    kind = "極大値" if want_max else "極小値"
    answer = f.subs(X, x0)
    wrongs = [
        ("extremum_swapped", f.subs(X, other)),
        ("extremum_x_value", sp.Integer(x0)),
    ]
    df = sp.diff(f, X)
    steps = [
        rf"$f'(x) = {to_latex(df)} = {to_latex(sp.factor(df))}$ より、$f'(x) = 0$ となるのは $x = {r1}, {r2}$",
        rf"増減表から $x = {max_x}$ で極大、$x = {min_x}$ で極小。{kind}は $f({x0}) = {answer}$",
    ]
    return Built(
        f,
        wrongs,
        steps,
        answer=answer,
        prompt=f"次の関数の{kind}を求めなさい。",
        answer_prefix=rf"\text{{{kind}}} =",
        meta={"x0": x0, "kind": kind},
    )


def _max_on(f: sp.Expr, hi) -> tuple[sp.Expr, sp.Expr]:
    """0 < x < hi での f の最大値と、そのときの x。箱の容積は両端で 0 になるので、内部の極値だけを調べる。"""
    xs = [r for r in sp.solve(sp.diff(f, X), X) if r.is_real and 0 < r < hi]
    best = max(xs, key=lambda r: f.subs(X, r))
    return sp.simplify(f.subs(X, best)), best


def _build_box(rng):
    """文章題：厚紙の四隅を切り取って作る箱の容積の最大値。"""
    k = rng.randint(1, 4)
    # 最大になる x が整数になる縦・横（正方形 6k×6k、長方形 8k×5k）
    a, b = rng.choice([(6 * k, 6 * k), (8 * k, 5 * k)])
    volume = X * (a - 2 * X) * (b - 2 * X)
    answer, x0 = _max_on(volume, sp.Rational(min(a, b), 2))
    one_side, _ = _max_on(X * (a - X) * (b - X), min(a, b))
    wrongs = [
        ("extremum_x_value", x0),
        ("app_box_one_side", one_side),
    ]
    dv = sp.expand(sp.diff(volume, X))
    base = f"1 辺 ${to_latex(a - 2 * X)}$ の正方形" if a == b else f"縦 ${to_latex(b - 2 * X)}$、横 ${to_latex(a - 2 * X)}$ の長方形"
    steps = [
        rf"箱の底面は{base}、高さは $x$ なので $V(x) = x({to_latex(a - 2 * X)})({to_latex(b - 2 * X)})$（$0 < x < {to_latex(sp.Rational(min(a, b), 2))}$）",
        rf"$V'(x) = {to_latex(dv)} = {to_latex(sp.factor(dv))}$ より、$x = {x0}$ で極大かつ最大。$V({x0}) = {answer}$",
    ]
    shape = f"1 辺 {a} cm の正方形" if a == b else f"縦 {b} cm、横 {a} cm の長方形"
    prompt = (
        f"{shape}の厚紙の四隅から、1 辺 $x$ cm の正方形を切り取り、残りを折り曲げてふたのない箱を作る。"
        "箱の容積の最大値を求めなさい。"
    )
    return Built(
        volume,
        wrongs,
        steps,
        latex="",
        answer=answer,
        prompt=prompt,
        answer_prefix=r"\text{容積の最大値} =",
        meta={"a": a, "b": b},
    )


TYPES = [
    ProblemType("app_tangent", "application", "接線の方程式", r"$y = f'(a)(x - a) + f(a)$", _build_tangent),
    ProblemType("app_normal", "application", "法線の方程式", r"$y = -\frac{1}{f'(a)}(x - a) + f(a)$", _build_normal),
    ProblemType("app_extremum", "application", "極大値・極小値", r"3次関数の極値", _build_extremum),
    ProblemType("app_box", "application", "最大・最小（文章題）", r"箱の容積 $V(x)$ を作って最大値を求める", _build_box),
]
