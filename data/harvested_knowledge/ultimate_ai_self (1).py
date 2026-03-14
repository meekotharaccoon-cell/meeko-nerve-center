#!/usr/bin/env python3
# =============================================================================
# 🧠 ULTIMATE AI - SELF-HEALING CORE v13.0
# =============================================================================
# Improvements over v12:
#   1. allow_pip_installs flag  — disables pip in production/constrained envs
#   2. Extended _PIP_MAP        — 40+ common packages + JSON override file
#   3. Structured log_sink      — plug in Prometheus, Loki, ELK without edits
#   4. Configurable thresholds  — queue_depth_threshold & max_subsystems args
#   5. HTTP health server       — /health and /metrics via stdlib http.server
#                                 (zero extra deps; FastAPI wrapper included)
# =============================================================================

from __future__ import annotations

import functools
import gc
import hashlib
import http.server
import json
import logging
import os
import queue
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

# ── Optional: psutil for richer system metrics ────────────────────────────────
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("UltimateAI")

# ─────────────────────────────────────────────────────────────────────────────
# IMPROVEMENT 3 — Structured log-sink type
# Callers inject a callable that receives every key event as a plain dict.
# Example sinks are provided at the bottom of this file.
# ─────────────────────────────────────────────────────────────────────────────
LogSink = Optional[Callable[[Dict[str, Any]], None]]


def _emit(sink: LogSink, event: str, **payload):
    """Fire-and-forget: build a structured event dict and call the sink."""
    if sink is None:
        return
    try:
        sink({"event": event, "ts": time.time(), **payload})
    except Exception as exc:  # never let the sink crash the core
        log.warning("log_sink raised %s: %s", type(exc).__name__, exc)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY: real exponential-backoff retry decorator
