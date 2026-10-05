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
    Misconception(
        "dint_area_sign",
        "上下を逆にして引いた（面積が負になった）",
        r"面積は $\int_\alpha^\beta \{(\text{上のグラフ}) - (\text{下のグラフ})\}\,dx$ です。"
        r"どちらが上にあるか、区間内の 1 点を代入して確かめましょう。面積は必ず正です。",
    ),
    Misconception(
        "dint_area_curve_only",
        "放物線だけを積分した（直線を引き忘れた）",
        r"2 つのグラフで囲まれた部分の面積は、上のグラフから下のグラフを引いた差を積分します。",
    ),
    Misconception(
        "dint_area_no_coef",
        r"$\frac{1}{6}$ 公式で $x^2$ の係数を掛け忘れた",
        r"$\int_\alpha^\beta a(x-\alpha)(x-\beta)\,dx = -\frac{a}{6}(\beta-\alpha)^3$ です。"
        r"差の式の $x^2$ の係数 $a$ も掛けます。",
    ),
    Misconception(
        "dint_displacement",
        "道のりではなく位置の変化（変位）を求めた",
        r"$\int v(t)\,dt$ は位置の変化です。途中で向きが変わる（$v(t)$ の符号が変わる）ときの道のりは "
        r"$\int |v(t)|\,dt$ で、$v(t) = 0$ となる時刻で区間を分けて計算します。",
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


def _build_area(rng):
    """文章題：放物線と直線で囲まれた部分の面積（1/6 公式）。"""
    alpha = rng.randint(-3, 2)
    beta = rng.randint(alpha + 1, min(alpha + 4, 4))
    a = nonzero(rng, -3, 3)
    m, n = rng.randint(-3, 3), rng.randint(-4, 4)
    line = m * X + n
    diff = a * (X - alpha) * (X - beta)  # 放物線 − 直線
    curve = sp.expand(line + diff)
    area = sp.Rational(abs(a) * (beta - alpha) ** 3, 6)
    wrongs = [
        ("dint_area_sign", -area),
        ("dint_area_curve_only", sp.integrate(curve, (X, alpha, beta))),
        ("dint_area_no_coef", sp.Rational((beta - alpha) ** 3, 6)),
    ]
    upper = "直線" if a > 0 else "放物線"
    upper_minus_lower = sp.expand(-diff if a > 0 else diff)
    line_name = "x 軸" if line == 0 else f"直線 $y = {to_latex(line)}$ "
    steps = [
        rf"$y$ を消去すると ${to_latex(sp.expand(diff))} = 0$、${to_latex(sp.factor(diff))} = 0$ より交点は $x = {alpha}, {beta}$",
        rf"${alpha} < x < {beta}$ では{upper}が上にあるので "
        rf"$S = \int_{{{alpha}}}^{{{beta}}} \left({to_latex(upper_minus_lower)}\right) dx = \frac{{{abs(a)}}}{{6}} \cdot {beta - alpha}^3$",
    ]
    prompt = f"放物線 $y = {to_latex(curve)}$ と{line_name}で囲まれた部分の面積 $S$ を求めなさい。"
    return Built(
        curve,
        wrongs,
        steps,
        latex="",
        answer=area,
        prompt=prompt,
        answer_prefix="S =",
        meta={"lo": alpha, "hi": beta, "line": line},
    )


def _build_distance(rng):
    """文章題：速度から道のりを求める（途中で向きが変わる）。"""
    k = nonzero(rng, -3, 3)
    r = rng.randint(1, 3)
    T = rng.randint(r + 1, r + 3)
    v = k * (X - r)
    distance = sp.Rational(abs(k) * (r**2 + (T - r) ** 2), 2)
    displacement = sp.integrate(v, (X, 0, T))
    wrongs = [
        ("dint_displacement", displacement),
        ("dint_displacement", abs(displacement)),
    ]
    t = sp.Symbol("t")
    vt = to_latex(v.subs(X, t))
    steps = [
        rf"$v(t) = 0$ となるのは $t = {r}$。$0 \leq t \leq {r}$ と ${r} \leq t \leq {T}$ で $v(t)$ の符号が変わる",
        rf"道のりは $\int_0^{{{T}}} |v(t)|\,dt = \left|\int_0^{{{r}}} v(t)\,dt\right| + \left|\int_{{{r}}}^{{{T}}} v(t)\,dt\right|"
        rf" = {to_latex(sp.Rational(abs(k) * r**2, 2))} + {to_latex(sp.Rational(abs(k) * (T - r) ** 2, 2))}$",
    ]
    prompt = (
        rf"数直線上を動く点 P の時刻 $t$ における速度は $v(t) = {vt}$ である。"
        rf"$t = 0$ から $t = {T}$ までに P が動いた道のりを求めなさい。"
    )
    return Built(
        v,
        wrongs,
        steps,
        latex=rf"v(t) = {vt}",
        answer=distance,
        prompt=prompt,
        answer_prefix=r"\text{道のり} =",
        meta={"lo": 0, "hi": T, "r": r},
    )


TYPES = [
    ProblemType("dint_poly", "definite", "多項式", r"$\int_a^b (ax^2 + bx + c)\,dx$", _build_poly),
    ProblemType("dint_trig", "definite", "三角関数", r"$\int_0^{\pi} \sin x\,dx$ など", _build_trig),
    ProblemType("dint_explog", "definite", "指数・対数関数", r"$\int_0^1 e^{kx}\,dx$、$\int_1^e \frac{1}{x}\,dx$ など", _build_explog),
    ProblemType("dint_area", "definite", "囲まれた部分の面積（文章題）", r"$\int_\alpha^\beta (\text{上} - \text{下})\,dx$", _build_area),
    ProblemType("dint_distance", "definite", "速度と道のり（文章題）", r"$\int |v(t)|\,dt$", _build_distance),
]
