// 計算用のノート。手書き（キャンバス）と途中式メモ（数式エディタの行）の2種類。
// 新しい問題を出すたびに resetNote() で白紙に戻す。

const note = {
  strokes: [], // 手書きの線。座標は CSS ピクセルで持ち、サイズが変わっても描き直せるようにする
  current: null,
  tool: "pen",
};

const PEN_WIDTH = 2.5;
const ERASER_WIDTH = 40;
// スマホでは問題と解答欄が離れすぎないよう低くする
const canvasHeight = () => (window.matchMedia("(max-width: 600px)").matches ? 360 : 520);

function inkColor() {
  return getComputedStyle(document.documentElement).getPropertyValue("--text").trim() || "#000";
}

function drawStroke(ctx, s) {
  ctx.globalCompositeOperation = s.tool === "eraser" ? "destination-out" : "source-over";
  ctx.lineWidth = s.tool === "eraser" ? ERASER_WIDTH : PEN_WIDTH;
  ctx.strokeStyle = inkColor();
  ctx.fillStyle = inkColor();
  const pts = s.points;
  if (pts.length === 1) {
    ctx.beginPath();
    ctx.arc(pts[0][0], pts[0][1], ctx.lineWidth / 2, 0, Math.PI * 2);
    ctx.fill();
    return;
  }
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) smoothTo(ctx, pts, i);
  ctx.stroke();
}

const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];

// 点 i-1 を制御点にして、隣り合う点の中点どうしを曲線でつなぐ（折れ線より角が目立たない）
function smoothTo(ctx, pts, i) {
  if (i === 1) {
    ctx.lineTo(...mid(pts[0], pts[1]));
    return;
  }
  ctx.quadraticCurveTo(pts[i - 1][0], pts[i - 1][1], ...mid(pts[i - 1], pts[i]));
}

// 描いている途中の線に、点 from 以降の区間だけを描き足す
function drawTail(ctx, s, from) {
  const pts = s.points;
  ctx.globalCompositeOperation = s.tool === "eraser" ? "destination-out" : "source-over";
  ctx.lineWidth = s.tool === "eraser" ? ERASER_WIDTH : PEN_WIDTH;
  ctx.strokeStyle = inkColor();
  ctx.beginPath();
  const start = from === 1 ? pts[0] : mid(pts[from - 2], pts[from - 1]);
  ctx.moveTo(...start);
  for (let i = from; i < pts.length; i++) smoothTo(ctx, pts, i);
  ctx.stroke();
}

function redrawCanvas() {
  const canvas = $("note-canvas");
  const ctx = canvas.getContext("2d");
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.restore();
  for (const s of note.strokes) drawStroke(ctx, s);
}

function resizeCanvas() {
  const canvas = $("note-canvas");
  const width = canvas.clientWidth;
  if (!width) return; // 非表示のときは大きさが 0 なので、表示されたときにやり直す
  const dpr = window.devicePixelRatio || 1;
  const height = canvasHeight();
  canvas.style.height = `${height}px`;
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  redrawCanvas();
}

function canvasPoint(e) {
  const rect = $("note-canvas").getBoundingClientRect();
  return [e.clientX - rect.left, e.clientY - rect.top];
}

// 消しゴムのときは、消える範囲を円の枠で表示する（ペンの消しゴム側で描いているときも含む）
function moveEraserCursor(e) {
  const cursor = $("eraser-cursor");
  const erasing = note.current ? note.current.tool === "eraser" : note.tool === "eraser" || (e.pointerType === "pen" && e.buttons & 32);
  cursor.hidden = !erasing;
  if (!erasing) return;
  const [x, y] = canvasPoint(e);
  cursor.style.width = cursor.style.height = `${ERASER_WIDTH}px`;
  cursor.style.transform = `translate(${x - ERASER_WIDTH / 2}px, ${y - ERASER_WIDTH / 2}px)`;
}

