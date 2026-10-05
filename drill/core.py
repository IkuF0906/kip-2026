"""単元・問題の型・誤答パターンのデータ構造と、各単元で共通に使う補助関数。"""

import random
from dataclasses import dataclass, field
from typing import Callable

import sympy as sp

from .checker import C, N, X, equivalent


@dataclass(frozen=True)
class Misconception:
    id: str
    label: str
    explanation: str  # $...$ で囲んだ部分は LaTeX


@dataclass(frozen=True)
class Unit:
    """単元。問題文・解答欄の表示・正解の判定方法を単元ごとに持つ。"""

    id: str
    name: str
    prompt: str  # 既定の問題文（$...$ は LaTeX）
    answer_prefix: str  # 解答欄の左に出す LaTeX
    # 2つの答えを同じとみなすか。不定積分では積分定数の違いを無視する
    same: Callable[[sp.Expr, sp.Expr], bool] = equivalent
    # 問題の式から正解を求める（問題の型が正解を直接作る単元では None）
    solve: Callable[[sp.Expr], sp.Expr] | None = None
    answer_suffix: str = ""  # 正解の表示の後ろに付ける LaTeX（不定積分の + C）
    needs_constant: bool = False  # 積分定数 C を書くよう促す（不定積分）
    var: sp.Symbol = X  # 解答に使う変数（数列では n）

    def allowed_symbols(self) -> set[sp.Symbol]:
        return {self.var, C} if self.needs_constant else {self.var}


@dataclass
class Built:
    """問題の型が作る1問分の材料。"""

    f: sp.Expr  # 問題の中心となる式（微分・積分する関数など）
    wrongs: list[tuple[str, sp.Expr]]  # (誤答パターンID, その間違いをしたときの答え)
    steps: list[str]  # 解き方の手順（$...$ は LaTeX）
    latex: str | None = None  # 問題の表示。省略時は f(x) = ... の形。文章題で式がなければ ""
    answer: sp.Expr | None = None  # 正解。省略時は単元の solve で求める
    prompt: str | None = None  # 問題文。省略時は単元の既定
    answer_prefix: str | None = None  # 解答欄の左の表示。省略時は単元の既定
    meta: dict = field(default_factory=dict)  # テストでの検証用（定積分の区間、極限の行き先など）


@dataclass(frozen=True)
class ProblemType:
    id: str
    unit: str
    name: str
    description: str
    build: Callable[[random.Random], Built]


@dataclass
class Problem:
    problem_id: str
    type_id: str
    unit: Unit
    f: sp.Expr
    answer: sp.Expr
    wrongs: list[tuple[str, sp.Expr]]
    latex: str  # 問題の表示
    prompt: str
    answer_prefix: str
    answer_latex: str  # 正解の表示
    steps: list[str]
    meta: dict


def to_latex(expr: sp.Expr) -> str:
    return sp.latex(expr, ln_notation=True)


def tidy(expr: sp.Expr) -> sp.Expr:
    """答えを読みやすい形にする。

    simplify は sin x + cos x を √2 cos(x - π/4) にするなど、教科書と違う形にすることがあるため、
    π を新たに持ち込まない候補のうち最も短いものを選ぶ。
    """
    if expr.has(N):  # 数列の答え。和の公式（2次以上）は n(n+1) のように因数分解した形が見やすい
        if expr.is_polynomial(N):
            return sp.factor(expr) if sp.degree(expr, N) >= 2 else sp.expand(expr)
        return expr
    if not expr.has(X):  # 定積分・極限などの答え（定数）。ln 16 は 4 ln 2 の形にする
        return sp.expand_log(sp.simplify(expr), force=True)
    if expr.is_polynomial(X):  # 多項式は x でくくらず、展開した形にする
        return sp.expand(expr)
    candidates = [expr, sp.factor_terms(expr), sp.factor_terms(sp.together(expr)), sp.simplify(expr)]
    if not expr.has(sp.pi):
        candidates = [c for c in candidates if not c.has(sp.pi)]
    return min(candidates, key=sp.count_ops)


def nonzero(rng: random.Random, lo: int, hi: int) -> int:
    return rng.choice([n for n in range(lo, hi + 1) if n != 0])


# 合成・積で使う基本関数: 名前 → (g(t), g'(t))
T = sp.Symbol("t")
BASIC_FUNCS = {
    "sin": (sp.sin(T), sp.cos(T)),
    "cos": (sp.cos(T), -sp.sin(T)),
    "exp": (sp.exp(T), sp.exp(T)),
    "log": (sp.log(T), 1 / T),
}


def apply_func(name: str, arg: sp.Expr) -> tuple[sp.Expr, sp.Expr]:
    """基本関数 name に arg を入れた式と、その外側の微分 g'(arg) を返す。"""
    g, dg = BASIC_FUNCS[name]
    return g.subs(T, arg), dg.subs(T, arg)
