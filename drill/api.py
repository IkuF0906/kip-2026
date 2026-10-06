"""Web API と画面の配信。

起動: uvicorn drill.api:app --reload
保存先の DB は環境変数 DRILL_DB で変えられる（既定は drill.db）。
利用者は Cookie の ID で区別する。DRILL_ADOPT_LOCAL=1 で起動すると、Cookie のない
ブラウザに、利用者を区別する前の履歴（ID は local）を引き継がせる。
"""

import os
import random
import re
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import scheduler
from .checker import AnswerParseError, parse_answer
from .db import LOCAL_USER, Store
from .diagnosis import diagnose
from .templates import MISCONCEPTIONS, PROBLEM_TYPES, UNITS, Problem, from_id, generate, to_latex

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
USER_COOKIE = "drill_uid"
_USER_ID = re.compile(rf"[0-9a-f]{{32}}|{LOCAL_USER}")


class AnswerRequest(BaseModel):
    problem_id: str
    answer: str


def _problem_json(p: Problem) -> dict:
    return {
        "problem_id": p.problem_id,
        "type_id": p.type_id,
        "type_name": PROBLEM_TYPES[p.type_id].name,
        "unit_id": p.unit.id,
        "unit_name": p.unit.name,
        "prompt": p.prompt,
        "latex": p.latex,
        "answer_prefix": p.answer_prefix,
        "variable": str(p.unit.var),
    }


def _new_problem(type_id: str) -> Problem:
    return generate(type_id, random.randrange(10**9))


def _type_ids(unit: str | None) -> list[str]:
    """単元の型 ID の一覧（unit が None なら全単元）。"""
    if unit is not None and unit not in UNITS:
        raise HTTPException(404, "単元が見つかりません")
    return [tid for tid, t in PROBLEM_TYPES.items() if unit is None or t.unit == unit]


def create_app(db_path: str, now=datetime.now, adopt_local: bool = False) -> FastAPI:
    """now は現在時刻を返す関数（テストで時刻を固定するため差し替え可能）。
    adopt_local が真なら、Cookie のない利用者を LOCAL_USER とする。"""
    app = FastAPI(title="数学ドリル")
    store = Store(db_path)

    def user_id(request: Request, response: Response) -> str:
        """Cookie の利用者 ID。なければ新しく発行して Cookie に入れる。"""
        uid = request.cookies.get(USER_COOKIE, "")
        if _USER_ID.fullmatch(uid):
            return uid
        uid = LOCAL_USER if adopt_local else uuid.uuid4().hex
        response.set_cookie(USER_COOKIE, uid, max_age=400 * 24 * 3600, httponly=True, samesite="lax")
        return uid

    @app.get("/api/units")
    def list_units():
        return [{"id": u.id, "name": u.name} for u in UNITS.values()]

    @app.get("/api/types")
    def list_types(unit: str | None = None):
        return [
            {"id": tid, "unit": PROBLEM_TYPES[tid].unit, "name": PROBLEM_TYPES[tid].name, "description": PROBLEM_TYPES[tid].description}
            for tid in _type_ids(unit)
        ]

    @app.get("/api/problem")
    def problem(type: str | None = None, unit: str | None = None):
        """type を指定するとその型、省略すると unit（省略時は全単元）の中からランダムに出題する。"""
        if type is None:
            type = random.choice(_type_ids(unit))
        if type not in PROBLEM_TYPES:
            raise HTTPException(404, "問題の型が見つかりません")
        return _problem_json(_new_problem(type))

    @app.get("/api/review")
    def review(unit: str | None = None, uid: str = Depends(user_id)):
        state = scheduler.pick_next(store.states(uid, _type_ids(unit)), now())
        return _problem_json(_new_problem(state.type_id))

    @app.get("/api/preview")
    def preview(text: str):
        """テキスト入力の解答がどの式として読み取られるかを返す（答え合わせ前の確認用）。"""
        try:
            return {"latex": to_latex(parse_answer(text))}
        except AnswerParseError as exc:
            raise HTTPException(400, str(exc))

    @app.post("/api/answer")
    def answer(req: AnswerRequest, uid: str = Depends(user_id)):
        try:
            p = from_id(req.problem_id)
        except KeyError:
            raise HTTPException(404, "問題が見つかりません")
        try:
            user_expr = parse_answer(req.answer)
        except AnswerParseError as exc:
            raise HTTPException(400, str(exc))
        extra = user_expr.free_symbols - p.unit.allowed_symbols()
        if extra:
            names = "、".join(sorted(str(s) for s in extra))
            raise HTTPException(400, f"この問題では {names} は使いません。{p.unit.var} の式か数で答えてください")
        d = diagnose(p, user_expr)
        mc = d.misconception
        state = store.record(uid, p.problem_id, p.type_id, req.answer, d.correct, mc.id if mc else None, now())
        return {
            "correct": d.correct,
            "user_latex": to_latex(user_expr),
            "answer_latex": p.answer_latex,
            "misconception": {"id": mc.id, "label": mc.label, "explanation": mc.explanation} if mc else None,
            "note": d.note,
            "steps": p.steps,
            "next_due": state.due_at.isoformat(),
        }

    @app.get("/api/stats")
    def stats(uid: str = Depends(user_id)):
        counts = store.misconception_counts(uid)
        result = []
        for s in store.states(uid, list(PROBLEM_TYPES)):
            t = PROBLEM_TYPES[s.type_id]
            mistakes = [
                {
                    "id": mid,
                    "label": MISCONCEPTIONS[mid].label if mid else "未分類の誤り",
                    "count": n,
                }
                for mid, n in counts.get(s.type_id, Counter()).most_common()
            ]
            result.append(
                {
                    "type_id": s.type_id,
                    "type_name": t.name,
                    "unit_id": t.unit,
                    "unit_name": UNITS[t.unit].name,
                    "attempts": s.attempts,
                    "correct": s.correct,
                    "accuracy": s.accuracy,
                    "box": s.box,
                    "due_at": s.due_at.isoformat() if s.due_at else None,
                    "mistakes": mistakes,
                }
            )
        return result

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app(os.environ.get("DRILL_DB", "drill.db"), adopt_local=os.environ.get("DRILL_ADOPT_LOCAL") == "1")
