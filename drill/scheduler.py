"""問題の型ごとの復習スケジュール（ライトナー方式）。

箱 0 は「未学習・要再練習」で、すぐに出題対象になる。
正解すると箱が1つ上がって次回の出題が先に延び、不正解なら箱 0 に戻る。
"""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

INTERVAL_DAYS = {0: 0, 1: 1, 2: 2, 3: 4, 4: 8}
MAX_BOX = max(INTERVAL_DAYS)


@dataclass(frozen=True)
class TypeState:
    type_id: str
    box: int = 0
    due_at: datetime | None = None  # None は未学習
    attempts: int = 0
    correct: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.attempts if self.attempts else 0.0

    def is_due(self, now: datetime) -> bool:
        return self.due_at is None or self.due_at <= now


def update(state: TypeState, correct: bool, now: datetime) -> TypeState:
    box = min(state.box + 1, MAX_BOX) if correct else 0
    return replace(
        state,
        box=box,
        due_at=now + timedelta(days=INTERVAL_DAYS[box]),
        attempts=state.attempts + 1,
        correct=state.correct + int(correct),
    )


def pick_next(states: list[TypeState], now: datetime) -> TypeState:
    """次に復習する型を選ぶ。

    1. 期限が来た学習済みの型（期限が古い順、同じなら正答率が低い順）
    2. 未学習の型
    3. 期限前なら、正答率が低い順・期限が近い順
    """
    if not states:
        raise ValueError("states is empty")
    due_seen = [s for s in states if s.due_at is not None and s.due_at <= now]
    if due_seen:
        return min(due_seen, key=lambda s: (s.due_at, s.accuracy))
    unseen = [s for s in states if s.due_at is None]
    if unseen:
        return unseen[0]
    return min(states, key=lambda s: (s.accuracy, s.due_at))
