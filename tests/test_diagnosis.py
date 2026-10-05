import pytest
import sympy as sp

from drill.checker import X, parse_answer
from drill.diagnosis import diagnose
from drill.templates import PROBLEM_TYPES, generate


@pytest.mark.parametrize("type_id", PROBLEM_TYPES)
def test_each_wrong_answer_is_diagnosed(type_id):
    for seed in range(20):
        p = generate(type_id, seed)
        assert diagnose(p, p.answer).correct
        for mid, wrong in p.wrongs:
            d = diagnose(p, wrong)
            assert not d.correct
            assert d.misconception is not None and d.misconception.id == mid


def test_unclassified_mistake():
    p = generate("power", 0)
    d = diagnose(p, p.answer + 1)
    assert not d.correct and d.misconception is None


def test_typed_answer_in_other_form_is_correct():
    # 正解を展開した別の形で入力しても正解になる
    p = generate("product", 1)  # x ln x
    assert p.f == X * sp.log(X)
    assert diagnose(p, parse_answer("ln x + 1")).correct
    assert diagnose(p, parse_answer("1/x")).misconception.id == "product_naive"
