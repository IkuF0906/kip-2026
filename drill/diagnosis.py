"""利用者の解答を正解・誤答パターンと照合する。"""

from dataclasses import dataclass

import sympy as sp

from .checker import C
from .templates import MISCONCEPTIONS, Misconception, Problem


@dataclass
class Diagnosis:
    correct: bool
    misconception: Misconception | None  # 不正解で、どの誤答パターンにも一致しなければ None
    note: str | None = None  # 正誤とは別の注意（積分定数の書き忘れなど）


def diagnose(problem: Problem, user_expr: sp.Expr) -> Diagnosis:
    same = problem.unit.same
    if same(user_expr, problem.answer):
        note = None
        if problem.unit.needs_constant and not user_expr.has(C):
            note = r"積分定数 $C$ が書かれていません。不定積分では $+C$ を付けましょう。"
        return Diagnosis(correct=True, misconception=None, note=note)
    for mid, wrong in problem.wrongs:
        if same(user_expr, wrong):
            return Diagnosis(correct=False, misconception=MISCONCEPTIONS[mid])
    return Diagnosis(correct=False, misconception=None)
