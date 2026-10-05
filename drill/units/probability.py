"""単元「場合の数・確率」：文章題。答えは数（場合の数、または分数の確率）。"""

from math import comb, factorial, perm

import sympy as sp

from ..core import Built, Misconception, ProblemType, Unit

UNIT = Unit(
    id="probability",
    name="場合の数・確率",
    prompt="",  # 問題ごとに決める
    answer_prefix="P =",
)

MISCONCEPTIONS = [
    Misconception(
        "prob_perm_for_comb",
        "選ぶだけなのに順列で数えた",
        r"選ぶだけで順番を区別しないときは組合せ ${}_n\mathrm{C}_r = \frac{{}_n\mathrm{P}_r}{r!}$ です。"
        r"同じ組を $r!$ 回ずつ数えていないか確かめましょう。",
    ),
    Misconception(
        "prob_comb_for_perm",
        "役割や順番を区別するのに組合せで数えた",
        r"委員長・副委員長のように役割が違うときは、選んだ人の並べ方も区別するので順列 ${}_n\mathrm{P}_r$ です。",
    ),
    Misconception(
        "prob_power",
        "同じ人を何度も選べるとして数えた",
        r"$n^r$ は同じものを繰り返し選べるとき（重複順列）の数です。1 人を 2 回選ぶことはできません。",
    ),
    Misconception(
        "prob_circle_no_divide",
        "円順列で回転して同じになる並び方を区別した",
        r"円形に並べるときは、回転して重なるものは同じです。1 人を固定して残りを並べ、$(n-1)!$ 通りです。",
    ),
    Misconception(
        "prob_same_no_divide",
        "同じものを区別して数えた",
        r"同じ文字どうしを入れ替えても並びは変わりません。$\frac{n!}{p!\,q!\,r!}$ のように、同じものの個数の階乗で割ります。",
    ),
    Misconception(
        "prob_adjacent_no_swap",
        "隣り合う 2 人の並び方（2 通り）を掛け忘れた",
        r"隣り合う 2 人を 1 組とみて $(n-1)!$ 通り並べたあと、組の中での並び方 $2!$ 通りを掛けます。",
    ),
    Misconception(
        "prob_ignore_condition",
        "条件を考えずに全体の並べ方を答えた",
        r"$n!$ は条件のない並べ方の総数です。条件を満たすものだけを数えましょう。",
    ),
    Misconception(
        "prob_complement_forgot",
        "余事象の確率を 1 から引き忘れた",
        r"「少なくとも 1 回」は、余事象「1 回も起こらない」の確率 $(1-p)^n$ を 1 から引いて $1 - (1-p)^n$ です。",
    ),
    Misconception(
        "prob_add_probs",
        "1 回ごとの確率を回数分足した",
        r"各回の事象は互いに排反ではないので、確率を足すことはできません（回数が多いと 1 を超えてしまいます）。"
        r"余事象を使いましょう。",
    ),
    Misconception(
        "prob_all_times",
        "すべての回で起こる確率を求めた",
        r"$p^n$ は「$n$ 回とも起こる」確率です。「少なくとも 1 回」は $1 - (1-p)^n$ です。",
    ),
    Misconception(
        "prob_binom_no_comb",
        r"反復試行で ${}_n\mathrm{C}_k$ を掛け忘れた",
        r"$n$ 回のうち、どの $k$ 回で起こるかが ${}_n\mathrm{C}_k$ 通りあります。"
        r"確率は ${}_n\mathrm{C}_k\,p^k(1-p)^{n-k}$ です。",
    ),
    Misconception(
        "prob_binom_no_fail",
        r"起こらない回の確率 $(1-p)^{n-k}$ を掛け忘れた",
        r"残りの $n-k$ 回は「起こらない」ので、その確率 $(1-p)^{n-k}$ も掛けます。",
    ),
    Misconception(
        "prob_with_replacement",
        "取り出した玉を戻すとして計算した",
        r"戻さないときは、2 回目は袋の中の玉が 1 個減っています。2 回目の確率は残りの玉で考えます。",
    ),
    Misconception(
        "prob_denominator_same",
        "2 回目の分母を減らし忘れた",
        r"1 回目に取り出した玉は戻さないので、2 回目の全体の個数は 1 個少なくなります。",
    ),
    Misconception(
        "prob_order_forgot",
        "取り出す順番（赤→白と白→赤）の片方だけを数えた",
        r"「1 個ずつ赤と白」には、赤→白と白→赤の 2 通りの順番があります。両方の確率を足します。",
    ),
    Misconception(
        "prob_cond_joint",
        r"条件付き確率ではなく $P(A \cap B)$ を答えた",
        r"「不良品だったとき、それが A 製である確率」は、不良品全体に占める A 製の不良品の割合です。"
        r"$P_B(A) = \frac{P(A \cap B)}{P(B)}$ のように、不良品である確率で割ります。",
    ),
    Misconception(
        "prob_cond_reversed",
        r"$P_B(A)$ と $P_A(B)$ を取り違えた",
        r"A 製の製品が不良品である確率 $P_A(B)$ と、不良品が A 製である確率 $P_B(A)$ は別のものです。",
    ),
    Misconception(
        "prob_expect_plain_mean",
        "賞金の額を単純に平均した",
        r"期待値は、それぞれの値にその値をとる確率を掛けて足したもの $\sum x_i p_i$ です。本数（確率）の違いを考えます。",
    ),
    Misconception(
        "prob_expect_no_divide",
        "くじの総数で割り忘れた",
        r"確率は「その本数 ÷ くじの総数」です。期待値は $\sum x_i p_i$ なので、総数で割る必要があります。",
    ),
]

