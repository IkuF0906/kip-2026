// 計算用のノート。手書き（キャンバス）と途中式メモ（数式エディタの行）の2種類。
// 新しい問題を出すたびに resetNote() で白紙に戻す。

const note = {
  strokes: [], // 手書きの線。座標は CSS ピクセルで持ち、サイズが変わっても描き直せるようにする
  current: null,
  tool: "pen",
};

const PEN_WIDTH = 2.5;
const ERASER_WIDTH = 22;
const CANVAS_HEIGHT = 360;

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
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
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
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(CANVAS_HEIGHT * dpr);
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

function setupCanvas() {
  const canvas = $("note-canvas");
  canvas.style.height = `${CANVAS_HEIGHT}px`;

  canvas.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    canvas.setPointerCapture(e.pointerId);
    // ペンのボタンや消しゴム側で描いたときは消しゴムとして扱う
    const tool = e.pointerType === "pen" && (e.buttons & 32) ? "eraser" : note.tool;
    note.current = { tool, points: [canvasPoint(e)] };
    note.strokes.push(note.current);
    drawStroke(canvas.getContext("2d"), note.current);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!note.current) return;
    const pts = note.current.points;
    pts.push(canvasPoint(e));
    // 最後の1区間だけを描き足す
    drawStroke(canvas.getContext("2d"), { tool: note.current.tool, points: pts.slice(-2) });
  });
  const end = () => {
    note.current = null;
  };
  canvas.addEventListener("pointerup", end);
  canvas.addEventListener("pointercancel", end);

  new ResizeObserver(resizeCanvas).observe(canvas);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redrawCanvas);

  document.querySelectorAll(".note-tool").forEach((b) =>
    b.addEventListener("click", () => {
      note.tool = b.dataset.tool;
      document.querySelectorAll(".note-tool").forEach((x) => x.classList.toggle("active", x === b));
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
