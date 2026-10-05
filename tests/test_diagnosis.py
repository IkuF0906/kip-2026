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


def test_integral_ignores_constant_and_reminds_c():
    # int_power-0 は ∫(3x^5 + 4x^4 + 9)dx = x^6/2 + 4x^5/5 + 9x + C
    p = generate("int_power", 0)
    with_c = diagnose(p, parse_answer("x^6/2 + 4x^5/5 + 9x + C"))
    other_const = diagnose(p, parse_answer("x^6/2 + 4x^5/5 + 9x + 7"))
    without_c = diagnose(p, parse_answer("x^6/2 + 4x^5/5 + 9x"))
    assert with_c.correct and with_c.note is None
    assert other_const.correct
    assert without_c.correct and "C" in without_c.note
    # 微分してしまった答え
    assert diagnose(p, parse_answer("15x^4 + 16x^3")).misconception.id == "int_differentiated"


def test_derivative_has_no_constant_note():
    p = generate("power", 0)
    assert diagnose(p, p.answer).note is None


def test_limit_infinity_answer():
    seed = next(s for s in range(100) if generate("lim_rational", s).answer == sp.oo)
    p = generate("lim_rational", seed)
    assert diagnose(p, parse_answer("oo")).correct
    assert not diagnose(p, parse_answer("-oo")).correct
