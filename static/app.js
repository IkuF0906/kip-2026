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

// 要素を作る（cls・text は省略できる）
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

async function api(path, options) {
  const res = await fetch(path, options);
  // nginx が返すエラー（回数制限など）は JSON ではない
  const body = await res.json().catch(() => ({}));
  if (res.status === 429) throw new Error("短い時間に送った回数が多すぎます。少し待ってからもう一度送ってください");
  if (!res.ok) throw new Error(body.detail || "通信エラー");
  return body;
}

// 単元を選んでいれば ?unit=... を付ける（「すべて」は空文字）
function withUnit(path, unit) {
  return unit ? `${path}?unit=${unit}` : path;
}

// 切り替えボタンの選択中の見た目と、読み上げ用の状態をそろえる
function markActive(button, on) {
  button.classList.toggle("active", on);
  button.setAttribute("aria-pressed", String(on));
}

// 動きを減らす設定のときは、スクロールをなめらかにしない
const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = false;
}

let units = []; // [{id, name}]
let selectedUnit = "derivative"; // 選んでいる単元（"" はすべて）

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
  const chips = $("unit-chips");
  for (const u of [{ id: "", name: "すべて" }, ...units]) {
    const chip = el("button", "chip", u.name);
    chip.type = "button";
    chip.dataset.unit = u.id;
    chip.addEventListener("click", () => selectUnit(u.id));
    chips.appendChild(chip);
  }
  const saved = savedUnit();
  selectedUnit = units.some((u) => u.id === saved) || saved === "" ? saved : "derivative";
  markSelectedUnit();
}

function markSelectedUnit() {
  for (const chip of $("unit-chips").children) {
    chip.setAttribute("aria-pressed", String(chip.dataset.unit === selectedUnit));
  }
}

// 問題の型の選択肢を、選んだ単元のものにする。「すべて」のときは単元ごとにまとめて並べる
async function loadTypes() {
  const unit = selectedUnit;
  const types = await api(withUnit("/api/types", unit));
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
    const opt = el("option", "", t.name);
    opt.value = t.id;
    parent.appendChild(opt);
  }
}

// 単元を切り替える。newOne が真なら、その単元の問題を出す
async function selectUnit(unit, newOne = true) {
  selectedUnit = unit;
  markSelectedUnit();
  try {
    localStorage.setItem("unit", unit);
  } catch {}
  await loadTypes();
  if (newOne) newProblem();
}

async function newProblem() {
  const unit = selectedUnit;
  const type = $("type-select").value;
  let path;
  if (mode === "review") path = withUnit("/api/review", unit);
  else if (type) path = `/api/problem?type=${type}`;
  else path = withUnit("/api/problem", unit);
  try {
    current = await api(path);
  } catch (e) {
    // 前の問題があればそのまま残し、取れなかったことだけを伝える
    showError(`問題を読み込めませんでした: ${e.message}`);
    $("problem-card").hidden = false;
    return;
  }
  // 単元は出すが、問題の型は解き方のヒントになるので答え合わせの後にだけ出す
  $("unit-tag").textContent = current.unit_name;
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
    showError(e.message);
    return;
  }
  $("error").hidden = true;
  $("submit").disabled = true;
  showResult(result);
  refreshDueBadge();
}

const ICON_CHECK = '<svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>';
const ICON_CROSS = '<svg viewBox="0 0 24 24"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>';

