from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from drill.api import create_app

NOW = datetime(2026, 10, 5, 12, 0)


@pytest.fixture
def clock():
    return {"now": NOW}


@pytest.fixture
def client(tmp_path, clock):
    return TestClient(create_app(str(tmp_path / "test.db"), now=lambda: clock["now"]))


def answer(client, problem_id, text):
    return client.post("/api/answer", json={"problem_id": problem_id, "answer": text})


def test_index_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "数学ドリル" in res.text


def test_problem_for_type(client):
    res = client.get("/api/problem", params={"type": "chain"})
    assert res.status_code == 200
    body = res.json()
    assert body["type_id"] == "chain"
    assert body["problem_id"].startswith("chain-")


def test_unknown_type_is_404(client):
    assert client.get("/api/problem", params={"type": "nope"}).status_code == 404


def test_correct_answer(client):
    res = answer(client, "power-0", "-15x^4 + 15x^2")
    body = res.json()
    assert body["correct"] is True
    assert body["misconception"] is None
    assert body["next_due"] == (NOW + timedelta(days=1)).isoformat()


def test_wrong_answer_is_diagnosed(client):
    # power-0 は -3x^5 + 5x^3 + 9。指数を前に出し忘れると -3x^4 + 5x^2
    body = answer(client, "power-0", "-3x^4 + 5x^2").json()
    assert body["correct"] is False
    assert body["misconception"]["id"] == "power_no_coeff"
    assert body["next_due"] == NOW.isoformat()


def test_parse_error_is_400(client):
    res = answer(client, "power-0", "(x+")
    assert res.status_code == 400
    assert res.json()["detail"]


def test_unknown_problem_is_404(client):
    assert answer(client, "nope-1", "x").status_code == 404


def test_review_picks_failed_type_first(client, clock):
    answer(client, "power-0", "-15x^4 + 15x^2")  # 正解 → 1日後
    answer(client, "trig-0", "0")  # 不正解 → すぐ
    clock["now"] = NOW + timedelta(minutes=1)
    assert client.get("/api/review").json()["type_id"] == "trig"


def test_stats(client):
    answer(client, "power-0", "-3x^4 + 5x^2")
    answer(client, "power-1", "1")
    answer(client, "power-2", "12x^3 + 10x")
    power = next(s for s in client.get("/api/stats").json() if s["type_id"] == "power")
    assert (power["attempts"], power["correct"]) == (3, 1)
    labels = {m["label"] for m in power["mistakes"]}
    assert "未分類の誤り" in labels
    assert any("前に出し忘れ" in label for label in labels)


def test_units_and_types(client):
    units = [u["id"] for u in client.get("/api/units").json()]
    assert units == ["derivative", "integral", "definite", "limit", "application"]
    types = client.get("/api/types", params={"unit": "limit"}).json()
    assert types and all(t["unit"] == "limit" for t in types)
    assert client.get("/api/types", params={"unit": "nope"}).status_code == 404


def test_problem_for_unit(client):
    for _ in range(5):
        body = client.get("/api/problem", params={"unit": "definite"}).json()
        assert body["unit_id"] == "definite"
        assert body["prompt"] and body["answer_prefix"]


def test_review_within_unit(client, clock):
    answer(client, "power-0", "0")  # 微分で不正解 → すぐ復習
    clock["now"] = NOW + timedelta(minutes=1)
    assert client.get("/api/review").json()["type_id"] == "power"
    assert client.get("/api/review", params={"unit": "integral"}).json()["unit_id"] == "integral"


def test_integral_answer_with_note(client):
    body = answer(client, "int_power-0", "x^6/2 + 4x^5/5 + 9x").json()
    assert body["correct"] is True
    assert "C" in body["note"]
    assert body["answer_latex"].endswith("+ C")


def test_stats_has_unit(client):
    s = next(s for s in client.get("/api/stats").json() if s["type_id"] == "lim_e")
    assert (s["unit_id"], s["unit_name"]) == ("limit", "極限")


def test_preview(client):
    assert client.get("/api/preview", params={"text": "2xsin(x)"}).json()["latex"] == r"2 x \sin{\left(x \right)}"
    assert client.get("/api/preview", params={"text": "(x+"}).status_code == 400
