"""Web API と画面の配信。

起動: uvicorn drill.api:app --reload
保存先の DB は環境変数 DRILL_DB で変えられる（既定は drill.db）。
"""

import os
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import scheduler
from .checker import AnswerParseError, parse_answer
from .db import Store
from .diagnosis import diagnose
from .templates import MISCONCEPTIONS, PROBLEM_TYPES, Problem, from_id, generate, tidy, to_latex

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class AnswerRequest(BaseModel):
    problem_id: str
    answer: str


def _problem_json(p: Problem) -> dict:
    return {
        "problem_id": p.problem_id,
        "type_id": p.type_id,
        "type_name": PROBLEM_TYPES[p.type_id].name,
        "latex": p.latex,
    }


def _new_problem(type_id: str) -> Problem:
    return generate(type_id, random.randrange(10**9))


def create_app(db_path: str, now=datetime.now) -> FastAPI:
    """now は現在時刻を返す関数（テストで時刻を固定するため差し替え可能）。"""
    app = FastAPI(title="微分ドリル")
    store = Store(db_path)

    @app.get("/api/types")
    def list_types():
        return [{"id": t.id, "name": t.name, "description": t.description} for t in PROBLEM_TYPES.values()]

    @app.get("/api/problem")
    def problem(type: str | None = None):
        if type is None:
            type = random.choice(list(PROBLEM_TYPES))
        if type not in PROBLEM_TYPES:
            raise HTTPException(404, "問題の型が見つかりません")
        return _problem_json(_new_problem(type))

    @app.get("/api/review")
    def review():
        state = scheduler.pick_next(store.states(list(PROBLEM_TYPES)), now())
        return _problem_json(_new_problem(state.type_id))

    @app.post("/api/answer")
    def answer(req: AnswerRequest):
        try:
            p = from_id(req.problem_id)
        except KeyError:
            raise HTTPException(404, "問題が見つかりません")
        try:
            user_expr = parse_answer(req.answer)
        except AnswerParseError as exc:
            raise HTTPException(400, str(exc))
        d = diagnose(p, user_expr)
        mc = d.misconception
        state = store.record(p.problem_id, p.type_id, req.answer, d.correct, mc.id if mc else None, now())
        return {
            "correct": d.correct,
            "user_latex": to_latex(user_expr),
            "answer_latex": to_latex(tidy(p.answer)),
            "misconception": {"id": mc.id, "label": mc.label, "explanation": mc.explanation} if mc else None,
            "steps": p.steps,
            "next_due": state.due_at.isoformat(),
        }

    @app.get("/api/stats")
    def stats():
        counts = store.misconception_counts()
        result = []
        for s in store.states(list(PROBLEM_TYPES)):
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
                    "type_name": PROBLEM_TYPES[s.type_id].name,
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


app = create_app(os.environ.get("DRILL_DB", "drill.db"))