def _built(answer, wrongs, steps, prompt, prefix, meta) -> Built:
    return Built(
        sp.nsimplify(answer),
        [(mid, sp.nsimplify(w)) for mid, w in wrongs],
        steps,
        latex="",
        answer=sp.nsimplify(answer),
        prompt=prompt,
        answer_prefix=prefix,
        meta=meta,
    )


def _build_perm_comb(rng):
    n = rng.randint(6, 10)
    if rng.random() < 0.5:
        r = rng.randint(2, 4)
        answer = comb(n, r)
        ordered = False
        wrongs = [("prob_perm_for_comb", perm(n, r)), ("prob_power", n**r)]
        prompt = f"{n} 人の中から {r} 人の委員を選ぶ。選び方は何通りあるか。"
        steps = [
            "選ぶだけで順番は区別しないので組合せ",
            rf"${{}}_{{{n}}}\mathrm{{C}}_{{{r}}} = \frac{{{n}!}}{{{r}!\,{n - r}!}} = {answer}$",
        ]
    else:
        roles = rng.choice([["委員長", "副委員長"], ["委員長", "副委員長", "書記"]])
        r = len(roles)
        answer = perm(n, r)
        ordered = True
        wrongs = [("prob_comb_for_perm", comb(n, r)), ("prob_power", n**r)]
        prompt = f"{n} 人の中から{'・'.join(roles)}を 1 人ずつ選ぶ。選び方は何通りあるか。"
        steps = [
            "役割が違うので、選んだ人の並び方も区別する（順列）",
            rf"${{}}_{{{n}}}\mathrm{{P}}_{{{r}}} = " + r" \cdot ".join(str(n - i) for i in range(r)) + rf" = {answer}$",
        ]
    return _built(answer, wrongs, steps, prompt, r"\text{選び方} =", {"n": n, "r": r, "ordered": ordered})


_WORDS = ["AABBBC", "AAABBC", "AABBCC", "AAABBB", "AABBCD", "AAAABC"]


def _build_arrange(rng):
    variant = rng.choice(["circle", "same", "adjacent"])
    if variant == "circle":
        n = rng.randint(4, 8)
        answer = factorial(n - 1)
        wrongs = [("prob_circle_no_divide", factorial(n))]
        prompt = f"{n} 人が円形のテーブルのまわりに座る。座り方は何通りあるか。"
        steps = [
            "回転して重なる座り方は同じなので、1 人の位置を固定する",
            rf"残りの {n - 1} 人の並べ方で $({n}-1)! = {answer}$",
        ]
        prefix = r"\text{座り方} ="
    elif variant == "same":
        word = rng.choice(_WORDS)
        counts = [word.count(ch) for ch in sorted(set(word))]
        n = len(word)
        denom = 1
        for c in counts:
            denom *= factorial(c)
        answer = factorial(n) // denom
        wrongs = [("prob_same_no_divide", factorial(n))]
        prompt = f"{len(word)} 個の文字 {', '.join(word)} を 1 列に並べる。並べ方は何通りあるか。"
        frac_den = r"\,".join(f"{c}!" for c in counts)
        steps = [
            "同じ文字どうしを入れ替えても同じ並びなので、同じものの個数の階乗で割る",
            rf"$\frac{{{n}!}}{{{frac_den}}} = {answer}$",
        ]
        prefix = r"\text{並べ方} ="
    else:
        n = rng.randint(4, 7)
        answer = 2 * factorial(n - 1)
        wrongs = [
            ("prob_adjacent_no_swap", factorial(n - 1)),
            ("prob_ignore_condition", factorial(n)),
        ]
        prompt = f"A, B を含む {n} 人が 1 列に並ぶ。A と B が隣り合う並び方は何通りあるか。"
        steps = [
            rf"A と B を 1 組とみて、{n - 1} 人分を並べる：$({n}-1)! = {factorial(n - 1)}$ 通り",
            rf"組の中の A, B の並び方が $2! = 2$ 通りあるので $2 \times {factorial(n - 1)} = {answer}$",
        ]
        prefix = r"\text{並べ方} ="
    return _built(answer, wrongs, steps, prompt, prefix, {"variant": variant, "n": n, "word": word if variant == "same" else None})


