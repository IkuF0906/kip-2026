const $ = (id) => document.getElementById(id);

let mode = "practice"; // practice | review
let current = null; // 表示中の問題
let useText = false; // MathLive の代わりにテキスト入力を使う
// スマホ・タブレット（指で操作する端末）。入力欄に自動でフォーカスすると、キーボードが開いて画面が隠れる
const touchDevice = window.matchMedia("(pointer: coarse)").matches;

function renderMath(el) {
  renderMathInElement(el, {
    delimiters: [{ left: "$", right: "$", display: false }],
    throwOnError: false,
  });
}

function setMathText(el, text) {
  el.textContent = text;
  renderMath(el);
}

function setLatex(el, latex) {
  katex.render(latex, el, { throwOnError: false });
}

async function api(path, options) {
  const res = await fetch(path, options);
  // nginx が返すエラー（回数制限など）は JSON ではない
  const body = await res.json().catch(() => ({}));
  if (res.status === 429) throw new Error("短い時間に送った回数が多すぎます。少し待ってからもう一度送ってください");
  if (!res.ok) throw new Error(body.detail || "通信エラー");
  return body;
}

let units = []; // [{id, name}]

// 選んだ単元を覚えておく（使えない環境では毎回「微分」から始める）
function savedUnit() {
  try {
    return localStorage.getItem("unit") ?? "derivative";
  } catch {
    return "derivative";
  }
}

async function loadUnits() {
  units = await api("/api/units");
  const select = $("unit-select");
  for (const u of units) {
    const opt = document.createElement("option");
    opt.value = u.id;
    opt.textContent = u.name;
    select.appendChild(opt);
  }
  const saved = savedUnit();
  select.value = units.some((u) => u.id === saved) || saved === "" ? saved : "derivative";
}

// 問題の型の選択肢を、選んだ単元のものにする。「すべて」のときは単元ごとにまとめて並べる
async function loadTypes() {
  const unit = $("unit-select").value;
  const types = await api(`/api/types${unit ? `?unit=${unit}` : ""}`);
  const select = $("type-select");
  select.length = 1; // 先頭の「ランダム」だけ残す
  const groups = new Map();
  for (const t of types) {
    let parent = select;
    if (!unit) {
      if (!groups.has(t.unit)) {
        const group = document.createElement("optgroup");
        group.label = units.find((u) => u.id === t.unit).name;
        select.appendChild(group);
        groups.set(t.unit, group);
      }
      parent = groups.get(t.unit);
    }
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = t.name;
    parent.appendChild(opt);
  }
}

async function changeUnit() {
  try {
    localStorage.setItem("unit", $("unit-select").value);
  } catch {}
  await loadTypes();
  newProblem();
}

async function newProblem() {
  const unit = $("unit-select").value;
  const type = $("type-select").value;
  let path;
  if (mode === "review") path = `/api/review${unit ? `?unit=${unit}` : ""}`;
  else if (type) path = `/api/problem?type=${type}`;
  else path = `/api/problem${unit ? `?unit=${unit}` : ""}`;
  current = await api(path);
  setMathText($("prompt"), current.prompt);
  setLatex($("problem"), current.latex);
  $("problem").hidden = !current.latex; // 文章題で式がないときは問題文だけを出す
  setVariable(current.variable);
  setLatex($("answer-prefix"), current.answer_prefix);
  $("answer-math").value = "";
  $("answer-text").value = "";
  $("error").hidden = true;
  $("preview").hidden = true;
  $("result").hidden = true;
  $("problem-card").hidden = false;
  resetNote();
  activeField = null;
  $("submit").disabled = false;
  // 「次の問題」は下のほうにあるので、問題の先頭が見えるところまで戻す
  const top = $("problem-card").getBoundingClientRect().top;
  if (top < 0) window.scrollBy({ top: top - 16 });
  // パソコンでは、すぐ打ち始められるようにフォーカスする（その位置までスクロールはしない）
  if (!touchDevice) (useText ? $("answer-text") : $("answer-math")).focus({ preventScroll: true });
}

function readAnswer() {
  if (useText) return $("answer-text").value;
  // MathLive は \times を ASCII の "xx" に変換し、x×x と区別できなくなるため \cdot に置き換えてから変換する
  const latex = $("answer-math").getValue("latex").replace(/\\times/g, "\\cdot ");
  return MathLive.convertLatexToAsciiMath(latex);
}

