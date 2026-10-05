"""利用者の解答を正解・誤答ルールと照合する。"""

from dataclasses import dataclass

import sympy as sp

from .checker import equivalent
from .templates import MISCONCEPTIONS, Misconception, Problem


@dataclass
class Diagnosis:
    correct: bool
    misconception: Misconception | None  # 不正解で、どの誤答ルールにも一致しなければ None


def diagnose(problem: Problem, user_expr: sp.Expr) -> Diagnosis:
    if equivalent(user_expr, problem.answer):
        return Diagnosis(correct=True, misconception=None)
    for mid, wrong in problem.wrongs:
        if equivalent(user_expr, wrong):
            return Diagnosis(correct=False, misconception=MISCONCEPTIONS[mid])
    return Diagnosis(correct=False, misconception=None)