# さいころ 1 回で起こる事象: (説明, その事象になる目)
_DICE_EVENTS = [
    ("1 の目が出る", {1}),
    ("6 の目が出る", {6}),
    ("3 の倍数の目が出る", {3, 6}),
    ("5 以上の目が出る", {5, 6}),
    ("偶数の目が出る", {2, 4, 6}),
]


def _build_complement(rng):
    event, faces = rng.choice(_DICE_EVENTS)
    p = sp.Rational(len(faces), 6)
    n = rng.randint(2, 4)
    answer = 1 - (1 - p) ** n
    wrongs = [
        ("prob_complement_forgot", (1 - p) ** n),
        ("prob_add_probs", n * p),
        ("prob_all_times", p**n),
    ]
    prompt = f"1 個のさいころを {n} 回投げるとき、{event}ことが少なくとも 1 回ある確率を求めなさい。"
    steps = [
        rf"余事象は「{n} 回とも{event.replace('出る', '出ない')}」で、その確率は $\left({sp.latex(1 - p)}\right)^{{{n}}} = {sp.latex((1 - p) ** n)}$",
        rf"求める確率は $1 - {sp.latex((1 - p) ** n)}$",
    ]
    return _built(answer, wrongs, steps, prompt, "P =", {"faces": faces, "n": n})


def _build_binomial(rng):
    event, faces = rng.choice(_DICE_EVENTS)
    p = sp.Rational(len(faces), 6)
    n = rng.randint(3, 5)
    k = rng.randint(1, n - 1)
    answer = comb(n, k) * p**k * (1 - p) ** (n - k)
    wrongs = [
        ("prob_binom_no_comb", p**k * (1 - p) ** (n - k)),
        ("prob_binom_no_fail", comb(n, k) * p**k),
    ]
    prompt = f"1 個のさいころを {n} 回投げるとき、{event}回数がちょうど {k} 回である確率を求めなさい。"
    pl, ql = sp.latex(p), sp.latex(1 - p)
    steps = [
        rf"{event}確率は 1 回あたり ${pl}$。{n} 回のうちどの {k} 回かで ${{}}_{{{n}}}\mathrm{{C}}_{{{k}}} = {comb(n, k)}$ 通り",
        rf"${comb(n, k)} \times \left({pl}\right)^{{{k}}} \times \left({ql}\right)^{{{n - k}}}$",
    ]
    return _built(answer, wrongs, steps, prompt, "P =", {"faces": faces, "n": n, "k": k})


def _build_draw(rng):
    red, white = rng.randint(2, 6), rng.randint(2, 6)
    total = red + white
    base = f"袋の中に赤玉が {red} 個、白玉が {white} 個入っている。この袋から玉を 1 個ずつ 2 回、取り出した玉を戻さずに取り出す。"
    if rng.random() < 0.5:
        answer = sp.Rational(red, total) * sp.Rational(red - 1, total - 1)
        wrongs = [
            ("prob_with_replacement", sp.Rational(red, total) ** 2),
            ("prob_denominator_same", sp.Rational(red * (red - 1), total**2)),
        ]
        prompt = base + "2 個とも赤玉である確率を求めなさい。"
        steps = [
            rf"1 回目に赤：$\frac{{{red}}}{{{total}}}$。残りは赤 {red - 1} 個・全体 {total - 1} 個なので、2 回目も赤：$\frac{{{red - 1}}}{{{total - 1}}}$",
            rf"$\frac{{{red}}}{{{total}}} \times \frac{{{red - 1}}}{{{total - 1}}}$",
        ]
        kind = "both_red"
    else:
        one_order = sp.Rational(red, total) * sp.Rational(white, total - 1)
        answer = 2 * one_order
        wrongs = [
            ("prob_order_forgot", one_order),
            ("prob_with_replacement", 2 * sp.Rational(red * white, total**2)),
        ]
        prompt = base + "赤玉と白玉が 1 個ずつ出る確率を求めなさい。"
        steps = [
            rf"赤→白：$\frac{{{red}}}{{{total}}} \times \frac{{{white}}}{{{total - 1}}}$、白→赤：$\frac{{{white}}}{{{total}}} \times \frac{{{red}}}{{{total - 1}}}$",
            "2 つの順番は互いに排反なので、確率を足す",
        ]
        kind = "one_each"
    return _built(answer, wrongs, steps, prompt, "P =", {"red": red, "white": white, "kind": kind})


