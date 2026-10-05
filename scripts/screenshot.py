"""画面の自動確認。アプリをブラウザ（Chrome）で開き、主な画面のスクリーンショットを撮る。

実行: python -m scripts.screenshot [出力先フォルダ]（既定は screenshots/）
普段の解答履歴（drill.db）に確認用の解答が混ざらないよう、一時的な DB を使う専用のサーバーを
別のポートで起動して確認し、終わったら止める。
コンソールのエラーと、読み込みに失敗したリソースも表示する。
"""

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

from drill.templates import from_id

PORT = 8765


def start_server(db_path: str) -> subprocess.Popen:
    env = dict(os.environ, DRILL_DB=db_path)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "drill.api:app", "--port", str(PORT)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/api/types")
            return proc
        except OSError:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("確認用のサーバーが起動しませんでした")


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "screenshots")
    out.mkdir(parents=True, exist_ok=True)
    # Windows では止めたサーバーが DB をしばらく開いたままのことがあるので、消せなくても止まらないようにする
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        server = start_server(str(Path(tmp) / "screenshot.db"))
        try:
            take_screenshots(out, f"http://localhost:{PORT}/")
        finally:
            server.terminate()
            server.wait()


def text_input_on(page) -> bool:
    return page.evaluate("useText")


def take_screenshots(out: Path, url: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1000, "height": 900})
        problems = []
        page.on("pageerror", lambda e: problems.append(f"JS エラー: {e}"))
        page.on("console", lambda m: m.type == "error" and problems.append(f"console: {m.text}"))
        page.on("response", lambda r: r.status >= 400 and problems.append(f"{r.status} {r.url}"))

        page.goto(url)
        page.select_option("#type-select", "power")
        page.wait_for_selector("#problem .katex", timeout=15000)
        page.wait_for_timeout(500)
        page.screenshot(path=out / "1_problem.png", full_page=True)

        # 手書き: ペンで線を引き、消しゴムで一部を消して、消しゴムの円が出ている状態を撮る
        c = page.locator("#note-canvas").bounding_box()
        page.mouse.move(c["x"] + 60, c["y"] + 100)
        page.mouse.down()
        for i in range(40):
            page.mouse.move(c["x"] + 60 + i * 10, c["y"] + 100 + (i % 5) * 6)
        page.mouse.up()
        page.click('.note-tool[data-tool="eraser"]')
        page.mouse.move(c["x"] + 200, c["y"] + 100)
        page.mouse.down()
        page.mouse.move(c["x"] + 260, c["y"] + 110)
        page.mouse.up()
        page.mouse.move(c["x"] + 330, c["y"] + 105)
        page.wait_for_timeout(200)
        page.screenshot(path=out / "2_note.png", clip={"x": c["x"], "y": c["y"], "width": 600, "height": 220})

        # 途中式メモ
        page.click('.note-tab[data-note="memo"]')
        page.screenshot(path=out / "3_memo.png", full_page=True)
        page.click('.note-tab[data-note="draw"]')

        # キーで「x」とだけ入力して答え合わせ（不正解の例）
        page.click("#math-buttons button[title='変数 x']")
        page.click("#submit")
        page.wait_for_selector("#result:not([hidden])")
        page.wait_for_timeout(500)
        page.locator("#result").screenshot(path=out / "4_result.png")

        page.click("#open-guide")
        page.wait_for_timeout(300)
        page.screenshot(path=out / "5_guide.png")
        page.keyboard.press("Escape")

        # 単元ごとの問題（問題文・問題・解答欄の表示）
        page.click('.tab[data-tab="practice"]')
        units = page.eval_on_selector_all("#unit-select option", "os => os.map(o => o.value).filter(v => v)")
        for i, unit in enumerate(units, start=1):
            page.select_option("#unit-select", unit)
            page.wait_for_function("u => typeof current !== 'undefined' && current && current.unit_id === u", arg=unit)
            page.wait_for_timeout(300)
            card = page.locator("#problem-card").bounding_box()
            # ノートを除いた上部（問題）と下部（解答欄）を縦に並べたいので、カード全体を撮る
            page.screenshot(path=out / f"7_unit{i}_{unit}.png", clip={"x": card["x"], "y": card["y"], "width": card["width"], "height": 200})
            page.locator("#answer-prefix").screenshot(path=out / f"7_unit{i}_{unit}_prefix.png")

        # 極値の問題（解答欄の左に「極大値 =」などの日本語が出る）
        page.select_option("#unit-select", "application")
        page.wait_for_function("() => current.unit_id === 'application'")
        before = page.evaluate("current.problem_id")
        page.select_option("#type-select", "app_extremum")
        page.wait_for_function("id => current.problem_id !== id && current.type_id === 'app_extremum'", arg=before)
        page.wait_for_timeout(300)
        page.locator("#problem-card .answer-row").screenshot(path=out / "7_extremum_answer_row.png")

        # 文章題（式の欄がなく、問題文だけが出る）
        page.select_option("#unit-select", "probability")
        page.wait_for_function("() => current.unit_id === 'probability'")
        before = page.evaluate("current.problem_id")
        page.select_option("#type-select", "prob_conditional")
        page.wait_for_function("id => current.problem_id !== id && current.type_id === 'prob_conditional'", arg=before)
        page.wait_for_timeout(300)
        card = page.locator("#problem-card").bounding_box()
        page.screenshot(path=out / "9_word_problem.png", clip={"x": card["x"], "y": card["y"], "width": card["width"], "height": 200})

        # 数列：入力キーの x が n に変わり、n の式で答え合わせできる
        page.select_option("#unit-select", "sequence")
        page.wait_for_function("() => current.unit_id === 'sequence'")
        before = page.evaluate("current.problem_id")
        page.select_option("#type-select", "seq_recur")
        page.wait_for_function("id => current.problem_id !== id && current.type_id === 'seq_recur'", arg=before)
        page.locator("#math-buttons").screenshot(path=out / "10_sequence_keys.png")
        page.click("#math-buttons button[title='変数 n']")
        if not text_input_on(page):
            page.click("#toggle-input")
        answer = from_id(page.evaluate("current.problem_id")).answer
        page.fill("#answer-text", str(answer).replace("**", "^"))
        page.click("#submit")
        page.wait_for_selector("#result:not([hidden])")
        page.wait_for_timeout(300)
        page.screenshot(path=out / "10_sequence_result.png", full_page=True)
        if text_input_on(page):
            page.click("#toggle-input")

        # 不定積分で C を付けずに正解したときの注意
        page.select_option("#unit-select", "integral")
        page.wait_for_function("() => current.unit_id === 'integral'")
        before = page.evaluate("current.problem_id")
        page.select_option("#type-select", "int_power")
        # 型を選ぶと新しい問題が出るので、問題が切り替わるのを待つ
        page.wait_for_function("id => current.problem_id !== id && current.type_id === 'int_power'", arg=before)
        page.click("#toggle-input")
        answer = from_id(page.evaluate("current.problem_id")).answer  # C を付けない正解
        page.fill("#answer-text", str(answer))
        page.click("#submit")
        page.wait_for_selector("#result:not([hidden])")
        page.screenshot(path=out / "8_integral_result.png", full_page=True)

        page.click('.tab[data-tab="stats"]')
        page.wait_for_selector("#stats-body tr")
        page.screenshot(path=out / "6_stats.png", full_page=True)

        browser.close()

    print(f"スクリーンショットを {out}/ に保存しました")
    print("\n".join(problems) if problems else "エラーなし")


if __name__ == "__main__":
    main()
