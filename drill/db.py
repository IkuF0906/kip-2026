"""解答履歴と、型ごとの復習状態を SQLite に保存する。"""

import sqlite3
import threading
from collections import Counter
from datetime import datetime

from . import scheduler
from .scheduler import TypeState

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    type_id TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    correct INTEGER NOT NULL,
    misconception_id TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS type_state (
    type_id TEXT PRIMARY KEY,
    box INTEGER NOT NULL,
    due_at TEXT,
    attempts INTEGER NOT NULL,
    correct INTEGER NOT NULL
);
"""


class Store:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # FastAPI の同期エンドポイントは複数スレッドから呼ばれるため直列化する
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(_SCHEMA)

    def states(self, type_ids: list[str]) -> list[TypeState]:
        """指定した型の状態を返す。記録のない型は未学習の状態になる。"""
        with self._lock:
            rows = {r["type_id"]: r for r in self._conn.execute("SELECT * FROM type_state")}
        result = []
        for tid in type_ids:
            r = rows.get(tid)
            if r is None:
                result.append(TypeState(tid))
            else:
                due = datetime.fromisoformat(r["due_at"]) if r["due_at"] else None
                result.append(TypeState(tid, r["box"], due, r["attempts"], r["correct"]))
        return result

    def record(
        self,
        problem_id: str,
        type_id: str,
        answer_text: str,
        correct: bool,
        misconception_id: str | None,
        now: datetime,
    ) -> TypeState:
        [state] = self.states([type_id])
        new = scheduler.update(state, correct, now)
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO attempts (problem_id, type_id, answer_text, correct, misconception_id, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (problem_id, type_id, answer_text, int(correct), misconception_id, now.isoformat()),
            )
            self._conn.execute(
                "INSERT OR REPLACE INTO type_state (type_id, box, due_at, attempts, correct) VALUES (?, ?, ?, ?, ?)",
                (type_id, new.box, new.due_at.isoformat(), new.attempts, new.correct),
            )
        return new

    def misconception_counts(self) -> dict[str, Counter]:
        """型ごとの、診断された誤答ルールの回数。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT type_id, misconception_id FROM attempts WHERE correct = 0"
            ).fetchall()
        counts: dict[str, Counter] = {}
        for r in rows:
            counts.setdefault(r["type_id"], Counter())[r["misconception_id"]] += 1
        return counts
