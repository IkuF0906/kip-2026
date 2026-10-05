"""全ての型について、多数のシードで問題・正解・誤答が矛盾しないことを確かめる。

正解は、問題の型が作ったものとは別に、単元の定義から求め直して比べる。
"""

import pytest
import sympy as sp

from drill.checker import X, equivalent
from drill.templates import MISCONCEPTIONS, PROBLEM_TYPES, UNITS, from_id, generate

SEEDS = range(30)


def check_answer(p) -> None:
    """単元の定義に照らして、正解が正しいことを確かめる。"""
    unit = p.unit.id
    if unit == "derivative":
        assert equivalent(p.answer, sp.diff(p.f, X))
    elif unit == "integral":
        assert equivalent(sp.diff(p.answer, X), p.f)
    elif unit == "definite":
        assert equivalent(p.answer, sp.integrate(p.f, (X, p.meta["lo"], p.meta["hi"])))
    elif unit == "limit":
        to = p.meta["to"]
        expected = sp.limit(p.f, X, to)
        if to != sp.oo:  # x → a は左右から一致することも確かめる
            assert sp.limit(p.f, X, to, "-") == expected
        assert p.unit.same(p.answer, expected)
    elif p.type_id in ("app_tangent", "app_normal"):
        a = p.meta["a"]
        slope = sp.diff(p.answer, X)
        df_a = sp.diff(p.f, X).subs(X, a)
        assert p.answer.subs(X, a) == p.f.subs(X, a), "接点を通らない"
        assert slope == (df_a if p.type_id == "app_tangent" else -1 / df_a)
    elif p.type_id == "app_extremum":
        x0 = p.meta["x0"]
        df, d2f = sp.diff(p.f, X), sp.diff(p.f, X, 2)
        assert df.subs(X, x0) == 0
        assert (d2f.subs(X, x0) < 0) == (p.meta["kind"] == "極大値")
        assert p.answer == p.f.subs(X, x0)
    else:
        raise AssertionError(f"検証方法が決まっていない型: {p.type_id}")


@pytest.mark.parametrize("type_id", PROBLEM_TYPES)
def test_generated_problems_are_consistent(type_id):
    for seed in SEEDS:
        p = generate(type_id, seed)
        assert p.problem_id == f"{type_id}-{seed}"
        check_answer(p)
        assert p.wrongs, "診断に使える誤答が1つもない"
        same = p.unit.same
        for mid, wrong in p.wrongs:
            assert mid in MISCONCEPTIONS
            assert not same(wrong, p.answer)
        for i, (_, a) in enumerate(p.wrongs):
            for _, b in p.wrongs[i + 1 :]:
                assert not same(a, b)


def test_derivative_problems_are_not_constant():
    for type_id, t in PROBLEM_TYPES.items():
        if t.unit == "derivative":
            for seed in SEEDS:
                assert not equivalent(generate(type_id, seed).answer, sp.Integer(0))


@pytest.mark.parametrize("type_id", PROBLEM_TYPES)
def test_same_seed_gives_same_problem(type_id):
    assert generate(type_id, 7).f == generate(type_id, 7).f


def test_every_type_belongs_to_a_unit():
    assert {t.unit for t in PROBLEM_TYPES.values()} == set(UNITS)


def test_from_id_roundtrip():
    p = from_id("chain-123")
    assert p.type_id == "chain"
    assert p.f == generate("chain", 123).f


@pytest.mark.parametrize("bad", ["", "chain", "nope-1", "chain-abc", "chain--1"])
def test_from_id_rejects(bad):
    with pytest.raises(KeyError):
        from_id(bad)


def test_every_misconception_is_used():
    used = {mid for t in PROBLEM_TYPES for s in SEEDS for mid, _ in generate(t, s).wrongs}
    assert used == set(MISCONCEPTIONS)
