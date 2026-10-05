"""全ての型について、多数のシードで問題・正解・誤答が矛盾しないことを確かめる。"""

import pytest
import sympy as sp

from drill.checker import X, equivalent
from drill.templates import MISCONCEPTIONS, PROBLEM_TYPES, from_id, generate

SEEDS = range(40)


@pytest.mark.parametrize("type_id", PROBLEM_TYPES)
def test_generated_problems_are_consistent(type_id):
    for seed in SEEDS:
        p = generate(type_id, seed)
        assert p.problem_id == f"{type_id}-{seed}"
        assert equivalent(p.answer, sp.diff(p.f, X))
        assert not equivalent(p.answer, sp.Integer(0)), "f が定数になっている"
        assert p.wrongs, "診断に使える誤答が1つもない"
        for mid, wrong in p.wrongs:
            assert mid in MISCONCEPTIONS
            assert not equivalent(wrong, p.answer)
        for i, (_, a) in enumerate(p.wrongs):
            for _, b in p.wrongs[i + 1 :]:
                assert not equivalent(a, b)


@pytest.mark.parametrize("type_id", PROBLEM_TYPES)
def test_same_seed_gives_same_problem(type_id):
    assert generate(type_id, 7).f == generate(type_id, 7).f


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