function showResult(r) {
  const result = $("result");
  result.classList.toggle("ok", r.correct);
  result.classList.toggle("ng", !r.correct);
  $("verdict-icon").innerHTML = r.correct ? ICON_CHECK : ICON_CROSS;
  $("verdict").textContent = r.correct ? "正解！" : "不正解";
  setMathText($("problem-type"), `${current.unit_name} ／ ${current.type_name}`);
  setLatex($("user-answer"), r.user_latex);
  setLatex($("correct-answer"), r.answer_latex);

  const diag = $("diagnosis");
  diag.hidden = r.correct;
  if (!r.correct) {
    if (r.misconception) {
      setMathText($("diag-label"), r.misconception.label);
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
  for (const s of r.steps) steps.appendChild(el("li", "", s));
  renderMath(steps);
  $("steps-box").open = !r.correct;

  $("next-due").textContent = `この型の次の復習: ${formatDue(r.next_due)}`;
  result.hidden = false;
  if (!touchDevice) $("next").focus({ preventScroll: true }); // Enter で次の問題へ進めるように
  result.scrollIntoView({ behavior: reduceMotion() ? "auto" : "smooth", block: "nearest" });
}

function formatDue(iso) {
  if (!iso) return "未学習";
  const days = Math.round((new Date(iso) - new Date()) / 86400000);
  if (days <= 0) return "今すぐ";
  return `${days}日後`;
}

// --- 成績 ---

const isDue = (s) => s.attempts > 0 && s.due_at && new Date(s.due_at) <= new Date();

// 「復習」のタブに、期限が来た型の数を出す
function showDueBadge(rows) {
  const n = rows.filter(isDue).length;
  $("due-badge").textContent = n;
  $("due-badge").hidden = n === 0;
  $("due-badge-label").textContent = n ? `（期限の来た型 ${n}）` : "";
}

async function refreshDueBadge() {
  try {
    showDueBadge(await api("/api/stats"));
  } catch {} // バッジは補助の表示なので、取れなくても何もしない
}

async function loadStats() {
  let rows;
  try {
    rows = await api("/api/stats");
  } catch {
    $("stats-error").hidden = false;
    return;
  }
  $("stats-error").hidden = true;
  showDueBadge(rows);

  const attempts = rows.reduce((n, s) => n + s.attempts, 0);
  const correct = rows.reduce((n, s) => n + s.correct, 0);
  $("sum-attempts").textContent = attempts;
  $("sum-accuracy").textContent = attempts ? Math.round((correct / attempts) * 100) : "-";
  $("sum-accuracy-unit").hidden = !attempts;
  $("sum-due").textContent = rows.filter(isDue).length;

  // つまずいているところ: 間違えたことのある型を、正答率の低い順に3つまで
  const weak = rows
    .filter((s) => s.mistakes.length && s.accuracy < 1)
    .sort((a, b) => a.accuracy - b.accuracy || b.attempts - a.attempts)
    .slice(0, 3);
  $("weak-box").hidden = !weak.length;
  const weakList = $("weak-list");
  weakList.innerHTML = "";
  for (const s of weak) {
    const item = el("div", "weak-item");
    const body = el("div", "weak-body");
    const name = el("div", "weak-name", s.type_name);
    name.appendChild(el("small", "", `／ ${s.unit_name}`));
    const mistakes = s.mistakes.slice(0, 2).map((m) => `${m.label} ${m.count}回`);
    const detail = el("div", "weak-detail");
    setMathText(detail, `${mistakes.join("、")} ・ 正答率 ${Math.round(s.accuracy * 100)}%`);
    body.append(name, detail);
    const go = el("button", "", "この型を練習する");
    go.type = "button";
    go.addEventListener("click", () => practiceType(s.unit_id, s.type_id));
    item.append(body, go);
    weakList.appendChild(item);
  }

  // 単元ごとの習熟: 型ごとに箱（0〜4）を点で表す
  const grid = $("stats-units");
  grid.innerHTML = "";
  const byUnit = new Map();
  for (const s of rows) {
    if (!byUnit.has(s.unit_id)) byUnit.set(s.unit_id, []);
    byUnit.get(s.unit_id).push(s);
  }
  for (const types of byUnit.values()) {
    const card = el("section", "pane unit-card");
    const head = el("div", "unit-card-head");
    const studied = types.filter((s) => s.attempts).length;
    head.append(el("h3", "", types[0].unit_name), el("span", "", `学習済み ${studied} / ${types.length} 型`));
    const bar = el("div", "bar");
    const fill = el("span");
    fill.style.width = `${(types.reduce((n, s) => n + s.box, 0) / (types.length * 4)) * 100}%`;
    bar.appendChild(fill);
    card.append(head, bar);
    for (const s of types) {
      const row = el("div", "type-row");
      const dots = el("span", "dots");
      dots.setAttribute("aria-label", `習熟 ${s.box} / 4`);
      for (let i = 0; i < 4; i++) dots.appendChild(el("span", i < s.box ? "dot on" : "dot"));
      const status = el("span", "status", s.attempts ? formatDue(s.due_at) : "未学習");
      if (s.attempts) status.classList.add(isDue(s) ? "due" : "later");
      row.append(el("span", "type-name", s.type_name), dots, status);
      if (s.mistakes.length) {
        const m = s.mistakes[0];
        const note = el("p", "type-mistakes");
        setMathText(note, `多い間違い: ${m.label}（${m.count}回）`);
        row.appendChild(note);
      }
      card.appendChild(row);
    }
    grid.appendChild(card);
  }
}

// 成績から、その型の練習に移る
async function practiceType(unit, type) {
  await selectUnit(unit, false);
  $("type-select").value = type;
  switchTab("practice");
}

function switchTab(tab) {
  document.querySelectorAll(".tab").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === tab);
    if (b.dataset.tab === tab) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
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

// スマホでは、ノートをボタンで開いたときだけ出す（PC では常に出ている）
function toggleNote() {
  const open = $("problem-card").classList.toggle("note-open");
  $("note-toggle").setAttribute("aria-expanded", String(open));
  $("note-toggle-label").textContent = open ? "ノートを閉じる" : "ノートを開く";
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
    const box = $("preview");
    try {
      const r = await api(`/api/preview?text=${encodeURIComponent(text)}`);
      box.textContent = "";
      box.append("読み取った式: ");
      const span = document.createElement("span");
      setLatex(span, r.latex);
      box.append(span);
    } catch (e) {
      box.textContent = `読み取れません: ${e.message}`;
    }
    box.hidden = false;
  }, 300);
}