def _build_conditional(rng):
    """原因の確率（ベイズ）：不良品が機械 A 製である確率。"""
    share_a = rng.choice([30, 40, 60, 70])
    rate_a, rate_b = rng.sample([1, 2, 3, 4, 5], 2)
    pa, pb = sp.Rational(share_a, 100), sp.Rational(100 - share_a, 100)
    da, db = sp.Rational(rate_a, 100), sp.Rational(rate_b, 100)
    joint_a = pa * da
    answer = joint_a / (joint_a + pb * db)
    wrongs = [
        ("prob_cond_joint", joint_a),
        ("prob_cond_reversed", da),
    ]
    prompt = (
        f"ある製品は、機械 A で全体の {share_a}%、機械 B で残りの {100 - share_a}% が作られている。"
        f"不良品の割合は、A で作ったものでは {rate_a}%、B で作ったものでは {rate_b}% である。"
        "製品の中から 1 個を取り出したところ不良品だった。それが機械 A で作られたものである確率を求めなさい。"
    )
    # 製品 10000 個あたりの不良品の個数で考えると、分数が入れ子にならない
    bad_a, bad_b = share_a * rate_a, (100 - share_a) * rate_b
    steps = [
        rf"製品 10000 個あたり、A 製の不良品は ${share_a * 100} \times \frac{{{rate_a}}}{{100}} = {bad_a}$ 個、"
        rf"B 製の不良品は ${(100 - share_a) * 100} \times \frac{{{rate_b}}}{{100}} = {bad_b}$ 個",
        rf"不良品 ${bad_a + bad_b}$ 個のうち A 製は ${bad_a}$ 個なので $\frac{{{bad_a}}}{{{bad_a + bad_b}}}$",
    ]
    return _built(answer, wrongs, steps, prompt, "P =", {"kind": "bayes", "pa": pa, "da": da, "db": db})


def _build_expectation(rng):
    """くじの賞金の期待値。"""
    prizes = sorted(rng.sample([10, 50, 100, 500, 1000], 2), reverse=True)
    counts = [rng.randint(1, 3), rng.randint(3, 10)]
    total = rng.choice([20, 50, 100])
    lose = total - sum(counts)
    answer = sp.Rational(sum(x * c for x, c in zip(prizes, counts)), total)
    wrongs = [
        ("prob_expect_plain_mean", sp.Rational(sum(prizes), 3)),  # はずれ（0 円）を含めた 3 種類の平均
        ("prob_expect_no_divide", sum(x * c for x, c in zip(prizes, counts))),
    ]
    prompt = (
        f"{total} 本のくじの中に、{prizes[0]} 円の当たりが {counts[0]} 本、{prizes[1]} 円の当たりが {counts[1]} 本あり、"
        f"残りの {lose} 本ははずれ（0 円）である。このくじを 1 本引くときにもらえる金額の期待値を求めなさい。"
    )
    steps = [
        rf"それぞれの確率は $\frac{{{counts[0]}}}{{{total}}}$、$\frac{{{counts[1]}}}{{{total}}}$、$\frac{{{lose}}}{{{total}}}$",
        rf"${prizes[0]} \times \frac{{{counts[0]}}}{{{total}}} + {prizes[1]} \times \frac{{{counts[1]}}}{{{total}}} + 0 \times \frac{{{lose}}}{{{total}}}$",
    ]
    meta = {"kind": "expectation", "prizes": prizes, "counts": counts, "total": total}
    return _built(answer, wrongs, steps, prompt, r"\text{期待値} =", meta)


TYPES = [
    ProblemType("prob_perm_comb", "probability", "順列と組合せ", r"${}_n\mathrm{P}_r$ と ${}_n\mathrm{C}_r$ の使い分け", _build_perm_comb),
    ProblemType("prob_arrange", "probability", "いろいろな並べ方", r"円順列・同じものを含む順列・隣り合う並び方", _build_arrange),
    ProblemType("prob_complement", "probability", "余事象（少なくとも 1 回）", r"$1 - (1-p)^n$", _build_complement),
    ProblemType("prob_binomial", "probability", "反復試行", r"${}_n\mathrm{C}_k\,p^k(1-p)^{n-k}$", _build_binomial),
    ProblemType("prob_draw", "probability", "玉を戻さずに取り出す", r"2 回目は残りの玉で考える", _build_draw),
    ProblemType("prob_conditional", "probability", "条件付き確率", r"$P_B(A) = \frac{P(A \cap B)}{P(B)}$", _build_conditional),
    ProblemType("prob_expectation", "probability", "期待値", r"$E = \sum x_i p_i$", _build_expectation),
]
