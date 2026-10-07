"""答え合わせを別のプロセス（ワーカー）で、時間とメモリに上限を付けて動かす。

「9^9^9^9」のような解答は SymPy の計算が終わらず、メモリも使い切ってしまう。
同じプロセスで計算すると1回の解答でアプリ全体が止まるので、ワーカーに任せ、
時間内に終わらなければワーカーを止めて作り直す。
"""

import multiprocessing as mp
import os
import queue
import signal
import threading


class ComputeTimeout(Exception):
    """計算が時間内に終わらなかった（またはワーカーがメモリ不足などで落ちた）。"""


class Busy(Exception):
    """ワーカーがすべて使用中のまま空かなかった。"""


def _limit_memory(memory_mb: int | None) -> None:
    if not memory_mb:
        return
    try:
        import resource  # Linux などだけにある
    except ImportError:
        return
    limit = memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def _worker_main(conn, memory_mb: int | None) -> None:
    # Ctrl+C はアプリ本体が受けて、ワーカーは本体と一緒に終わる
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    _limit_memory(memory_mb)
    from .grading import TASKS

    conn.send("ready")
    while True:
        try:
            task, args = conn.recv()
        except EOFError:
            return
        try:
            result = ("ok", TASKS[task](*args))
        except Exception as exc:  # MemoryError・RecursionError も含め、本体に返して扱いを任せる
            result = ("err", exc)
        try:
            conn.send(result)
        except Exception as exc:  # 例外が pickle できないとき
            conn.send(("err", RuntimeError(str(exc))))


class _Worker:
    def __init__(self, ctx, memory_mb: int | None):
        self.conn, child = ctx.Pipe()
        self.proc = ctx.Process(target=_worker_main, args=(child, memory_mb), daemon=True)
        self.proc.start()
        child.close()
        self.ready = False

    def wait_ready(self, timeout: float) -> bool:
        """SymPy の読み込みが終わって "ready" が届くまで待つ。"""
        if not self.ready and self.conn.poll(timeout):
            self.ready = self.conn.recv() == "ready"
        return self.ready

    def kill(self) -> None:
        self.proc.kill()
        self.proc.join(1)
        self.conn.close()


class Sandbox:
    def __init__(self, workers: int = 2, timeout: float = 5.0, memory_mb: int | None = None, wait: float = 30.0):
        """timeout は1回の計算の上限（秒）、wait は空いたワーカーと、その起動を待つ上限（秒）。"""
        self.workers = workers
        self.timeout = timeout
        self.memory_mb = memory_mb
        self.wait = wait
        # スレッドのあるプロセスで fork すると固まることがあるので、どの OS でも spawn にする
        self._ctx = mp.get_context("spawn")
        self._idle: queue.Queue[_Worker] | None = None
        self._start_lock = threading.Lock()

    def _new_worker(self) -> _Worker:
        return _Worker(self._ctx, self.memory_mb)

    def start(self) -> None:
        """ワーカーを起動しておく（起動には SymPy の読み込みで数秒かかる）。呼ばなければ最初に使うときに起動する。"""
        self._pool()

    def _pool(self) -> queue.Queue:
        with self._start_lock:
            if self._idle is None:
                self._idle = queue.Queue()
                for _ in range(self.workers):
                    self._idle.put(self._new_worker())
        return self._idle

    def call(self, task: str, *args):
        """ワーカーで grading.TASKS[task](*args) を実行し、結果を返す。例外はそのまま投げ直す。"""
        idle = self._pool()
        try:
            w = idle.get(timeout=self.wait)
        except queue.Empty:
            raise Busy() from None
        try:
            # 起動直後のワーカーは SymPy の読み込みを待つ（この時間は計算の上限に含めない）
            if not w.wait_ready(self.wait):
                raise ComputeTimeout()
            w.conn.send((task, args))
            if not w.conn.poll(self.timeout):
                raise ComputeTimeout()
            status, value = w.conn.recv()
        except (ComputeTimeout, EOFError, OSError):
            w.kill()
            w = self._new_worker()
            raise ComputeTimeout() from None
        finally:
            idle.put(w)
        if status == "err":
            if isinstance(value, MemoryError):
                raise ComputeTimeout()
            raise value
        return value

    def close(self) -> None:
        if self._idle is None:
            return
        while not self._idle.empty():
            self._idle.get_nowait().kill()


def from_env() -> Sandbox:
    """環境変数 DRILL_WORKERS・DRILL_TIMEOUT・DRILL_WORKER_MEMORY_MB で設定する。"""
    memory = os.environ.get("DRILL_WORKER_MEMORY_MB")
    return Sandbox(
        workers=int(os.environ.get("DRILL_WORKERS", "2")),
        timeout=float(os.environ.get("DRILL_TIMEOUT", "5")),
        memory_mb=int(memory) if memory else None,
    )