// 数式の入力ボタン（電卓風の 6 列 × 6 行）。
// latex は数式エディタ用（#? は空欄、#0 は選択中の部分、#@ は直前の項）、
// text はテキスト入力用で [カーソルの前に入れる文字, 後に入れる文字]。
// kind は見た目の種類（fn: 関数・記号、num: 数字、op: 演算子、edit: カーソル・削除、clear: 全部消す、submit: 答え合わせ）。
// math: true のラベルは KaTeX で表示する
const key = (label, title, latex, text, kind = "fn", math = true) => ({ label, title, latex, text, kind, math });
const num = (d) => key(d, d, d, [d, ""], "num", false);
const act = (label, title, action, kind = "edit") => ({ label, title, action, kind });

// 変数のキー（x）は、数列の問題では n に置き換える（setVariable）
const varKey = () => ({ ...key("", "", "", []), variable: true });

// テキスト入力で分数のキーを押すと「(分子)/(分母)」が入る。その分子と分母の間の部分
const FRACTION_MIDDLE = ")/(";

const MATH_BUTTONS = [
  varKey(),
  key("(\\square)", "括弧", "\\left(#0\\right)", ["(", ")"]),
  act("←", "カーソルを左へ", "left"),
  act("→", "カーソルを右へ（指数や分数から抜けるときにも使う）", "right"),
  act("⌫", "1文字消す", "backspace"),
  act("AC", "全部消す", "clear", "clear"),

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
  // ÷ は直前の項を分子にするが、こちらは空の分数を入れる（選んでいる部分があれば分子にする）
  key("\\dfrac{\\square}{\\square}", "分数", "\\frac{#0}{#?}", ["(", `${FRACTION_MIDDLE})`]),
  num("0"),
  key(".", "小数点", ".", [".", ""], "num", false),
  key("\\pi", "円周率", "\\pi", ["pi", ""]),
  key("+", "足し算", "+", ["+", ""], "op", false),

  // 積分・極限で使う記号と、答え合わせ（右下の3列分）
  key("e", "ネイピア数 e", "e", ["e", ""]),
  key("\\infty", "無限大（極限）", "\\infty", ["oo", ""]),
  // 「C」だけだと全部消す（Clear）と紛らわしいので「+C」として、押すと + C まで入れる
  key("+C", "積分定数 +C を入れる", "+C", ["+C", ""]),
  act("答え合わせ", "答え合わせ（Enter）", "submit", "submit"),
];

// 入力ボタンの入力先。解答欄か、途中式メモの行のうち最後にフォーカスしたもの
let activeField = null;

function targetField() {
  if (activeField && activeField.isConnected && !activeField.hidden) return activeField;
  return useText ? $("answer-text") : $("answer-math");
}

// テキスト入力の選択範囲（カーソルだけのときは start === end）
function textSelection(input) {
  const start = input.selectionStart ?? input.value.length;
  return [start, input.selectionEnd ?? start];
}

// 選んでいる部分を before と after で挟む（選んでいなければカーソルの位置に入れる）
function insertText(input, before, after) {
  const [start, end] = textSelection(input);
  const selected = input.value.slice(start, end);
  input.value = input.value.slice(0, start) + before + selected + after + input.value.slice(end);
  const cursor = start + before.length + selected.length;
  input.setSelectionRange(cursor, cursor);
}

