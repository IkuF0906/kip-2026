"""単元「数列」：一般項・和・Σ・漸化式。答えは n の式。"""

import sympy as sp

from ..checker import N
from ..core import Built, Misconception, ProblemType, Unit, nonzero, to_latex

UNIT = Unit(
    id="sequence",
    name="数列",
    prompt="",  # 問題ごとに決める
    answer_prefix="a_n =",
    var=N,
)

MISCONCEPTIONS = [
    Misconception(
        "seq_n_not_minus1",
        r"公差を $n-1$ 回ではなく $n$ 回足した",
        r"初項から第 $n$ 項までに公差を足す回数は $n-1$ 回です。一般項は $a_n = a + (n-1)d$ です。",
    ),
    Misconception(
        "seq_diff_no_divide",
        "公差を求めるとき、項の番号の差で割り忘れた",
        r"第 $p$ 項と第 $q$ 項の間には公差が $q-p$ 個あります。$d = \frac{a_q - a_p}{q - p}$ です。",
    ),
    Misconception(
        "seq_sum_no_half",
        "等差数列の和で 2 で割り忘れた",
        r"等差数列の和は $S_n = \frac{n\{2a + (n-1)d\}}{2}$ です。"
        r"（初項＋末項）× 項数を 2 で割ります。",
    ),
    Misconception(
        "seq_term_for_sum",
        "和ではなく第 n 項を答えた",
        r"問われているのは第 $n$ 項までの合計（和 $S_n$）です。一般項 $a_n$ を求めたら、和の公式を使います。",
    ),
    Misconception(
        "seq_geom_power",
        r"等比数列の和で $r^n$ ではなく $r^{n-1}$ を使った",
        r"等比数列の和は $S_n = \frac{a(r^n - 1)}{r - 1}$ です。一般項 $ar^{n-1}$ の指数と取り違えないようにしましょう。",
    ),
    Misconception(
        "seq_geom_no_divide",
        r"等比数列の和で $r-1$ で割り忘れた",
        r"$S_n - rS_n$ を計算すると $(1-r)S_n = a(1 - r^n)$ なので、$r-1$ で割る必要があります。",
    ),
    Misconception(
        "seq_sigma_const",
        r"$\sum c$ を $c$ とした",
        r"定数 $c$ を $n$ 個足すので $\sum_{k=1}^{n} c = cn$ です。",
    ),
    Misconception(
        "seq_sigma_square",
        r"$\sum k^2$ を $\left(\sum k\right)^2$ とした",
        r"$\sum_{k=1}^{n} k^2 = \frac{n(n+1)(2n+1)}{6}$ です。$\left\{\frac{n(n+1)}{2}\right\}^2$ は $\sum k^3$ の公式です。",
    ),
    Misconception(
        "seq_diff_upper_n",
        "階差数列の和を k = n まで取った",
        r"$a_n = a_1 + \sum_{k=1}^{n-1} b_k$ です。$a_n$ までに足す階差は $n-1$ 個なので、和の上端は $n-1$ です。",
    ),
    Misconception(
        "seq_diff_no_a1",
        "初項 $a_1$ を足し忘れた",
        r"$a_n = a_1 + \sum_{k=1}^{n-1} b_k$ です。階差の和に初項を足します。",
    ),
    Misconception(
        "seq_recur_power_n",
        r"$p^{n-1}$ ではなく $p^n$ にした",
        r"$a_n - \alpha$ は初項 $a_1 - \alpha$、公比 $p$ の等比数列なので、$a_n - \alpha = (a_1 - \alpha)p^{n-1}$ です。",
    ),
    Misconception(
        "seq_recur_no_alpha",
        "定数項を無視して等比数列とした",
        r"$a_{n+1} = pa_n + q$ は、$\alpha = p\alpha + q$ を満たす $\alpha$ を使って "
        r"$a_{n+1} - \alpha = p(a_n - \alpha)$ と変形してから等比数列とみます。",
    ),
    Misconception(
        "seq_recur_alpha_sign",
        r"$a_n - \alpha$ の符号を間違えた",
        r"$\alpha = p\alpha + q$ を解いて、$a_{n+1} - \alpha = p(a_n - \alpha)$ と変形します。"
        r"$\alpha$ の符号を確かめましょう。",
    ),
]


def _p(v) -> str:
    """負の数だけ括弧で囲む（式の途中に代入した値を書くため）。"""
    return f"({v})" if v < 0 else str(v)


def _minus(v) -> str:
    """「a_n - v」の「- v」の部分（v が負なら + |v|）。"""
    return f"+ {-v}" if v < 0 else f"- {v}"


def _arith(a, d):
    return a + (N - 1) * d


def _arith_sum(a, d):
    return N * (2 * a + (N - 1) * d) / 2