function setupCanvas() {
  const canvas = $("note-canvas");
  // 触れている指。2本目が触れたら拡大・移動の操作とみなし、1本目で書き始めた線を取り消す
  // （拡大・移動そのものはブラウザに任せる。CSS の touch-action: pinch-zoom）
  const touches = new Set();

  const cancelStroke = () => {
    if (!note.current) return;
    note.strokes.splice(note.strokes.indexOf(note.current), 1);
    note.current = null;
    redrawCanvas();
  };

  canvas.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    if (e.pointerType === "touch") {
      touches.add(e.pointerId);
      if (touches.size > 1) {
        cancelStroke();
        return;
      }
    }
    canvas.setPointerCapture(e.pointerId);
    // ペンのボタンや消しゴム側で描いたときは消しゴムとして扱う
    const tool = e.pointerType === "pen" && (e.buttons & 32) ? "eraser" : note.tool;
    note.current = { tool, pointerId: e.pointerId, points: [canvasPoint(e)] };
    note.strokes.push(note.current);
    drawStroke(canvas.getContext("2d"), note.current);
    moveEraserCursor(e);
  });
  canvas.addEventListener("pointermove", (e) => {
    moveEraserCursor(e);
    if (!note.current || e.pointerId !== note.current.pointerId) return;
    const pts = note.current.points;
    const from = pts.length;
    // 前回のイベントから後の細かい動きもまとめて受け取り、速く動かしても線が角張らないようにする
    const events = e.getCoalescedEvents?.() ?? [];
    for (const ev of events.length ? events : [e]) pts.push(canvasPoint(ev));
    drawTail(canvas.getContext("2d"), note.current, from);
  });
  const end = (e) => {
    touches.delete(e.pointerId);
    if (note.current && e.pointerId === note.current.pointerId) note.current = null;
  };
  canvas.addEventListener("pointerup", end);
  canvas.addEventListener("pointercancel", (e) => {
    // ブラウザが拡大・スクロールの操作として引き取ったときも、書きかけの線を取り消す
    if (note.current && e.pointerId === note.current.pointerId) cancelStroke();
    touches.delete(e.pointerId);
  });
  canvas.addEventListener("pointerleave", () => {
    $("eraser-cursor").hidden = true;
  });

  new ResizeObserver(resizeCanvas).observe(canvas);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redrawCanvas);

  document.querySelectorAll(".note-tool").forEach((b) =>
    b.addEventListener("click", () => {
      note.tool = b.dataset.tool;
      document.querySelectorAll(".note-tool").forEach((x) => x.classList.toggle("active", x === b));
      canvas.classList.toggle("erasing", note.tool === "eraser");
    })
  );
  $("note-undo").addEventListener("click", () => {
    note.strokes.pop();
    redrawCanvas();
  });
  $("note-clear").addEventListener("click", () => {
    note.strokes = [];
    redrawCanvas();
  });
}

// --- 途中式メモ ---

function addMemoLine(after = null, latex = "") {
  const row = document.createElement("div");
  row.className = "memo-line";

  const mf = document.createElement("math-field");
  // 画面の入力キーを使うので、MathLive の仮想キーボードは出さない
  mf.setAttribute("math-virtual-keyboard-policy", "manual");
  mf.value = latex;
  mf.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addMemoLine(row).focus();
    } else if (e.key === "Backspace" && !mf.value && $("memo-lines").children.length > 1) {
      // 空の行で Backspace を押したら行を消して前の行へ
      e.preventDefault();
      const prev = row.previousElementSibling || row.nextElementSibling;
      row.remove();
      prev.querySelector("math-field").focus();
    }
  });

  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "link";
  copy.textContent = "解答欄へ";
  copy.title = "この行の式を解答欄にコピーする";
  copy.addEventListener("click", () => copyToAnswer(mf.value));

  const del = document.createElement("button");
  del.type = "button";
  del.className = "link";
  del.textContent = "×";
  del.title = "この行を消す";
  del.addEventListener("click", () => {
    if ($("memo-lines").children.length > 1) row.remove();
    else mf.value = "";
  });

  row.append(mf, copy, del);
  const list = $("memo-lines");
  if (after) after.after(row);
  else list.appendChild(row);
  return mf;
}

function copyToAnswer(latex) {
  if (!latex) return;
  if (useText) {
    $("answer-text").value = MathLive.convertLatexToAsciiMath(latex);
    updatePreview();
    $("answer-text").focus();
  } else {
    $("answer-math").value = latex;
    $("answer-math").focus();
  }
}

// --- 全体 ---

function switchNoteTab(name) {
  document.querySelectorAll(".note-tab").forEach((b) => b.classList.toggle("active", b.dataset.note === name));
  $("note-draw").hidden = name !== "draw";
  $("note-memo").hidden = name !== "memo";
  if (name === "draw") resizeCanvas();
  try {
    localStorage.setItem("noteTab", name);
  } catch {}
}

function resetNote() {
  note.strokes = [];
  note.current = null;
  redrawCanvas();
  $("memo-lines").innerHTML = "";
  addMemoLine();
}

function setupNote() {
  setupCanvas();
  document.querySelectorAll(".note-tab").forEach((b) => b.addEventListener("click", () => switchNoteTab(b.dataset.note)));
  $("memo-add").addEventListener("click", () => {
    const rows = $("memo-lines").children;
    addMemoLine(rows[rows.length - 1]).focus();
  });
  let tab = "draw";
  try {
    tab = localStorage.getItem("noteTab") || "draw";
  } catch {}
  switchNoteTab(tab);
  resetNote();
}