// step は -1（左）か 1（右）
function moveTextCursor(input, step) {
  const [cur] = textSelection(input);
  // 分数のキーで入れた「(分子)/(分母)」の「)/(」は、1回で飛び越えて分子と分母の間を移る
  const jump =
    step > 0 ? input.value.startsWith(FRACTION_MIDDLE, cur) : input.value.slice(0, cur).endsWith(FRACTION_MIDDLE);
  const pos = Math.min(Math.max(cur + step * (jump ? FRACTION_MIDDLE.length : 1), 0), input.value.length);
  input.setSelectionRange(pos, pos);
}

// 選んでいる部分があればそれを、なければカーソルの前の1文字を消す
function deleteTextBackward(input) {
  let [start, end] = textSelection(input);
  if (start === end) start = Math.max(start - 1, 0);
  input.value = input.value.slice(0, start) + input.value.slice(end);
  input.setSelectionRange(start, start);
}

function pressTextKey(input, b) {
  if (b.action === "left" || b.action === "right") {
    moveTextCursor(input, b.action === "left" ? -1 : 1);
    return;
  }
  if (b.action === "clear") input.value = "";
  else if (b.action === "backspace") deleteTextBackward(input);
  else insertText(input, ...b.text);
  updatePreview();
}

const MATH_FIELD_COMMANDS = { left: "moveToPreviousChar", right: "moveToNextChar", backspace: "deleteBackward" };

function pressMathFieldKey(field, b) {
  if (b.action === "clear") field.value = "";
  else if (b.action) field.executeCommand(MATH_FIELD_COMMANDS[b.action]);
  else field.insert(b.latex, { format: "latex", selectionMode: "placeholder" });
}

function pressMathButton(b) {
  if (b.action === "submit") {
    submit();
    return;
  }
  const field = targetField();
  if (field.tagName === "INPUT") pressTextKey(field, b);
  else pressMathFieldKey(field, b);
  field.focus();
}

const varButtons = []; // [{b, btn}] 変数のキー
let variable = null;

function setVariable(v) {
  if (v === variable) return;
  variable = v;
  for (const { b, btn } of varButtons) {
    b.label = b.latex = v;
    b.text = [v, ""];
    b.title = `変数 ${v}`;
    btn.title = b.title;
    katex.render(v, btn, { throwOnError: false });
  }
}

function setupMathButtons() {
  const bar = $("math-buttons");
  for (const b of MATH_BUTTONS) {
    const btn = document.createElement("button");
    if (b.variable) varButtons.push({ b, btn });
    btn.type = "button";
    btn.title = b.title;
    btn.className = `key key-${b.kind}`;
    if (b.action === "submit") btn.id = "submit";
    if (b.math) katex.render(b.label, btn, { throwOnError: false });
    else btn.textContent = b.label;
    // クリックで入力欄のフォーカス（カーソル位置）が外れないようにする
    btn.addEventListener("mousedown", (e) => e.preventDefault());
    btn.addEventListener("click", () => pressMathButton(b));
    bar.appendChild(btn);
  }
  setVariable("x");
}

// 長押し・右クリックで MathLive のメニュー（英語）が出ないようにする。
// ページに組み込まれる前に設定すると例外になるので、組み込まれたとき（mount）にも設定する
function hideMathMenu(mf) {
  const apply = () => {
    try {
      mf.menuItems = [];
    } catch {}
  };
  apply();
  mf.addEventListener("mount", apply, { once: true });
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
  $("next").addEventListener("click", newProblem);
  $("start-review").addEventListener("click", () => switchTab("review"));
  $("stats-retry").addEventListener("click", loadStats);
  $("toggle-input").addEventListener("click", toggleInput);
  $("note-toggle").addEventListener("click", toggleNote);
  $("answer-text").addEventListener("input", updatePreview);
  hideMathMenu($("answer-math"));
  setupGuide();
  setupMathButtons();
  setupNote();
  // 入力ボタンの入力先を、最後にフォーカスした数式欄にする
  document.addEventListener("focusin", (e) => {
    const t = e.target;
    if (t.tagName === "MATH-FIELD" || t.id === "answer-text") activeField = t;
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
  refreshDueBadge();
});
