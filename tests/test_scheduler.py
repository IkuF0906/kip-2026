from datetime import datetime, timedelta

from drill.scheduler import MAX_BOX, TypeState, pick_next, update

NOW = datetime(2026, 10, 5, 12, 0)


def test_correct_moves_box_up_and_delays():
    s = update(TypeState("a"), True, NOW)
    assert (s.box, s.due_at, s.attempts, s.correct) == (1, NOW + timedelta(days=1), 1, 1)
    s = update(s, True, NOW)
    assert (s.box, s.due_at) == (2, NOW + timedelta(days=2))


def test_box_is_capped():
    s = TypeState("a", box=MAX_BOX, due_at=NOW, attempts=5, correct=5)
    assert update(s, True, NOW).box == MAX_BOX


def test_wrong_resets_to_box0_due_now():
    s = TypeState("a", box=3, due_at=NOW, attempts=3, correct=3)
    s = update(s, False, NOW)
    assert (s.box, s.due_at, s.attempts, s.correct) == (0, NOW, 4, 3)


def test_pick_prefers_overdue_then_unseen():
    overdue = TypeState("old", box=1, due_at=NOW - timedelta(days=2), attempts=1, correct=1)
    recent = TypeState("recent", box=0, due_at=NOW - timedelta(hours=1), attempts=1, correct=0)
    unseen = TypeState("new")
    future = TypeState("future", box=2, due_at=NOW + timedelta(days=1), attempts=2, correct=2)
    assert pick_next([future, unseen, recent, overdue], NOW).type_id == "old"
    assert pick_next([future, unseen], NOW).type_id == "new"


def test_pick_lowest_accuracy_when_nothing_due():
    good = TypeState("good", box=2, due_at=NOW + timedelta(days=1), attempts=4, correct=4)
    weak = TypeState("weak", box=1, due_at=NOW + timedelta(days=2), attempts=4, correct=1)
    assert pick_next([good, weak], NOW).type_id == "weak"
