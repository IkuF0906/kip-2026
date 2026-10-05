"""レポート用の評価。問題の型ごとに、誤答診断がどれだけ働くかと処理時間を測る。

実行: python -m scripts.evaluate [問題数]
結果は Markdown の表として標準出力に出す。
"""

import statistics
import sys
import time
from collections import Counter

from drill.diagnosis import diagnose
from drill.templates import MISCONCEPTIONS, PROBLEM_TYPES, UNITS, generate


def evaluate_type(type_id: str, n: int) -> dict:
    gen_times, diag_times = [], []
    wrong_counts = []
    rules = Counter()
    correct_ok = diag_ok = diag_total = 0
    for seed in range(n):
        t0 = time.perf_counter()
        p = generate(type_id, seed)
        gen_times.append(time.perf_counter() - t0)
        wrong_counts.append(len(p.wrongs))

        t0 = time.perf_counter()
        correct_ok += diagnose(p, p.answer).correct
        diag_times.append(time.perf_counter() - t0)

        for mid, wrong in p.wrongs:
            rules[mid] += 1
            d = diagnose(p, wrong)
            diag_total += 1
            diag_ok += (not d.correct) and d.misconception is not None and d.misconception.id == mid
    return {
        "type": PROBLEM_TYPES[type_id].name,
        "correct_rate": correct_ok / n,
        "diag_rate": diag_ok / diag_total if diag_total else 0.0,
        "avg_wrongs": statistics.mean(wrong_counts),
        "min_wrongs": min(wrong_counts),
        "rules": rules,
        "gen_ms": statistics.mean(gen_times) * 1000,
        "diag_ms": statistics.mean(diag_times) * 1000,
    }


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    print(f"各型 {n} 問（シード 0〜{n - 1}）で評価\n")
    print("| 単元 | 型 | 正解の判定 | 誤答の診断 | 診断できる誤答数（平均/最小） | 生成 (ms) | 判定 (ms) |")
    print("|---|---|---|---|---|---|---|")
    all_rules = Counter()
    for tid, t in PROBLEM_TYPES.items():
        r = evaluate_type(tid, n)
        all_rules.update(r["rules"])
        print(
            f"| {UNITS[t.unit].name} | {r['type']} | {r['correct_rate']:.0%} | {r['diag_rate']:.0%} "
            f"| {r['avg_wrongs']:.2f} / {r['min_wrongs']} | {r['gen_ms']:.1f} | {r['diag_ms']:.1f} |"
        )
    print("\n誤答パターンごとの、診断候補として使えた問題数（全型の合計）\n")
    print("| 誤答パターン | 問題数 |")
    print("|---|---|")
    for mid, m in MISCONCEPTIONS.items():
        print(f"| {m.label} | {all_rules[mid]} |")


if __name__ == "__main__":
    main()
