"""解答の読み取りと答え合わせ。sandbox のワーカープロセスで動かすので、結果は辞書で返す。"""

from .checker import AnswerParseError, parse_answer
from .diagnosis import diagnose
from .templates import from_id, to_latex


def check(problem_id: str, text: str) -> dict:
    """問題が見つからなければ KeyError、解答を読み取れなければ AnswerParseError。"""
    p = from_id(problem_id)
    user_expr = parse_answer(text)
    extra = user_expr.free_symbols - p.unit.allowed_symbols()
    if extra:
        names = "、".join(sorted(str(s) for s in extra))
        raise AnswerParseError(f"この問題では {names} は使いません。{p.unit.var} の式か数で答えてください")
    d = diagnose(p, user_expr)
    return {
        "problem_id": p.problem_id,
        "type_id": p.type_id,
        "correct": d.correct,
        "misconception_id": d.misconception.id if d.misconception else None,
        "note": d.note,
        "user_latex": to_latex(user_expr),
        "answer_latex": p.answer_latex,
        "steps": p.steps,
    }


def preview(text: str) -> str:
    """テキストの解答がどの式として読み取られるか（LaTeX）。"""
    return to_latex(parse_answer(text))


TASKS = {"check": check, "preview": preview}
