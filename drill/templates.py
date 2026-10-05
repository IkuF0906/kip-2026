"""全単元の問題の型・誤答パターンをまとめ、問題を生成する。

各型は乱数から問題・正解・誤答の式・解き方の手順を作る。
誤答の式は「この間違いをするとこの答えになる」を表し、診断で利用者の解答と照合する。
問題IDは "<型ID>-<シード>" で、同じIDからは常に同じ問題が再生成される。
"""

import random

import sympy as sp

from .checker import X, equivalent
from .core import Misconception, Problem, ProblemType, Unit, tidy, to_latex  # noqa: F401（他のモジュール向けに再公開）
from .units import application, definite, derivative, integral, limit, probability, sequence

_UNIT_MODULES = [derivative, integral, definite, limit, application, sequence, probability]

UNITS: dict[str, Unit] = {m.UNIT.id: m.UNIT for m in _UNIT_MODULES}
MISCONCEPTIONS: dict[str, Misconception] = {mc.id: mc for m in _UNIT_MODULES for mc in m.MISCONCEPTIONS}
PROBLEM_TYPES: dict[str, ProblemType] = {t.id: t for m in _UNIT_MODULES for t in m.TYPES}


def _drop_collisions(unit: Unit, answer: sp.Expr, wrongs: list[tuple[str, sp.Expr]]) -> list[tuple[str, sp.Expr]]:
    """正解と同じになる誤答、先に出た誤答と同じになる誤答を除く。

    例えば x^1 の積では「指数を減らし忘れ」が正解と一致するため、診断に使えない。
    """
    kept: list[tuple[str, sp.Expr]] = []
    for mid, expr in wrongs:
        if unit.same(expr, answer):
            continue
        if any(unit.same(expr, other) for _, other in kept):
            continue
        kept.append((mid, expr))
    return kept


def generate(type_id: str, seed: int) -> Problem:
    ptype = PROBLEM_TYPES[type_id]
    unit = UNITS[ptype.unit]
    rng = random.Random(f"{type_id}-{seed}")
    # 係数の組み合わせによっては f が定数になったり（例: (2x+4)/(x+2) の微分）、
    # 誤答が全て正解と一致して診断できなくなったりするので作り直す
    for _ in range(10):
        b = ptype.build(rng)
        answer = b.answer if b.answer is not None else unit.solve(b.f)
        wrongs = _drop_collisions(unit, answer, b.wrongs)
        trivial = unit.solve is not None and b.f.has(X) and not answer.has(X) and equivalent(answer, sp.Integer(0))
        if wrongs and not trivial:
            break
    prefix = b.answer_prefix or unit.answer_prefix
    answer_latex = to_latex(tidy(answer)) + unit.answer_suffix
    return Problem(
        problem_id=f"{type_id}-{seed}",
        type_id=type_id,
        unit=unit,
        f=b.f,
        answer=answer,
        wrongs=wrongs,
        latex=b.latex if b.latex is not None else f"f(x) = {to_latex(b.f)}",
        prompt=b.prompt or unit.prompt,
        answer_prefix=prefix,
        answer_latex=answer_latex,
        steps=b.steps + [f"${prefix} {answer_latex}$"],
        meta=b.meta,
    )


def from_id(problem_id: str) -> Problem:
    type_id, _, seed = problem_id.rpartition("-")
    if type_id not in PROBLEM_TYPES or not seed.isdigit():
        raise KeyError(problem_id)
    return generate(type_id, int(seed))
