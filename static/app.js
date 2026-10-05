const $ = (id) => document.getElementById(id);

let mode = "practice"; // practice | review
let current = null; // 表示中の問題
let useText = false; // MathLive の代わりにテキスト入力を使う

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
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "通信エラー");
  return body;
}

async function loadTypes() {
  const types = await api("/api/types");
  const select = $("type-select");
  for (const t of types) {
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = t.name;
    select.appendChild(opt);
  }
}

async function newProblem() {
  const type = $("type-select").value;
  const path = mode === "review" ? "/api/review" : `/api/problem${type ? `?type=${type}` : ""}`;
  current = await api(path);
  $("problem-type").textContent = current.type_name;
  setLatex($("problem"), `f(x) = ${current.latex}`);
  $("answer-math").value = "";
  $("answer-text").value = "";
  $("error").hidden = true;
  $("preview").hidden = true;
  $("result").hidden = true;
  $("problem-card").hidden = false;
  $("submit").disabled = false;
  (useText ? $("answer-text") : $("answer-math")).focus();
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
  $("next").focus();
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
  for (const s of rows) {
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
  $("practice-toolbar").hidden = tab !== "practice";
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

// 数式の入力ボタン。latex は数式エディタ用（#? は空欄、#0 は選択中の部分、#@ は直前の項）、
// text はテキスト入力用で、[カーソルの前に入れる文字, 後に入れる文字]。null は区切り線、"row" は改行
const MATH_BUTTONS = [
  { label: "x", title: "変数 x", latex: "x", text: ["x", ""] },
  { label: "\\square^{n}", title: "累乗（直前の項を底にする）", latex: "#@^{#?}", text: ["^(", ")"] },
  { label: "\\frac{\\square}{\\square}", title: "分数", latex: "\\frac{#0}{#?}", text: ["(", ")/()"] },
  { label: "\\sqrt{\\square}", title: "ルート", latex: "\\sqrt{#0}", text: ["sqrt(", ")"] },
  { label: "(\\square)", title: "括弧", latex: "\\left(#0\\right)", text: ["(", ")"] },
  { label: "\\cdot", title: "掛け算", latex: "\\cdot", text: ["*", ""] },
  null,
  { label: "\\sin", title: "sin", latex: "\\sin\\left(#0\\right)", text: ["sin(", ")"] },
  { label: "\\cos", title: "cos", latex: "\\cos\\left(#0\\right)", text: ["cos(", ")"] },
  { label: "\\tan", title: "tan", latex: "\\tan\\left(#0\\right)", text: ["tan(", ")"] },
  { label: "e^{\\square}", title: "指数関数 e", latex: "e^{#?}", text: ["e^(", ")"] },
  { label: "\\ln", title: "自然対数", latex: "\\ln\\left(#0\\right)", text: ["ln(", ")"] },
  null,
  { label: "⌫", title: "1文字消す", action: "backspace" },
  { label: "クリア", title: "全部消す", action: "clear" },
  "row",
  ..."0123456789".split("").map((d) => ({ label: d, title: d, latex: d, text: [d, ""] })),
  null,
  { label: "+", title: "足し算", latex: "+", text: ["+", ""] },
  { label: "-", title: "引き算・マイナス", latex: "-", text: ["-", ""] },
];

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
  const mf = $("answer-math");
  const input = $("answer-text");
  if (b.action === "clear") {
    mf.value = "";
    input.value = "";
    updatePreview();
  } else if (b.action === "backspace") {
    if (useText) {
      const pos = input.selectionStart ?? input.value.length;
      if (pos > 0) {
        input.value = input.value.slice(0, pos - 1) + input.value.slice(pos);
        input.setSelectionRange(pos - 1, pos - 1);
      }
      updatePreview();
    } else {
      mf.executeCommand("deleteBackward");
    }
  } else if (useText) {
    insertText(...b.text);
    return;
  } else {
    mf.insert(b.latex, { format: "latex", selectionMode: "placeholder" });
  }
  (useText ? input : mf).focus();
}

function setupMathButtons() {
  const bar = $("math-buttons");
  for (const b of MATH_BUTTONS) {
    if (!b || b === "row") {
      const sep = document.createElement("span");
      sep.className = b ? "row-break" : "sep";
      bar.appendChild(sep);
      continue;
    }
    const btn = document.createElement("button");
    btn.type = "button";
    btn.title = b.title;
    if (b.action) btn.textContent = b.label;
    else katex.render(b.label, btn, { throwOnError: false });
    // クリックで入力欄のフォーカス（カーソル位置）が外れないようにする
    btn.addEventListener("mousedown", (e) => e.preventDefault());
    btn.addEventListener("click", () => pressMathButton(b));
    bar.appendChild(btn);
  }
}

// 入力方法ガイドの開閉を覚えておく（使えない環境では毎回開いた状態）
function setupGuide() {
  const guide = $("guide");
  try {
    if (localStorage.getItem("guideOpen") === "0") guide.open = false;
  } catch {}
  guide.addEventListener("toggle", () => {
    try {
      localStorage.setItem("guideOpen", guide.open ? "1" : "0");
    } catch {}
  });
  renderMath(guide);
}

window.addEventListener("DOMContentLoaded", async () => {
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => switchTab(b.dataset.tab)));
  $("new-problem").addEventListener("click", newProblem);
  $("type-select").addEventListener("change", newProblem);
  $("submit").addEventListener("click", submit);
  $("next").addEventListener("click", newProblem);
  $("toggle-input").addEventListener("click", toggleInput);
  $("answer-text").addEventListener("input", updatePreview);
  setupGuide();
  setupMathButtons();
  for (const id of ["answer-math", "answer-text"]) {
    $(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        submit();
      }
    });
  }
  await loadTypes();
  newProblem();
});