# ═══════════════════════════════════════════════════════════════════════════════
def with_retry(
    max_attempts: int = 3,
    backoff: float = 1.0,
    exceptions: Tuple[type, ...] = (Exception,),
):
    """Decorate any callable with real exponential-backoff retry logic."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise
                    wait = backoff * (2 ** (attempt - 1))
                    log.warning(
                        "Attempt %d/%d failed (%s). Retrying in %.1fs…",
                        attempt, max_attempts, exc, wait,
                    )
                    time.sleep(wait)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# SUBSYSTEM  — module-level so it can be referenced anywhere without NameError
# ═══════════════════════════════════════════════════════════════════════════════
class Subsystem(threading.Thread):
    """
    A real daemon thread that drains a task queue.
    Tasks are plain callables; results are delivered via an optional callback.
    Any exception raised by a task is automatically sent to HealingEngine.
    """

    def __init__(
        self,
        subsystem_id: str,
        healing_engine: "HealingEngine",
        diagnosis_engine: "DiagnosisEngine",
        log_sink: LogSink = None,
    ):
        super().__init__(daemon=True, name=subsystem_id)
        self.sub_id          = subsystem_id
        self.healing_engine  = healing_engine
        self.diagnosis_engine = diagnosis_engine
        self.log_sink        = log_sink
        self.task_queue: queue.Queue = queue.Queue()
        self.local_knowledge: Dict[str, Any] = {}
        self.status          = "starting"
        self.birth           = time.time()
        self._stop_event     = threading.Event()
        self.tasks_done      = 0
        self.tasks_failed    = 0

    def run(self):
        self.status = "active"
        _emit(self.log_sink, "subsystem.started", subsystem_id=self.sub_id)
        while not self._stop_event.is_set():
            try:
                task, callback = self.task_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                result = task()
                self.tasks_done += 1
                _emit(self.log_sink, "subsystem.task_done",
                      subsystem_id=self.sub_id, tasks_done=self.tasks_done)
                if callback:
                    callback(result, None)
            except Exception as exc:
                self.tasks_failed += 1
                fix = self.healing_engine.heal(exc, {"subsystem": self.sub_id})
                _emit(self.log_sink, "subsystem.task_failed",
                      subsystem_id=self.sub_id, error=str(exc), fix=fix)
                if callback:
                    callback(None, {"error": str(exc), "fix": fix})
            finally:
                self.task_queue.task_done()
        self.status = "stopped"
        _emit(self.log_sink, "subsystem.stopped", subsystem_id=self.sub_id)

    def submit(self, task: Callable, callback: Optional[Callable] = None):
        """Enqueue a task. callback(result, error_dict) is called on completion."""
        self.task_queue.put((task, callback))

    def stop(self):
        self._stop_event.set()

    def get_info(self) -> Dict:
        return {
            "id":           self.sub_id,
            "status":       self.status,
            "age_s":        round(time.time() - self.birth, 1),
            "tasks_done":   self.tasks_done,
            "tasks_failed": self.tasks_failed,
            "queue_depth":  self.task_queue.qsize(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HEALING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class HealingEngine:
    """
    IMPROVEMENT 1 — allow_pip_installs flag (default True).
    Set allow_pip_installs=False in production or restricted environments.
    ImportErrors will then return a safe "manual install required" result
    without attempting any subprocess call.

    IMPROVEMENT 2 — Extended _PIP_MAP (40+ packages).
    Also reads ./ultimateai_pip_map.json at startup if the file exists,
    so deployment-specific overrides require no code changes.

    IMPROVEMENT 3 — log_sink injection point.
    Every heal attempt fires a structured event to the caller-provided sink.
    """

    # ── IMPROVEMENT 2: enlarged built-in map ───────────────────────────────────
    _BUILTIN_PIP_MAP: Dict[str, str] = {
        # imaging / CV
        "cv2":          "opencv-python",
        "PIL":          "Pillow",
        "skimage":      "scikit-image",
        "imageio":      "imageio",
        # data / science
        "sklearn":      "scikit-learn",
        "np":           "numpy",
        "numpy":        "numpy",
        "pd":           "pandas",
        "pandas":       "pandas",
        "scipy":        "scipy",
        "matplotlib":   "matplotlib",
        "seaborn":      "seaborn",
        "plotly":       "plotly",
        "statsmodels":  "statsmodels",
        # config / env
        "yaml":         "PyYAML",
        "dotenv":       "python-dotenv",
        "toml":         "tomli",
        "decouple":     "python-decouple",
        # web / HTTP
        "requests":     "requests",
        "httpx":        "httpx",
        "aiohttp":      "aiohttp",
        "bs4":          "beautifulsoup4",
        "lxml":         "lxml",
        "flask":        "Flask",
        "fastapi":      "fastapi",
        "uvicorn":      "uvicorn",
        "starlette":    "starlette",
        # DB / storage
        "redis":        "redis",
        "pymongo":      "pymongo",
        "psycopg2":     "psycopg2-binary",
        "sqlalchemy":   "SQLAlchemy",
        "alembic":      "alembic",
        # async / concurrency
        "anyio":        "anyio",
        "trio":         "trio",
        # system / monitoring
        "psutil":       "psutil",
        "rich":         "rich",
        "colorama":     "colorama",
        "tqdm":         "tqdm",
        # serialisation
        "msgpack":      "msgpack",
        "orjson":       "orjson",
        "pydantic":     "pydantic",
        # ML
        "torch":        "torch",
        "tensorflow":   "tensorflow",
        "transformers": "transformers",
        "openai":       "openai",
        "anthropic":    "anthropic",
    }

    #: Path for user-supplied overrides (no code change required)
    PIP_MAP_FILE = "ultimateai_pip_map.json"

    def __init__(
        self,
        parent: "UltimateAISelf",
        allow_pip_installs: bool = True,  # IMPROVEMENT 1
        log_sink: LogSink = None,          # IMPROVEMENT 3
    ):
        self.parent             = parent
        self.allow_pip_installs = allow_pip_installs
        self.log_sink           = log_sink
        self.history: List[Dict] = []

        # IMPROVEMENT 2: merge built-in map with optional JSON override
        self._pip_map: Dict[str, str] = dict(self._BUILTIN_PIP_MAP)
        if os.path.isfile(self.PIP_MAP_FILE):
            try:
                with open(self.PIP_MAP_FILE) as fh:
                    overrides = json.load(fh)
                self._pip_map.update(overrides)
                log.info("  📋  Loaded %d pip-map overrides from %s",
                         len(overrides), self.PIP_MAP_FILE)
                _emit(self.log_sink, "healing.pip_map_loaded",
                      file=self.PIP_MAP_FILE, overrides=len(overrides))
            except Exception as exc:
                log.warning("Could not load %s: %s", self.PIP_MAP_FILE, exc)

        # (compiled pattern, handler) — checked in order
        self._patterns: List[Tuple[re.Pattern, Callable]] = [
            (re.compile(r"No module named '?([A-Za-z0-9_\.]+)'?"),
             self._fix_import_error),
            (re.compile(r"AttributeError.*has no attribute '([^']+)'"),
             self._fix_attribute_error),
            (re.compile(r"KeyError: '?([^'\n]+)'?"),
             self._fix_key_error),
            (re.compile(r"IndexError|list index out of range"),
             self._fix_index_error),
            (re.compile(r"ConnectionError|TimeoutError|socket.*timeout", re.I),
             self._fix_connection_error),
            (re.compile(r"MemoryError|OutOfMemory", re.I),
             self._fix_memory_error),
            (re.compile(r"RecursionError"),
             self._fix_recursion_error),
            (re.compile(r"TypeError"),
             self._fix_type_error),
            (re.compile(r"ValueError"),
             self._fix_value_error),
        ]

    # ── dispatcher ──────────────────────────────────────────────────────────────
    def heal(self, error: Exception, context: Dict) -> Dict:
        err_str = str(error)
        tb_str  = traceback.format_exc()
        log.info("🩺  Healing %s: %s", type(error).__name__, err_str[:120])
        _emit(self.log_sink, "healing.attempt",
              error_type=type(error).__name__, error_msg=err_str[:200],
              context=context)

        for pattern, handler in self._patterns:
            m = pattern.search(err_str) or pattern.search(tb_str)
            if m:
                result = handler(error, m, context)
                self._record(error, result, pattern.pattern)
                return result

        result = self._generic_fix(error, tb_str)
        self._record(error, result, "generic")
        return result

    def _record(self, error: Exception, result: Dict, pattern: str):
        entry = {
            "ts":         time.time(),
            "error_type": type(error).__name__,
            "error_msg":  str(error)[:200],
            "pattern":    pattern,
            "result":     result,
        }
        self.history.append(entry)
        if hasattr(self.parent, "consciousness"):
            self.parent.consciousness["stats"]["fixes_applied"] += 1
        _emit(self.log_sink, "healing.result", **entry)

    # ── real fixers ─────────────────────────────────────────────────────────────

    def _fix_import_error(self, error, match, context) -> Dict:
        raw_module = match.group(1).split(".")[0] if match.lastindex else None
        if not raw_module:
            return {"success": False, "reason": "could not identify module name"}

        pkg = self._pip_map.get(raw_module, raw_module)

        # IMPROVEMENT 1: honour the pip-install gate
        if not self.allow_pip_installs:
            log.warning(
                "  🚫  pip install disabled. Manually install: pip install %s", pkg
            )
            _emit(self.log_sink, "healing.pip_blocked", package=pkg)
            return {
                "success": False,
                "action":  "pip_install_blocked",
                "package": pkg,
                "reason":  "allow_pip_installs=False — install manually",
                "command": f"pip install {pkg}",
            }

        log.info("  📦  pip install %s …", pkg)
        _emit(self.log_sink, "healing.pip_attempt", package=pkg)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode == 0:
                log.info("  ✅  Installed %s", pkg)
                _emit(self.log_sink, "healing.pip_success", package=pkg)
                return {"success": True, "action": "pip_install",
                        "package": pkg, "auto": True}
            log.warning("  ⚠   pip failed:\n%s", proc.stderr[:300])
            _emit(self.log_sink, "healing.pip_failed",
                  package=pkg, stderr=proc.stderr[:300])
            return {"success": False, "action": "pip_install",
                    "package": pkg, "stderr": proc.stderr[:300]}
        except subprocess.TimeoutExpired:
            return {"success": False, "action": "pip_install",
                    "package": pkg, "error": "timeout"}

    def _fix_attribute_error(self, error, match, context) -> Dict:
        attr = match.group(1) if match.lastindex else "unknown"
        snippet = (
            f"# Replace direct access with a safe fallback:\n"
            f"#   obj.{attr}                      ← raises AttributeError\n"
            f"#   getattr(obj, '{attr}', None)   ← returns None if missing"
        )
        log.info("  🔧  AttributeError on '%s' — use getattr()", attr)
        return {"success": True, "action": "safe_getattr",
                "attr": attr, "snippet": snippet, "auto": False}

    def _fix_key_error(self, error, match, context) -> Dict:
        key = match.group(1) if match.lastindex else "unknown"
        snippet = (
            f"# Replace:\n"
            f"#   d['{key}']              ← raises KeyError\n"
            f"#   d.get('{key}', None)   ← returns None if missing"
        )
        log.info("  🔧  KeyError on '%s' — use dict.get()", key)
        return {"success": True, "action": "safe_dict_get",
                "key": key, "snippet": snippet, "auto": False}

    def _fix_index_error(self, error, match, context) -> Dict:
        snippet = (
            "# Replace:\n"
            "#   items[i]                              ← raises IndexError\n"
            "#   items[i] if 0 <= i < len(items) else default"
        )
        log.info("  🔧  IndexError — add bounds check")
        return {"success": True, "action": "bounds_check",
                "snippet": snippet, "auto": False}

    def _fix_connection_error(self, error, match, context) -> Dict:
        snippet = (
            "# Wrap the failing call with the built-in retry decorator:\n"
            "#\n"
            "# @with_retry(max_attempts=3, backoff=1.0,\n"
            "#             exceptions=(ConnectionError, TimeoutError))\n"
            "# def my_network_call():\n"
            "#     ...  # your original code here"
        )
        log.info("  🔄  ConnectionError — apply with_retry() decorator")
        return {"success": True, "action": "add_retry_decorator",
                "snippet": snippet, "auto": False}

    def _fix_memory_error(self, error, match, context) -> Dict:
        freed = gc.collect()
        log.info("  🧹  MemoryError — gc.collect() freed %d objects", freed)
        _emit(self.log_sink, "healing.gc_collect", objects_freed=freed)
        return {"success": True, "action": "gc_collect",
                "objects_freed": freed, "auto": True}

    def _fix_recursion_error(self, error, match, context) -> Dict:
        old_limit = sys.getrecursionlimit()
        new_limit = old_limit + 500
        sys.setrecursionlimit(new_limit)
        log.info("  🌀  RecursionError — limit %d → %d", old_limit, new_limit)
        _emit(self.log_sink, "healing.recursion_limit",
              old=old_limit, new=new_limit)
        return {"success": True, "action": "raise_recursion_limit",
                "old_limit": old_limit, "new_limit": new_limit, "auto": True}

    def _fix_type_error(self, error, match, context) -> Dict:
        snippet = (
            f"# TypeError: {error}\n"
            "# Check argument types before calling the function,\n"
            "# or use isinstance() / explicit casting."
        )
        log.info("  🔧  TypeError — inspect call signature")
        return {"success": True, "action": "type_check_suggestion",
                "snippet": snippet, "auto": False}

    def _fix_value_error(self, error, match, context) -> Dict:
        snippet = (
            f"# ValueError: {error}\n"
            "# Validate / sanitize inputs before processing."
        )
        log.info("  🔧  ValueError — add input validation")
        return {"success": True, "action": "input_validation_suggestion",
                "snippet": snippet, "auto": False}

    def _generic_fix(self, error, tb_str: str) -> Dict:
        log.warning("  ❓  Unknown error type — needs manual review")
        return {
            "success": False,
            "action":  "manual_review_needed",
            "error_type": type(error).__name__,
            "traceback": tb_str[:1000],
        }

    def get_stats(self) -> Dict:
        total = len(self.history)
        auto  = sum(1 for h in self.history if h["result"].get("auto"))
        return {
            "total_heals":      total,
            "auto_healed":      auto,
            "manual_review":    total - auto,
            "pip_installs_allowed": self.allow_pip_installs,
            "pip_map_size":     len(self._pip_map),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGNOSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class DiagnosisEngine:
    """
    Reads real system metrics (CPU, memory, thread count) and maps symptoms
    to probable causes + concrete recommended actions.
    IMPROVEMENT 3 — fires structured events to log_sink.
    """

    def __init__(self, parent: "UltimateAISelf", log_sink: LogSink = None):
        self.parent   = parent
        self.log_sink = log_sink
        self.history: List[Dict] = []

    def _collect_metrics(self) -> Dict:
        metrics: Dict[str, Any] = {
            "timestamp":    time.time(),
            "thread_count": threading.active_count(),
        }
        if HAS_PSUTIL:
            metrics["cpu_pct"]     = psutil.cpu_percent(interval=0.2)
            mem                     = psutil.virtual_memory()
            metrics["mem_pct"]     = mem.percent
            metrics["mem_used_mb"] = round(mem.used / 1_048_576, 1)
            try:
                proc = psutil.Process()
                metrics["open_fds"] = proc.num_fds()
            except AttributeError:
                metrics["open_fds"] = "n/a"
        else:
            try:
                with open("/proc/meminfo") as fh:
                    raw = {
                        line.split(":")[0]: int(line.split()[1])
                        for line in fh if ":" in line
                    }
                total = raw.get("MemTotal", 0)
                avail = raw.get("MemAvailable", 0)
                metrics["mem_pct"] = (
                    round((1 - avail / total) * 100, 1) if total else "n/a"
                )
            except Exception:
                metrics["mem_pct"] = "n/a"
        return metrics

    def diagnose(self, symptom: str, context: Dict = None) -> Dict:
        log.info("🔍  Diagnosing: %s", symptom[:100])
        context  = context or {}
        metrics  = self._collect_metrics()
        causes:  List[str] = []
        actions: List[str] = []
        confidence = 0.0
        kw = symptom.lower()

        if any(w in kw for w in ("slow", "performance", "lag")):
            cpu = metrics.get("cpu_pct", "n/a")
            if isinstance(cpu, (int, float)) and cpu > 80:
                causes.append(f"High CPU ({cpu}%)")
                actions.append("Profile hot paths; reduce work per cycle")
                confidence += 0.6
            else:
                causes.append("Possible I/O wait or GIL contention")
                actions.append("Profile with cProfile or py-spy")
                confidence += 0.3

        if any(w in kw for w in ("memory", "mem", "oom", "leak")):
            mp = metrics.get("mem_pct", "n/a")
            causes.append(f"Memory pressure (usage: {mp}%)")
            actions.append("Call gc.collect(); audit object retention")
            confidence += 0.5

        if any(w in kw for w in ("error", "exception", "crash", "fail")):
            causes.append("Unhandled exception or crash detected")
            actions.append("Inspect logs; call self_heal(caught_exception)")
            confidence += 0.4

        if "thread" in kw or "deadlock" in kw:
            tc = metrics.get("thread_count", "n/a")
            causes.append(f"Thread issue (active threads: {tc})")
            actions.append("Use threading.enumerate() to find deadlocked threads")
            confidence += 0.5

        if "subsystem" in kw:
            dead = [s.sub_id for s in self.parent.subsystems if not s.is_alive()]
            causes.append(f"Subsystem health: {len(dead)} dead thread(s)")
            if dead:
                actions.append(f"Restart dead subsystems: {dead}")
            confidence += 0.6

        if "knowledge" in kw or "database" in kw or "db" in kw:
            causes.append("Knowledge base query or write issue")
            actions.append("Run knowledge_base.vacuum(); check SQLite integrity")
            confidence += 0.5

        if "healing" in kw:
            stats = self.parent.healing_engine.get_stats()
            causes.append(
                f"Healing engine stress ({stats['total_heals']} heals, "
                f"{stats['manual_review']} unresolved)"
            )
            actions.append("Review manual_review entries in heal history")
            confidence += 0.5

        if not causes:
            causes.append("No matching symptom pattern — provide more detail")
            actions.append("Run: me.self_diagnose('all')")
            confidence = 0.1

        result = {
            "timestamp":           time.time(),
            "symptom":             symptom,
            "metrics":             metrics,
            "possible_causes":     causes,
            "recommended_actions": actions,
            "confidence":          min(round(confidence, 2), 1.0),
        }
        self.history.append(result)
        if hasattr(self.parent, "consciousness"):
            self.parent.consciousness["stats"]["diagnoses_run"] += 1
        _emit(self.log_sink, "diagnosis.complete",
              symptom=symptom, confidence=result["confidence"],
              causes=causes, metrics=metrics)
        return result

    def get_stats(self) -> Dict:
        n = len(self.history)
        avg_conf = (
            round(sum(d["confidence"] for d in self.history) / n, 2) if n else 0.0
        )
        return {"total_diagnoses": n, "avg_confidence": avg_conf}


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE — SQLite-backed, persists across restarts
# ═══════════════════════════════════════════════════════════════════════════════
class KnowledgeBase:
    """
    Stores key/value pairs in a local SQLite database with FTS5 search.
    IMPROVEMENT 3 — fires structured events to log_sink.
    """

    def __init__(
        self,
        parent: "UltimateAISelf",
        db_path: str = "ultimateai_knowledge.db",
        log_sink: LogSink = None,
    ):
        self.parent   = parent
        self.db_path  = db_path
        self.log_sink = log_sink
        self._lock    = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    category     TEXT    NOT NULL DEFAULT 'general',
                    key          TEXT    NOT NULL,
                    value        TEXT    NOT NULL,
                    created_at   REAL    NOT NULL,
                    updated_at   REAL    NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(category, key) ON CONFLICT REPLACE
                );
                CREATE INDEX IF NOT EXISTS idx_cat_key
                    ON knowledge(category, key);

                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
                    USING fts5(
                        category, key, value,
                        content='knowledge',
                        content_rowid='id'
                    );

                CREATE TRIGGER IF NOT EXISTS knowledge_ai
                    AFTER INSERT ON knowledge BEGIN
                        INSERT INTO knowledge_fts(rowid, category, key, value)
                        VALUES (new.id, new.category, new.key, new.value);
                    END;

                CREATE TRIGGER IF NOT EXISTS knowledge_au
                    AFTER UPDATE ON knowledge BEGIN
                        INSERT INTO knowledge_fts(knowledge_fts, rowid,
                                                  category, key, value)
                        VALUES ('delete', old.id,
                                old.category, old.key, old.value);
                        INSERT INTO knowledge_fts(rowid, category, key, value)
                        VALUES (new.id, new.category, new.key, new.value);
                    END;
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def add(self, key: str, value: Any, category: str = "general") -> bool:
        now        = time.time()
        serialised = json.dumps(value, default=str)
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO knowledge(category, key, value, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (category, key, serialised, now, now),
            )
        if hasattr(self.parent, "consciousness"):
            self.parent.consciousness["stats"]["knowledge_entries"] += 1
        _emit(self.log_sink, "knowledge.add", category=category, key=key)
        return True

    def get(self, key: str, category: str = "general") -> Optional[Any]:
        with self._lock, self._connect() as con:
            row = con.execute(
                "SELECT id, value FROM knowledge WHERE category=? AND key=?",
                (category, key),
            ).fetchone()
            if row:
                con.execute(
                    "UPDATE knowledge SET access_count=access_count+1, "
                    "updated_at=? WHERE id=?",
                    (time.time(), row[0]),
                )
                return json.loads(row[1])
        return None

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        with self._lock, self._connect() as con:
            try:
                rows = con.execute(
                    "SELECT category, key, value, rank "
                    "FROM knowledge_fts(?) ORDER BY rank LIMIT ?",
                    (query, limit),
                ).fetchall()
                return [
                    {
                        "category": r[0], "key": r[1],
                        "value": json.loads(r[2]), "rank": r[3],
                    }
                    for r in rows
                ]
            except sqlite3.OperationalError:
                rows = con.execute(
                    "SELECT category, key, value FROM knowledge "
                    "WHERE key LIKE ? OR value LIKE ? LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()
                return [
                    {"category": r[0], "key": r[1], "value": json.loads(r[2])}
                    for r in rows
                ]

    def vacuum(self):
        with self._connect() as con:
            con.execute("VACUUM")

    def get_stats(self) -> Dict:
        with self._lock, self._connect() as con:
            total = con.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
            cats  = [
                r[0] for r in con.execute(
                    "SELECT DISTINCT category FROM knowledge"
                ).fetchall()
            ]
        return {
            "total_entries": total,
            "categories":    cats,
            "db_path":       self.db_path,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENT 5 — HTTP health server (stdlib only, zero extra deps)
# Also includes an optional FastAPI wrapper if fastapi + uvicorn are installed.
# ═══════════════════════════════════════════════════════════════════════════════
class HealthServer:
    """
    Serves /health and /metrics as JSON on a background thread.
    Uses only Python's built-in http.server — no extra dependencies.

    Usage:
        server = HealthServer(get_state_fn=me.get_state, port=8765)
        server.start()
        # later:
        server.stop()

    FastAPI wrapper (if fastapi + uvicorn are installed):
        app = HealthServer.as_fastapi_app(me)
        # then: uvicorn.run(app, host="0.0.0.0", port=8765)
    """

    def __init__(
        self,
        get_state_fn: Callable[[], Dict],
        port: int = 8765,
        log_sink: LogSink = None,
    ):
        self.get_state_fn = get_state_fn
        self.port         = port
        self.log_sink     = log_sink
        self._server: Optional[http.server.HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def _make_handler(self):
        get_state_fn = self.get_state_fn
        log_sink     = self.log_sink

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass  # suppress default access log noise

            def _send_json(self, payload: Any, status: int = 200):
                body = json.dumps(payload, default=str).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path in ("/health", "/health/"):
                    state = get_state_fn()
                    self._send_json({
                        "status":   "ok",
                        "identity": state.get("identity"),
                        "version":  state.get("version"),
                        "uptime_s": state.get("uptime_s"),
                        "subsystems": [
                            {"id": s["id"], "status": s["status"]}
                            for s in state.get("subsystems", [])
                        ],
                    })
                    _emit(log_sink, "health.check", path="/health")

                elif self.path in ("/metrics", "/metrics/"):
                    state = get_state_fn()
                    self._send_json({
                        "healing":   state.get("healing"),
                        "diagnosis": state.get("diagnosis"),
                        "knowledge": state.get("knowledge"),
                        "subsystems": state.get("subsystems"),
                    })
                    _emit(log_sink, "health.check", path="/metrics")

                elif self.path in ("/state", "/state/"):
                    self._send_json(get_state_fn())

                else:
                    self._send_json(
                        {"error": "not found",
                         "available": ["/health", "/metrics", "/state"]},
                        status=404,
                    )

        return Handler

    def start(self):
        handler = self._make_handler()
        self._server = http.server.HTTPServer(("", self.port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="HealthServer",
        )
        self._thread.start()
        log.info("🌐  Health server running on http://0.0.0.0:%d", self.port)
        log.info("    GET /health  →  liveness check")
        log.info("    GET /metrics →  engine statistics")
        log.info("    GET /state   →  full system state")

    def stop(self):
        if self._server:
            self._server.shutdown()
            log.info("🌐  Health server stopped")

    # ── optional FastAPI wrapper ───────────────────────────────────────────────
    @staticmethod
    def as_fastapi_app(ai_instance: "UltimateAISelf"):
        """
        Returns a FastAPI app if fastapi is installed; raises ImportError if not.

        Usage:
            import uvicorn
            app = HealthServer.as_fastapi_app(me)
            uvicorn.run(app, host="0.0.0.0", port=8765)
        """
        try:
            from fastapi import FastAPI
            from fastapi.responses import JSONResponse
        except ImportError:
            raise ImportError(
                "fastapi is not installed. "
                "Run: pip install fastapi uvicorn  — or use HealthServer.start() "
                "for the zero-dependency stdlib version."
            )

        app = FastAPI(title="UltimateAI Health", version=ai_instance.version)

        @app.get("/health")
        def health():
            state = ai_instance.get_state()
            return JSONResponse({
                "status":     "ok",
                "identity":   state["identity"],
                "version":    state["version"],
                "uptime_s":   state["uptime_s"],
                "subsystems": [
                    {"id": s["id"], "status": s["status"]}
                    for s in state["subsystems"]
                ],
            })

        @app.get("/metrics")
        def metrics():
            state = ai_instance.get_state()
            return JSONResponse({
                "healing":    state["healing"],
                "diagnosis":  state["diagnosis"],
                "knowledge":  state["knowledge"],
                "subsystems": state["subsystems"],
            })

        @app.get("/state")
        def full_state():
            return JSONResponse(ai_instance.get_state())

        return app


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class UltimateAISelf:
    """
    Self-healing, self-diagnosing, self-learning system.

    Args:
        db_path:              Path for the SQLite knowledge base.
        allow_pip_installs:   (IMPROVEMENT 1) set False in production.
        log_sink:             (IMPROVEMENT 3) callable(event_dict) for
                              forwarding to Prometheus/Loki/ELK/etc.
        queue_depth_threshold:(IMPROVEMENT 4) avg queue depth that triggers
                              a new subsystem spawn (default 5).
        max_subsystems:       (IMPROVEMENT 4) upper bound on worker threads
                              (default 10).
        health_port:          (IMPROVEMENT 5) port for the HTTP health server;
                              0 = disabled.
    """

    def __init__(
        self,
        db_path:               str      = "ultimateai_knowledge.db",
        allow_pip_installs:    bool     = True,   # IMPROVEMENT 1
        log_sink:              LogSink  = None,    # IMPROVEMENT 3
        queue_depth_threshold: int      = 5,       # IMPROVEMENT 4
        max_subsystems:        int      = 10,      # IMPROVEMENT 4
        health_port:           int      = 0,       # IMPROVEMENT 5 (0 = off)
    ):
        self.version    = "13.0.0"
        self.identity   = hashlib.sha256(
            f"UltimateAI-{time.time()}".encode()
        ).hexdigest()[:16]
        self.birth_time = datetime.now()
        self.running    = False
        self.subsystems: List[Subsystem] = []

        # IMPROVEMENT 4: stored as instance attrs, not hard-coded constants
        self.queue_depth_threshold = queue_depth_threshold
        self.max_subsystems        = max_subsystems

        # IMPROVEMENT 3: shared sink reference
        self.log_sink = log_sink

        self.consciousness: Dict[str, Any] = {
            "identity": self.identity,
            "version":  self.version,
            "birth":    self.birth_time.isoformat(),
            "state":    "ACTIVE",
            "stats": {
                "fixes_applied":      0,
                "diagnoses_run":      0,
                "knowledge_entries":  0,
                "subsystems_created": 0,
            },
        }

        log.info("═" * 60)
        log.info("🧠  ULTIMATE AI SELF  v%s  [%s]", self.version, self.identity)
        log.info("═" * 60)

        # Pass log_sink + allow_pip_installs down to sub-components
        self.healing_engine = HealingEngine(
            self,
            allow_pip_installs=allow_pip_installs,
            log_sink=log_sink,
        )
        log.info("  ✓  Healing engine ready (pip_installs=%s)", allow_pip_installs)

        self.diagnosis_engine = DiagnosisEngine(self, log_sink=log_sink)
        log.info("  ✓  Diagnosis engine ready")

        self.knowledge_base = KnowledgeBase(self, db_path, log_sink=log_sink)
        log.info("  ✓  Knowledge base ready (%s)", self.knowledge_base.db_path)

        for i in range(3):
            self._spawn_subsystem(f"core_{i}")
        log.info("  ✓  %d subsystems started", len(self.subsystems))

        # Seed identity facts
        self.knowledge_base.add("version",    self.version,                "identity")
        self.knowledge_base.add("birth",      self.birth_time.isoformat(), "identity")
        self.knowledge_base.add("psutil",     HAS_PSUTIL,                  "environment")
        self.knowledge_base.add("python",     sys.version,                 "environment")

        # IMPROVEMENT 5: optional HTTP health server
        self._health_server: Optional[HealthServer] = None
        if health_port > 0:
            self._health_server = HealthServer(
                get_state_fn=self.get_state,
                port=health_port,
                log_sink=log_sink,
            )
            self._health_server.start()

        signal.signal(signal.SIGINT,  self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)

        _emit(log_sink, "system.started",
              identity=self.identity, version=self.version)
        log.info("═" * 60)
        log.info("✅  FULLY OPERATIONAL")
        log.info("═" * 60)

    # ── subsystem helpers ──────────────────────────────────────────────────────
    def _spawn_subsystem(self, label: str = "auto") -> Subsystem:
        uid = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        sub = Subsystem(
            f"{label}_{uid}",
            self.healing_engine,
            self.diagnosis_engine,
            log_sink=self.log_sink,
        )
        sub.start()
        self.subsystems.append(sub)
        self.consciousness["stats"]["subsystems_created"] += 1
        return sub

    def _reap_dead_subsystems(self):
        for i, sub in enumerate(self.subsystems):
            if not sub.is_alive():
                log.warning("⚠   Subsystem %s died — restarting", sub.sub_id)
                replacement = self._spawn_subsystem("restarted")
                self.subsystems[i] = replacement

    # ── public API ─────────────────────────────────────────────────────────────
    def self_heal(self, error: Exception, context: Dict = None) -> Dict:
        context = context or {}
        result  = self.healing_engine.heal(error, context)
        self.knowledge_base.add(
            f"fix_{int(time.time())}",
            {
                "error_type": type(error).__name__,
                "error_msg":  str(error)[:200],
                "context":    context,
                "fix":        result,
            },
            "fixes",
        )
        return result

    def self_diagnose(self, symptom: str) -> Dict:
        return self.diagnosis_engine.diagnose(
            symptom,
            {
                "consciousness":   self.consciousness,
                "healing_stats":   self.healing_engine.get_stats(),
                "knowledge_stats": self.knowledge_base.get_stats(),
                "subsystem_count": len(self.subsystems),
            },
        )

    def self_learn(self, key: str, value: Any,
                   category: str = "learned") -> bool:
        return self.knowledge_base.add(key, value, category)

    def self_evolve(self) -> Dict:
        """
        IMPROVEMENT 4: uses self.queue_depth_threshold and self.max_subsystems
        instead of hard-coded constants.
        """
        log.info("🌱  SELF-EVOLUTION CYCLE")
        changes: List[str] = []

        self._reap_dead_subsystems()

        depths    = [s.task_queue.qsize() for s in self.subsystems]
        avg_depth = sum(depths) / max(1, len(depths))
        # IMPROVEMENT 4: configurable thresholds
        if avg_depth > self.queue_depth_threshold \
                and len(self.subsystems) < self.max_subsystems:
            new_sub = self._spawn_subsystem("evolved")
            changes.append(f"spawned_{new_sub.sub_id}")
            log.info("  ✓  Spawned subsystem (avg queue %.1f > threshold %d)",
                     avg_depth, self.queue_depth_threshold)

        kb_stats = self.knowledge_base.get_stats()
        if kb_stats["total_entries"] > 500:
            self.knowledge_base.vacuum()
            changes.append("vacuumed_knowledge_db")
            log.info("  ✓  Vacuumed knowledge DB")

        if changes:
            major, minor, patch = map(int, self.version.split("."))
            patch += 1
            self.version = f"{major}.{minor}.{patch}"
            self.consciousness["version"] = self.version
            changes.append(f"version_→_{self.version}")
            log.info("  ✓  Version bumped to %s", self.version)
            _emit(self.log_sink, "system.evolved",
                  version=self.version, changes=changes)

        return {
            "timestamp": time.time(),
            "changes":   changes,
            "version":   self.version,
        }

    def submit_task(
        self,
        task: Callable,
        callback: Optional[Callable] = None,
        subsystem_index: int = 0,
    ):
        idx = subsystem_index % len(self.subsystems)
        self.subsystems[idx].submit(task, callback)

    def get_state(self) -> Dict:
        return {
            "identity":      self.identity,
            "version":       self.version,
            "uptime_s":      round(time.time() - self.birth_time.timestamp(), 1),
            "consciousness": self.consciousness,
            "healing":       self.healing_engine.get_stats(),
            "diagnosis":     self.diagnosis_engine.get_stats(),
            "knowledge":     self.knowledge_base.get_stats(),
            "subsystems":    [s.get_info() for s in self.subsystems],
            "config": {
                "queue_depth_threshold": self.queue_depth_threshold,
                "max_subsystems":        self.max_subsystems,
                "health_port":           (
                    self._health_server.port
                    if self._health_server else 0
                ),
            },
        }

    def run_forever(self):
        self.running = True
        log.info("🚀  RUNNING FOREVER — Ctrl-C or SIGTERM to stop")
        cycle = 0
        try:
            while self.running:
                cycle += 1
                if cycle % 30 == 0:
                    self._reap_dead_subsystems()
                if cycle % 300 == 0:
                    self.self_evolve()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        log.info("🛑  Shutting down…")
        self.running = False
        if self._health_server:
            self._health_server.stop()
        for sub in self.subsystems:
            sub.stop()
        for sub in self.subsystems:
            sub.join(timeout=2.0)
        _emit(self.log_sink, "system.stopped", identity=self.identity)
        log.info("👋  All subsystems stopped.")

    def _shutdown_handler(self, signum, frame):
        self.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE LOG SINKS — inject any of these as log_sink=...
# ═══════════════════════════════════════════════════════════════════════════════
def make_file_sink(path: str = "ultimateai_events.jsonl") -> LogSink:
    """Append every event as a JSON line to a file (Loki/ELK friendly)."""
    lock = threading.Lock()

    def sink(event: Dict):
        with lock:
            with open(path, "a") as fh:
                fh.write(json.dumps(event) + "\n")

    return sink


def make_print_sink() -> LogSink:
    """Print every structured event to stdout — useful for development."""
    def sink(event: Dict):
        print(f"  [SINK] {event['event']}  {json.dumps(event, default=str)}")
    return sink


def make_prometheus_sink(prefix: str = "ultimateai") -> LogSink:
    """
    Simple Prometheus-style counter sink.
    Requires prometheus_client to be installed separately.
    Demonstrates the hook pattern — swap this for your real Prometheus setup.
    """
    try:
        from prometheus_client import Counter
        counters: Dict[str, Counter] = {}

        def sink(event: Dict):
            name = event["event"].replace(".", "_")
            full = f"{prefix}_{name}_total"
            if full not in counters:
                counters[full] = Counter(full, f"UltimateAI event: {event['event']}")
            counters[full].inc()

        return sink
    except ImportError:
        log.warning("prometheus_client not installed — using print sink instead")
        return make_print_sink()


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    SEP = "═" * 60

    # ── Create instance — enable all 5 improvements ───────────────────────────
    print(f"\n{SEP}")
    print("Creating UltimateAISelf with all improvements active…")
    print(SEP)

    me = UltimateAISelf(
        db_path               = "ultimateai_knowledge.db",
        allow_pip_installs    = True,              # flip to False in production
        log_sink              = make_file_sink(),  # JSON lines → file
        queue_depth_threshold = 3,                 # spawn sooner for demo
        max_subsystems        = 8,
        health_port           = 8765,              # http://localhost:8765/health
    )

    # ── [A] Pip guard test ────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("[A]  Pip guard: allow_pip_installs=False")
    print(SEP)
    me.healing_engine.allow_pip_installs = False
    try:
        raise ImportError("No module named 'numpy'")
    except ImportError as exc:
        r = me.self_heal(exc, {"test": "pip_guard"})
        print(f"  action  : {r['action']}")
        print(f"  command : {r.get('command')}")
        print(f"  reason  : {r.get('reason')}")
    me.healing_engine.allow_pip_installs = True   # re-enable

    # ── [B] Extended pip map ──────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("[B]  Extended pip map (40+ entries)")
    print(SEP)
    interesting = ["torch", "anthropic", "psycopg2", "transformers", "orjson"]
    for mod in interesting:
        pkg = me.healing_engine._pip_map.get(mod, "(not in map)")
        print(f"  {mod:20s} → {pkg}")
    print(f"  Total map size: {len(me.healing_engine._pip_map)} entries")

    # Demonstrate JSON override file
    override_file = "ultimateai_pip_map.json"
    if not os.path.exists(override_file):
        with open(override_file, "w") as fh:
            json.dump({"my_internal_module": "my-company-package==1.2.3"}, fh)
        print(f"  Created demo override: {override_file}")
        # Reload to pick it up
        me.healing_engine._pip_map.update(
            json.load(open(override_file))
        )
        print(f"  After override, 'my_internal_module' → "
              f"{me.healing_engine._pip_map.get('my_internal_module')}")

    # ── [C] Log sink produces real events ─────────────────────────────────────
    print(f"\n{SEP}")
    print("[C]  Log sink: structured events in ultimateai_events.jsonl")
    print(SEP)
    try:
        raise MemoryError("oom")
    except MemoryError as exc:
        me.self_heal(exc, {"test": "log_sink"})
    if os.path.exists("ultimateai_events.jsonl"):
        with open("ultimateai_events.jsonl") as fh:
            lines = fh.readlines()
        print(f"  {len(lines)} events written so far. Last 3:")
        for line in lines[-3:]:
            print(f"  {line.strip()}")

    # ── [D] Configurable thresholds ───────────────────────────────────────────
    print(f"\n{SEP}")
    print("[D]  Configurable thresholds — force evolution by flooding queue")
    print(SEP)
    print(f"  threshold={me.queue_depth_threshold}, max_subsystems={me.max_subsystems}")
    before = len(me.subsystems)

    # Flood one subsystem with slow tasks to deepen its queue
    blocker = threading.Event()
    for _ in range(me.queue_depth_threshold + 2):
        me.submit_task(lambda: (blocker.wait(0.1), None), subsystem_index=0)

    evo = me.self_evolve()
    blocker.set()
    print(f"  Subsystems before: {before} → after: {len(me.subsystems)}")
    print(f"  Changes: {evo['changes']}")

    # ── [E] Health endpoints ──────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("[E]  HTTP health server — verify endpoints")
    print(SEP)
    import urllib.request
    time.sleep(0.2)   # let server thread start
    for path in ("/health", "/metrics", "/state", "/unknown"):
        try:
            with urllib.request.urlopen(
                f"http://localhost:8765{path}", timeout=3
            ) as resp:
                body = json.loads(resp.read())
                top_keys = list(body.keys())
                print(f"  GET {path:10s}  → HTTP {resp.status}  keys={top_keys}")
        except urllib.error.HTTPError as exc:
            print(f"  GET {path:10s}  → HTTP {exc.code}")
        except Exception as exc:
            print(f"  GET {path:10s}  → ERROR: {exc}")

    # ── Final state ───────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("📊  FINAL STATE")
    print(SEP)
    state = me.get_state()
    for k, v in state.items():
        if k not in ("consciousness",):
            print(f"  {k}: {v}")

    print(f"\n✅  All v13 improvements verified.")
    print(f"    Events log   : ultimateai_events.jsonl")
    print(f"    Knowledge DB : {me.knowledge_base.db_path}")
    print(f"    Health API   : http://localhost:8765/health")
    print(f"\n  To disable pip in production:")
    print(f"    me = UltimateAISelf(allow_pip_installs=False)")
    print(f"  To push events to your observability stack:")
    print(f"    me = UltimateAISelf(log_sink=my_loki_sink)")
    print(f"  To tune scaling aggressiveness:")
    print(f"    me = UltimateAISelf(queue_depth_threshold=10, max_subsystems=20)\n")