def _build_arith(rng):
    """2つの項から等差数列の一般項を求める。"""
    a, d = rng.randint(-9, 9), nonzero(rng, -5, 5)
    p = rng.randint(2, 4)
    q = rng.randint(p + 2, p + 6)
    ap, aq = a + (p - 1) * d, a + (q - 1) * d
    # 公差を aq - ap としてしまったときの数列（第 p 項は合っている）
    d2 = aq - ap
    wrongs = [
        ("seq_n_not_minus1", a + N * d),
        ("seq_diff_no_divide", ap + (N - p) * d2),
    ]
    steps = [
        rf"公差を $d$ とすると $a_{{{q}}} - a_{{{p}}} = {q - p}d$ なので $d = \frac{{{aq} - {_p(ap)}}}{{{q - p}}} = {d}$",
        rf"初項は $a_1 = a_{{{p}}} - {p - 1}d = {a}$、一般項は $a_n = {a} + (n-1) \cdot {_p(d)}$",
    ]
    return Built(
        _arith(a, d),
        wrongs,
        steps,
        latex=rf"a_{{{p}}} = {ap}, \quad a_{{{q}}} = {aq}",
        answer=sp.expand(_arith(a, d)),
        prompt="次の条件を満たす等差数列 $\\{a_n\\}$ の一般項を求めなさい。",
        meta={"kind": "arith", "a": a, "d": d, "p": p, "q": q, "ap": ap, "aq": aq},
    )


def _build_arith_sum(rng):
    """文章題：座席の合計（等差数列の和）。"""
    a, d = rng.randint(10, 30), rng.randint(2, 4)
    wrongs = [
        ("seq_n_not_minus1", N * (2 * a + N * d) / 2),
        ("seq_sum_no_half", N * (2 * a + (N - 1) * d)),
        ("seq_term_for_sum", _arith(a, d)),
    ]
    steps = [
        rf"各列の座席数は初項 ${a}$、公差 ${d}$ の等差数列で、$n$ 列目は ${a} + (n-1) \cdot {d} = {to_latex(sp.expand(_arith(a, d)))}$ 席",
        rf"和の公式 $S_n = \frac{{n\{{2a + (n-1)d\}}}}{{2}}$ に $a = {a}$、$d = {d}$ を代入する",
    ]
    prompt = (
        f"ある劇場の座席は、1 列目が {a} 席で、後ろの列になるごとに {d} 席ずつ増えている。"
        "1 列目から $n$ 列目までの座席の合計を $n$ の式で表しなさい。"
    )
    return Built(
        _arith_sum(a, d),
        wrongs,
        steps,
        latex="",
        answer=_arith_sum(a, d),
        prompt=prompt,
        answer_prefix="S_n =",
        meta={"kind": "arith_sum", "a": a, "d": d},
    )


def _build_geom_sum(rng):
    """文章題：毎日 r 倍にする貯金（等比数列の和）。"""
    a, r = rng.choice([1, 2, 3, 5, 10]), rng.choice([2, 3])
    answer = a * (r**N - 1) / (r - 1)
    wrongs = [
        ("seq_geom_power", a * (r ** (N - 1) - 1) / (r - 1)),
        ("seq_geom_no_divide", a * (r**N - 1)),
        ("seq_term_for_sum", a * r ** (N - 1)),
    ]
    steps = [
        rf"$k$ 日目の金額は初項 ${a}$、公比 ${r}$ の等比数列で ${to_latex(a * r ** (N - 1))}$ 円",
        rf"和の公式 $S_n = \frac{{a(r^n - 1)}}{{r - 1}}$ に $a = {a}$、$r = {r}$ を代入する",
    ]
    times = {2: "2 倍", 3: "3 倍"}[r]
    prompt = (
        f"1 日目に {a} 円を貯金し、2 日目からは前の日の {times}の金額を貯金する。"
        "1 日目から $n$ 日目までに貯金した金額の合計を $n$ の式で表しなさい。"
    )
    return Built(
        answer,
        wrongs,
        steps,
        latex="",
        answer=answer,
        prompt=prompt,
        answer_prefix="S_n =",
        meta={"kind": "geom_sum", "a": a, "r": r},
    )


def _sum_k(n):
    return n * (n + 1) / 2


def _sum_k2(n):
    return n * (n + 1) * (2 * n + 1) / 6


def _build_sigma(rng):
    a, b, c = nonzero(rng, -3, 3), rng.randint(-4, 4), nonzero(rng, -5, 5)
    k = sp.Symbol("k")
    term = a * k**2 + b * k + c
    answer = a * _sum_k2(N) + b * _sum_k(N) + c * N
    wrongs = [
        ("seq_sigma_const", a * _sum_k2(N) + b * _sum_k(N) + c),
        ("seq_sigma_square", a * _sum_k(N) ** 2 + b * _sum_k(N) + c * N),
    ]
    steps = [
        r"$\sum k^2 = \frac{n(n+1)(2n+1)}{6}$、$\sum k = \frac{n(n+1)}{2}$、$\sum c = cn$ を使う",
        rf"${a} \cdot \frac{{n(n+1)(2n+1)}}{{6}} + {_p(b)} \cdot \frac{{n(n+1)}}{{2}} + {_p(c)} n$ を整理する",
    ]
    return Built(
        answer,
        wrongs,
        steps,
        latex=rf"\sum_{{k=1}}^{{n}} \left({to_latex(term)}\right)",
        answer=answer,
        prompt="次の和を求めなさい。",
        answer_prefix="=",
        meta={"kind": "sigma", "term": term, "k": k},
    )