async function submit() {
  if (!current || $("submit").disabled) return;
  const answer = readAnswer();
  let result;
  try {
    result = await api("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_id: current.problem_id, answer }),
    });
  } catch (e) {
    $("error").textContent = e.message;
    $("error").hidden = false;
    return;
  }
  $("error").hidden = true;
  $("submit").disabled = true;
  showResult(result);
}

function showResult(r) {
  const verdict = $("verdict");
  verdict.textContent = r.correct ? "正解！" : "不正解";
  verdict.className = `verdict ${r.correct ? "ok" : "ng"}`;
  // 単元・型の名前は解き方のヒントになるので、答え合わせの後にだけ出す
  setMathText($("problem-type"), `この問題：${current.unit_name} ／ ${current.type_name}`);
  setLatex($("user-answer"), r.user_latex);
  setLatex($("correct-answer"), r.answer_latex);

  const diag = $("diagnosis");
  if (r.correct) {
    diag.hidden = true;
  } else {
    diag.hidden = false;
    if (r.misconception) {
      setMathText($("diag-label"), `考えられる原因: ${r.misconception.label}`);
      setMathText($("diag-explanation"), r.misconception.explanation);
    } else {
      $("diag-label").textContent = "よくある間違いのパターンには当てはまりませんでした";
      $("diag-explanation").textContent = "下の「解き方」で、どこで答えがずれたか確認しましょう。";
    }
  }
  $("result-note").hidden = !r.note;
  if (r.note) setMathText($("result-note-text"), r.note);

  const steps = $("steps");
  steps.innerHTML = "";
  for (const s of r.steps) {
    const li = document.createElement("li");
    li.textContent = s;
    steps.appendChild(li);
  }
  renderMath(steps);
  $("steps-box").open = !r.correct;

  $("next-due").textContent = `この型の次の復習: ${formatDue(r.next_due)}`;
  $("result").hidden = false;
  if (!touchDevice) $("next").focus({ preventScroll: true }); // Enter で次の問題へ進めるように
  $("result").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function formatDue(iso) {
  if (!iso) return "未学習";
  const days = Math.round((new Date(iso) - new Date()) / 86400000);
  if (days <= 0) return "今すぐ";
  return `${days}日後`;
}

async function loadStats() {
  const rows = await api("/api/stats");
  const body = $("stats-body");
  body.innerHTML = "";
  let lastUnit = null;
  for (const s of rows) {
    // 単元が変わるところに見出しの行を入れる
    if (s.unit_id !== lastUnit) {
      lastUnit = s.unit_id;
      const head = document.createElement("tr");
      head.className = "unit-row";
      head.innerHTML = `<th colspan="6"></th>`;
      head.cells[0].textContent = s.unit_name;
      body.appendChild(head);
    }
    const tr = document.createElement("tr");
    const pct = Math.round(s.accuracy * 100);
    const mistakes = s.mistakes.length
      ? `<ul>${s.mistakes.slice(0, 3).map((m) => `<li class="m"></li>`).join("")}</ul>`
      : "—";
    tr.innerHTML = `
      <td></td>
      <td>${s.attempts}</td>
      <td>${s.attempts ? `<span class="meter"><span style="width:${pct}%"></span></span>${pct}%` : "—"}</td>
      <td>${s.box} / 4</td>
      <td>${s.attempts ? formatDue(s.due_at) : "未学習"}</td>
      <td>${mistakes}</td>`;
    tr.cells[0].textContent = s.type_name;
    tr.querySelectorAll("li.m").forEach((li, i) => {
      li.textContent = `${s.mistakes[i].label}（${s.mistakes[i].count}回）`;
    });
    renderMath(tr);
    body.appendChild(tr);
  }
}

function switchTab(tab) {
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  $("drill").hidden = tab === "stats";
  $("stats").hidden = tab !== "stats";
  if (tab === "stats") {
    loadStats();
    return;
  }
  mode = tab;
  $("type-label").hidden = tab !== "practice";
  $("review-hint").hidden = tab !== "review";
  newProblem();
}

function toggleInput() {
  useText = !useText;
  $("answer-math").hidden = useText;
  $("answer-text").hidden = !useText;
  $("guide-math").hidden = useText;
  $("guide-text").hidden = !useText;
  $("toggle-input").textContent = useText ? "数式エディタで入力する" : "テキストで入力する";
  updatePreview();
  (useText ? $("answer-text") : $("answer-math")).focus();
}

// テキスト入力のとき、入力中の式がどう読み取られるかを表示する
let previewTimer = null;
function updatePreview() {
  clearTimeout(previewTimer);
  const text = $("answer-text").value;
  if (!useText || !text.trim()) {
    $("preview").hidden = true;
    return;
  }
  previewTimer = setTimeout(async () => {
    const el = $("preview");
    try {
      const r = await api(`/api/preview?text=${encodeURIComponent(text)}`);
      el.textContent = "";
      el.append("読み取った式: ");
      const span = document.createElement("span");
      setLatex(span, r.latex);
      el.append(span);
    } catch (e) {
      el.textContent = `読み取れません: ${e.message}`;
    }
    el.hidden = false;
  }, 300);
}

// 数式の入力ボタン（電卓風の 6 列。5 行＋積分・極限用の記号の行）。
// latex は数式エディタ用（#? は空欄、#0 は選択中の部分、#@ は直前の項）、
// text はテキスト入力用で [カーソルの前に入れる文字, 後に入れる文字]。
// kind は見た目の種類（fn: 関数・編集、num: 数字、op: 演算子、submit: 答え合わせ）。
// math: true のラベルは KaTeX で表示する
const key = (label, title, latex, text, kind = "fn", math = true) => ({ label, title, latex, text, kind, math });
const num = (d) => key(d, d, d, [d, ""], "num", false);
const act = (label, title, action, kind = "fn") => ({ label, title, action, kind });

// 変数のキー（x と x^2）は、数列の問題では n に置き換える（setVariable）
const varKey = (power) => ({ ...key("", "", "", []), power });

const MATH_BUTTONS = [
  varKey(1),
  key("(\\square)", "括弧", "\\left(#0\\right)", ["(", ")"]),
  act("←", "カーソルを左へ", "left"),
  act("→", "カーソルを右へ（指数や分数から抜けるときにも使う）", "right"),
  act("⌫", "1文字消す", "backspace"),
  act("AC", "全部消す", "clear", "op"),

  key("\\sin", "sin", "\\sin\\left(#0\\right)", ["sin(", ")"]),
  key("\\cos", "cos", "\\cos\\left(#0\\right)", ["cos(", ")"]),
  num("7"), num("8"), num("9"),
  key("÷", "割り算（直前の項を分子にした分数）", "\\frac{#@}{#?}", ["/", ""], "op", false),

  key("\\tan", "tan", "\\tan\\left(#0\\right)", ["tan(", ")"]),
  key("\\ln", "自然対数", "\\ln\\left(#0\\right)", ["ln(", ")"]),
  num("4"), num("5"), num("6"),
  key("×", "掛け算", "\\cdot", ["*", ""], "op", false),

  key("e^{\\square}", "指数関数 e", "e^{#?}", ["e^(", ")"]),
  key("\\sqrt{\\square}", "ルート", "\\sqrt{#0}", ["sqrt(", ")"]),
  num("1"), num("2"), num("3"),
  key("−", "引き算・マイナス", "-", ["-", ""], "op", false),

  key("\\square^{n}", "累乗（直前の項を底にする）", "#@^{#?}", ["^(", ")"]),
  varKey(2),
  num("0"),
  key(".", "小数点", ".", [".", ""], "num", false),
  act("答え合わせ", "答え合わせ（Enter）", "submit", "submit"),
  key("+", "足し算", "+", ["+", ""], "op", false),

  // 積分・極限で使う記号（左2列と、数字の列の左2つに並ぶ）
  key("\\pi", "円周率", "\\pi", ["pi", ""]),
  key("e", "ネイピア数 e", "e", ["e", ""]),
  key("\\infty", "無限大（極限）", "\\infty", ["oo", ""], "num"),
  // 「C」だけだと全部消す（Clear）と紛らわしいので「+C」として、押すと + C まで入れる
  key("+C", "積分定数 +C を入れる", "+C", ["+C", ""], "num"),
];

// 入力ボタンの入力先。解答欄か、途中式メモの行のうち最後にフォーカスしたもの
let activeField = null;

function targetField() {
  if (activeField && activeField.isConnected && !activeField.hidden) return activeField;
  return useText ? $("answer-text") : $("answer-math");
}

function insertText(before, after) {
  const input = $("answer-text");
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? start;
  const selected = input.value.slice(start, end);
  input.value = input.value.slice(0, start) + before + selected + after + input.value.slice(end);
  const cursor = start + before.length + selected.length;
  input.setSelectionRange(cursor, cursor);
  input.focus();
  updatePreview();
}

function pressMathButton(b) {
  if (b.action === "submit") {
    submit();
    return;
  }
  const field = targetField();
  const isText = field.tagName === "INPUT";
  if (b.action === "clear") {
    field.value = "";
    if (isText) updatePreview();
  } else if (b.action === "left" || b.action === "right") {
    const step = b.action === "left" ? -1 : 1;
    if (isText) {
      const pos = Math.min(Math.max((field.selectionStart ?? field.value.length) + step, 0), field.value.length);
      field.setSelectionRange(pos, pos);
    } else {
      field.executeCommand(step < 0 ? "moveToPreviousChar" : "moveToNextChar");
    }
  } else if (b.action === "backspace") {
    if (isText) {
      const pos = field.selectionStart ?? field.value.length;
      if (pos > 0) {
        field.value = field.value.slice(0, pos - 1) + field.value.slice(pos);
        field.setSelectionRange(pos - 1, pos - 1);
      }
      updatePreview();
    } else {
      field.executeCommand("deleteBackward");
    }
  } else if (isText) {
    insertText(...b.text);
    return;
  } else {
    field.insert(b.latex, { format: "latex", selectionMode: "placeholder" });
  }
  field.focus();
}

const varButtons = []; // [{b, btn}] 変数のキー
let variable = null;

function setVariable(v) {
  if (v === variable) return;
  variable = v;
  for (const { b, btn } of varButtons) {
    const label = b.power === 1 ? v : `${v}^2`;
    b.label = b.latex = label;
    b.text = [label, ""];
    b.title = b.power === 1 ? `変数 ${v}` : `${v} の2乗`;
    btn.title = b.title;
    katex.render(label, btn, { throwOnError: false });
  }
}

function setupMathButtons() {
  const bar = $("math-buttons");
  for (const b of MATH_BUTTONS) {
    const btn = document.createElement("button");
    if (b.power) varButtons.push({ b, btn });
    btn.type = "button";
    btn.title = b.title;
    btn.className = `key key-${b.kind}`;
    if (b.action === "submit") btn.id = "submit";
    if (b.math) katex.render(b.label, btn, { throwOnError: false });
    else if (b.action === "submit") btn.innerHTML = "答え<wbr>合わせ"; // 狭い画面では「答え」の後で折り返す
    else btn.textContent = b.label;
    // クリックで入力欄のフォーカス（カーソル位置）が外れないようにする
    btn.addEventListener("mousedown", (e) => e.preventDefault());
    btn.addEventListener("click", () => pressMathButton(b));
    bar.appendChild(btn);
  }
  setVariable("x");
}

// 入力方法の一覧（ダイアログ）。背景をクリックしても閉じる
function setupGuide() {
  const guide = $("guide");
  renderMath(guide);
  $("open-guide").addEventListener("click", () => guide.showModal());
  $("close-guide").addEventListener("click", () => guide.close());
  guide.addEventListener("click", (e) => {
    // ダイアログの余白をクリックしたときも target は dialog になるため、座標で外側か判定する
    const r = guide.getBoundingClientRect();
    const outside = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    if (outside) guide.close();
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => switchTab(b.dataset.tab)));
  $("new-problem").addEventListener("click", newProblem);
  $("type-select").addEventListener("change", newProblem);
  $("unit-select").addEventListener("change", changeUnit);
  $("next").addEventListener("click", newProblem);
  $("toggle-input").addEventListener("click", toggleInput);
  $("answer-text").addEventListener("input", updatePreview);
  setupGuide();
  setupMathButtons();
  setupNote();
  // 入力ボタンの入力先を、最後にフォーカスした数式欄にする
  document.addEventListener("focusin", (e) => {
    const el = e.target;
    if (el.tagName === "MATH-FIELD" || el.id === "answer-text") activeField = el;
  });
  for (const id of ["answer-math", "answer-text"]) {
    $(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        submit();
      }
    });
  }
  await loadUnits();
  await loadTypes();
  newProblem();
});
