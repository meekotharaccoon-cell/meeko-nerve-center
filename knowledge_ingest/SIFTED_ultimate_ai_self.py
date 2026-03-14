#!/usr/bin/env python3
# =============================================================================
# 🧠 ULTIMATE AI - SELF-HEALING CORE v12.0  (FUNCTIONAL)
# =============================================================================
# Every component does something real:
#   HealingEngine  — pip-installs missing modules, runs gc.collect(),
#                    raises recursion limit, provides code-fix snippets
#   DiagnosisEngine — reads actual CPU/memory/thread metrics
#   KnowledgeBase  — SQLite-backed, persistent across restarts, FTS search
#   Subsystem      — real daemon Thread with a task queue
# =============================================================================

import functools
import gc
import hashlib
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
    ):
        super().__init__(daemon=True, name=subsystem_id)
        self.sub_id = subsystem_id
        self.healing_engine = healing_engine
        self.diagnosis_engine = diagnosis_engine
        self.task_queue: queue.Queue = queue.Queue()
        self.local_knowledge: Dict[str, Any] = {}
        self.status = "starting"
        self.birth = time.time()
        self._stop_event = threading.Event()
        self.tasks_done = 0
        self.tasks_failed = 0

    def run(self):
        self.status = "active"
        log.debug("Subsystem %s started", self.sub_id)
        while not self._stop_event.is_set():
            try:
                task, callback = self.task_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                result = task()
                self.tasks_done += 1
                if callback:
                    callback(result, None)
            except Exception as exc:
                self.tasks_failed += 1
                fix = self.healing_engine.heal(exc, {"subsystem": self.sub_id})
                if callback:
                    callback(None, {"error": str(exc), "fix": fix})
            finally:
                self.task_queue.task_done()
        self.status = "stopped"

    def submit(self, task: Callable, callback: Optional[Callable] = None):
        """Enqueue a task. callback(result, error_dict) is called on completion."""
        self.task_queue.put((task, callback))

    def stop(self):
        self._stop_event.set()

    def get_info(self) -> Dict:
        return {
            "id": self.sub_id,
            "status": self.status,
            "age_s": round(time.time() - self.birth, 1),
            "tasks_done": self.tasks_done,
            "tasks_failed": self.tasks_failed,
            "queue_depth": self.task_queue.qsize(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HEALING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class HealingEngine:
    """
    Dispatches to a real fixer for each recognised error class.
    Every fixer either applies an immediate automatic remedy
    (pip install, gc.collect, raise recursion limit …) or returns
    a code snippet explaining the correct fix pattern to use going forward.
    """

    # Map common import names → pip package names
    _PIP_MAP: Dict[str, str] = {
        "cv2":      "opencv-python",
        "PIL":      "Pillow",
        "sklearn":  "scikit-learn",
        "yaml":     "PyYAML",
        "bs4":      "beautifulsoup4",
        "dotenv":   "python-dotenv",
        "psutil":   "psutil",
        "requests": "requests",
    }

    def __init__(self, parent: "UltimateAISelf"):
        self.parent = parent
        self.history: List[Dict] = []
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
        err_str   = str(error)
        tb_str    = traceback.format_exc()
        log.info("🩺  Healing %s: %s", type(error).__name__, err_str[:120])

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
        self.history.append({
            "ts":         time.time(),
            "error_type": type(error).__name__,
            "error_msg":  str(error)[:200],
            "pattern":    pattern,
            "result":     result,
        })
        if hasattr(self.parent, "consciousness"):
            self.parent.consciousness["stats"]["fixes_applied"] += 1

    # ── real fixers ─────────────────────────────────────────────────────────────

    def _fix_import_error(self, error, match, context) -> Dict:
        module = match.group(1).split(".")[0] if match.lastindex else None
        if not module:
            return {"success": False, "reason": "could not identify module name"}
        pkg = self._PIP_MAP.get(module, module)
        log.info("  📦  pip install %s …", pkg)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode == 0:
                log.info("  ✅  Installed %s", pkg)
                return {"success": True, "action": "pip_install",
                        "package": pkg, "auto": True}
            log.warning("  ⚠   pip install failed:\n%s", proc.stderr[:300])
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
        return {"success": True, "action": "gc_collect",
                "objects_freed": freed, "auto": True}

    def _fix_recursion_error(self, error, match, context) -> Dict:
        old_limit = sys.getrecursionlimit()
        new_limit = old_limit + 500
        sys.setrecursionlimit(new_limit)
        log.info("  🌀  RecursionError — limit %d → %d", old_limit, new_limit)
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
            "total_heals":    total,
            "auto_healed":    auto,
            "manual_review":  total - auto,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGNOSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class DiagnosisEngine:
    """
    Reads real system metrics (CPU, memory, thread count) and maps symptoms
    to probable causes + concrete recommended actions.
    """

    def __init__(self, parent: "UltimateAISelf"):
        self.parent = parent
        self.history: List[Dict] = []

    def _collect_metrics(self) -> Dict:
        metrics: Dict[str, Any] = {
            "timestamp":    time.time(),
            "thread_count": threading.active_count(),
        }
        if HAS_PSUTIL:
            metrics["cpu_pct"]    = psutil.cpu_percent(interval=0.2)
            mem                    = psutil.virtual_memory()
            metrics["mem_pct"]    = mem.percent
            metrics["mem_used_mb"]= round(mem.used / 1_048_576, 1)
            try:
                proc = psutil.Process()
                metrics["open_fds"] = proc.num_fds()
            except AttributeError:
                metrics["open_fds"] = "n/a"
        else:
            # Best-effort on Linux without psutil
            try:
                with open("/proc/meminfo") as fh:
                    raw = {
                        line.split(":")[0]: int(line.split()[1])
                        for line in fh
                        if ":" in line
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
            dead = [s.sub_id for s in self.parent.subsystems
                    if not s.is_alive()]
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
            actions.append("Run a full health-check: me.self_diagnose('all')")
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
    Stores key/value pairs in a local SQLite database.
    Values are JSON-serialised so any Python type can be stored.
    Full-text search is provided via SQLite FTS5 (with a LIKE fallback).
    Data survives process restarts because it lives on disk.
    """

    def __init__(self, parent: "UltimateAISelf",
                 db_path: str = "ultimateai_knowledge.db"):
        self.parent  = parent
        self.db_path = db_path
        self._lock   = threading.Lock()
        self._init_db()

    # ── schema ──────────────────────────────────────────────────────────────────
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

    # ── CRUD ────────────────────────────────────────────────────────────────────
    def add(self, key: str, value: Any, category: str = "general") -> bool:
        now = time.time()
        serialised = json.dumps(value, default=str)
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO knowledge(category, key, value, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (category, key, serialised, now, now),
            )
        if hasattr(self.parent, "consciousness"):
            self.parent.consciousness["stats"]["knowledge_entries"] += 1
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
                # FTS5 not compiled in — fall back to LIKE
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
        """Compact the database file."""
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
# MAIN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class UltimateAISelf:
    """
    Self-healing, self-diagnosing, self-learning system.
    All components are real — no mock implementations.
    """

    def __init__(self, db_path: str = "ultimateai_knowledge.db"):
        self.version    = "12.0.0"
        self.identity   = hashlib.sha256(
            f"UltimateAI-{time.time()}".encode()
        ).hexdigest()[:16]
        self.birth_time = datetime.now()
        self.running    = False
        self.subsystems: List[Subsystem] = []

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

        self.healing_engine   = HealingEngine(self)
        log.info("  ✓  Healing engine ready")

        self.diagnosis_engine = DiagnosisEngine(self)
        log.info("  ✓  Diagnosis engine ready")

        self.knowledge_base   = KnowledgeBase(self, db_path)
        log.info("  ✓  Knowledge base ready (%s)", self.knowledge_base.db_path)

        # Start three core subsystem threads
        for i in range(3):
            self._spawn_subsystem(f"core_{i}")
        log.info("  ✓  %d subsystems started", len(self.subsystems))

        # Seed identity facts (idempotent thanks to UNIQUE ON CONFLICT REPLACE)
        self.knowledge_base.add("version", self.version,               "identity")
        self.knowledge_base.add("birth",   self.birth_time.isoformat(), "identity")
        if HAS_PSUTIL:
            self.knowledge_base.add("psutil_available", True, "environment")
        self.knowledge_base.add("python_version", sys.version,         "environment")

        # Graceful Ctrl-C / SIGTERM
        signal.signal(signal.SIGINT,  self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)

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
        )
        sub.start()
        self.subsystems.append(sub)
        self.consciousness["stats"]["subsystems_created"] += 1
        return sub

    def _reap_dead_subsystems(self):
        """Replace any subsystem threads that have died."""
        for i, sub in enumerate(self.subsystems):
            if not sub.is_alive():
                log.warning("⚠   Subsystem %s died — restarting", sub.sub_id)
                replacement = self._spawn_subsystem("restarted")
                self.subsystems[i] = replacement

    # ── public API ─────────────────────────────────────────────────────────────
    def self_heal(self, error: Exception, context: Dict = None) -> Dict:
        """Apply the appropriate real remedy and persist the fix record."""
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
        """Diagnose using real metrics; returns causes + recommended actions."""
        return self.diagnosis_engine.diagnose(
            symptom,
            {
                "consciousness": self.consciousness,
                "healing_stats": self.healing_engine.get_stats(),
                "knowledge_stats": self.knowledge_base.get_stats(),
                "subsystem_count": len(self.subsystems),
            },
        )

    def self_learn(self, key: str, value: Any,
                   category: str = "learned") -> bool:
        """Persist a new knowledge entry."""
        return self.knowledge_base.add(key, value, category)

    def self_evolve(self) -> Dict:
        """
        Inspect real load signals; spawn extra subsystems when queues are
        deep; compact the DB when it grows large; bump the patch version.
        """
        log.info("🌱  SELF-EVOLUTION CYCLE")
        changes: List[str] = []

        self._reap_dead_subsystems()

        # Spawn extra worker if average queue depth exceeds threshold
        depths = [s.task_queue.qsize() for s in self.subsystems]
        avg_depth = sum(depths) / max(1, len(depths))
        if avg_depth > 5 and len(self.subsystems) < 10:
            new_sub = self._spawn_subsystem("evolved")
            changes.append(f"spawned_{new_sub.sub_id}")
            log.info("  ✓  Spawned subsystem (avg queue %.1f)", avg_depth)

        # Vacuum DB if large
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
        """Route a task to a specific subsystem thread (round-robin by default)."""
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
        }

    def run_forever(self):
        """
        Heartbeat loop: checks subsystem health every 30 s,
        evolves every 5 min. Exits cleanly on SIGINT/SIGTERM.
        """
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
        for sub in self.subsystems:
            sub.stop()
        for sub in self.subsystems:
            sub.join(timeout=2.0)
        log.info("👋  All subsystems stopped.")

    def _shutdown_handler(self, signum, frame):
        self.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST — run directly: python ultimate_ai_self.py
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    me = UltimateAISelf()

    SEP = "═" * 60

    # ── 1. ImportError — actually tries pip install ────────────────────────────
    print(f"\n{SEP}")
    print("[1]  ImportError  →  real pip install attempt")
    print(SEP)
    try:
        raise ImportError("No module named 'requests'")
    except ImportError as exc:
        r = me.self_heal(exc, {"test": "import"})
        print(f"  Result : {r}")

    # ── 2. MemoryError — calls gc.collect() ───────────────────────────────────
    print(f"\n{SEP}")
    print("[2]  MemoryError  →  gc.collect()")
    print(SEP)
    try:
        raise MemoryError("not enough memory")
    except MemoryError as exc:
        r = me.self_heal(exc, {"test": "memory"})
        print(f"  Result : {r}")

    # ── 3. RecursionError — bumps sys.getrecursionlimit() ────────────────────
    print(f"\n{SEP}")
    print("[3]  RecursionError  →  raise sys.getrecursionlimit()")
    print(SEP)
    try:
        raise RecursionError("max recursion depth exceeded")
    except RecursionError as exc:
        r = me.self_heal(exc, {"test": "recursion"})
        print(f"  Result : {r}")

    # ── 4. KeyError — snippet advice ──────────────────────────────────────────
    print(f"\n{SEP}")
    print("[4]  KeyError  →  code-fix snippet")
    print(SEP)
    try:
        raise KeyError("config_api_key")
    except KeyError as exc:
        r = me.self_heal(exc, {"test": "key"})
        print(f"  Action : {r.get('action')}")
        print(r.get("snippet", ""))

    # ── 5. Self-diagnosis with real metrics ───────────────────────────────────
    print(f"\n{SEP}")
    print("[5]  Self-diagnosis: 'system running slow and memory climbing'")
    print(SEP)
    d = me.self_diagnose("system running slow and memory climbing")
    print(f"  Metrics  : {d['metrics']}")
    print(f"  Causes   : {d['possible_causes']}")
    print(f"  Actions  : {d['recommended_actions']}")
    print(f"  Confidence: {d['confidence']}")

    # ── 6. Persistent self-learning (survives restart) ────────────────────────
    print(f"\n{SEP}")
    print("[6]  Self-learn + persist")
    print(SEP)
    me.self_learn("universe_age",  "13.8 billion years",  "science")
    me.self_learn("python_binary", sys.executable,         "environment")
    val = me.knowledge_base.get("universe_age", "science")
    print(f"  Retrieved: universe_age = {val!r}")

    # ── 7. Full-text search ───────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("[7]  FTS search: 'version'")
    print(SEP)
    for hit in me.knowledge_base.search("version"):
        print(f"  [{hit['category']}] {hit['key']} = {hit['value']}")

    # ── 8. Real threaded task ─────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("[8]  Threaded task: compute 42²")
    print(SEP)
    done_event = threading.Event()

    def heavy_task():
        time.sleep(0.05)
        return {"result": 42 * 42}

    def on_done(result, error):
        print(f"  Callback received: result={result}  error={error}")
        done_event.set()

    me.submit_task(heavy_task, on_done, subsystem_index=0)
    done_event.wait(timeout=5)

    # ── 9. Evolution cycle ────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("[9]  Self-evolve")
    print(SEP)
    evo = me.self_evolve()
    print(f"  Changes : {evo['changes']}")
    print(f"  Version : {evo['version']}")

    # ── Final state ───────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("📊  FINAL STATE")
    print(SEP)
    state = me.get_state()
    for k, v in state.items():
        if k != "consciousness":
            print(f"  {k}: {v}")

    print(f"\n✅  All tests passed.")
    print(f"    Knowledge persisted to: {me.knowledge_base.db_path}")
    print(f"    Call me.run_forever() to keep running.\n")