def _build_diff(rng):
    """階差数列 a_{n+1} = a_n + (pn + q)。"""
    a1, p, q = rng.randint(-5, 5), nonzero(rng, -3, 3) * 2, rng.randint(-4, 4)
    # Σ_{k=1}^{n-1} (pk + q)
    answer = a1 + p * _sum_k(N - 1) + q * (N - 1)
    wrongs = [
        ("seq_diff_upper_n", a1 + p * _sum_k(N) + q * N),
        ("seq_diff_no_a1", p * _sum_k(N - 1) + q * (N - 1)),
    ]
    b = p * N + q
    b_latex = to_latex(b)
    rhs = f"a_n {b_latex}" if b_latex.startswith("-") else f"a_n + {b_latex}"
    steps = [
        rf"階差数列は $b_n = {to_latex(b)}$ なので、$n \geq 2$ のとき $a_n = {a1} + \sum_{{k=1}}^{{n-1}} ({to_latex(b.subs(N, sp.Symbol('k')))})$",
        rf"$\sum_{{k=1}}^{{n-1}} k = \frac{{(n-1)n}}{{2}}$ を使って整理する（$n = 1$ のときも成り立つ）",
    ]
    return Built(
        answer,
        wrongs,
        steps,
        latex=rf"a_1 = {a1}, \quad a_{{n+1}} = {rhs}",
        answer=sp.expand(answer),
        prompt=r"次の条件で定まる数列 $\{a_n\}$ の一般項を求めなさい。",
        meta={"kind": "recur", "a1": a1, "next": lambda an, n: an + p * n + q},
    )


def _build_recur(rng):
    """漸化式 a_{n+1} = p a_n + q（特性方程式で等比数列に直す）。"""
    p = rng.choice([2, 3])
    alpha = nonzero(rng, -4, 4)
    q = alpha * (1 - p)
    a1 = rng.choice([v for v in range(-4, 6) if v != alpha and v != -alpha])
    answer = (a1 - alpha) * p ** (N - 1) + alpha
    wrongs = [
        ("seq_recur_power_n", (a1 - alpha) * p**N + alpha),
        ("seq_recur_no_alpha", a1 * p ** (N - 1)),
        ("seq_recur_alpha_sign", (a1 + alpha) * p ** (N - 1) - alpha),
    ]
    rhs = to_latex(p * sp.Symbol("a_n") + q)
    m = _minus(alpha)
    q_term = f"- {-q}" if q < 0 else f"+ {q}"
    steps = [
        rf"$\alpha = {p}\alpha {q_term}$ を解くと $\alpha = {alpha}$。$a_{{n+1}} {m} = {p}(a_n {m})$ と変形できる",
        rf"$\{{a_n {m}\}}$ は初項 $a_1 {m} = {a1 - alpha}$、公比 ${p}$ の等比数列なので $a_n {m} = {_p(a1 - alpha)} \cdot {p}^{{n-1}}$",
    ]
    return Built(
        answer,
        wrongs,
        steps,
        latex=rf"a_1 = {a1}, \quad a_{{n+1}} = {rhs}",
        answer=answer,
        prompt=r"次の条件で定まる数列 $\{a_n\}$ の一般項を求めなさい。",
        meta={"kind": "recur", "a1": a1, "next": lambda an, n: p * an + q},
    )


TYPES = [
    ProblemType("seq_arith", "sequence", "等差数列の一般項", r"$a_n = a + (n-1)d$", _build_arith),
    ProblemType("seq_arith_sum", "sequence", "等差数列の和（文章題）", r"$S_n = \frac{n\{2a + (n-1)d\}}{2}$", _build_arith_sum),
    ProblemType("seq_geom_sum", "sequence", "等比数列の和（文章題）", r"$S_n = \frac{a(r^n - 1)}{r - 1}$", _build_geom_sum),
    ProblemType("seq_sigma", "sequence", "Σ の計算", r"$\sum k^2$、$\sum k$、$\sum c$ の公式", _build_sigma),
    ProblemType("seq_diff", "sequence", "階差数列", r"$a_n = a_1 + \sum_{k=1}^{n-1} b_k$", _build_diff),
    ProblemType("seq_recur", "sequence", "漸化式 a(n+1) = p a(n) + q", r"$a_{n+1} - \alpha = p(a_n - \alpha)$", _build_recur),
]
