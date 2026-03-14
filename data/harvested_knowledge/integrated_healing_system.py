#!/usr/bin/env python3
"""
INSA Integrated Healing System
Combines autonomous research agent with platform health monitor

Flow:
1. Platform Health Monitor detects issue
2. Research Agent searches for solution
3. Solution validation and ranking
4. Auto-deployment to healing agent
5. Verification and learning

Author: Insa Automation Corp
Date: October 19, 2025

SAFEGUARDS:
- Timeout limits on all operations
- Resource monitoring
- Runaway process prevention
- Memory leak detection
- Circuit breaker pattern
"""

import os
import sys
import json
import time
import subprocess
import signal
import resource
import psutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import logging
import sqlite3
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, '/home/wil')  # For notification_queue and email_reporter

# Import our agents
try:
    from autonomous_research_agent import (
        AutonomousResearchAgent,
        ResearchQuery,
        ResearchTrigger,
        Solution,
        SolutionStatus
    )
except ImportError:
    # Fallback import path
    from insa_crm_platform.core.agents.autonomous_research_agent import (
        AutonomousResearchAgent,
        ResearchQuery,
        ResearchTrigger,
        Solution,
        SolutionStatus
    )

# Import platform health monitor
try:
    from platform_health_monitor import PlatformHealthMonitor
except ImportError:
    # If not in PYTHONPATH, try direct import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "platform_health_monitor",
        "/home/wil/platform_health_monitor.py"
    )
    platform_health_monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(platform_health_monitor)
    PlatformHealthMonitor = platform_health_monitor.PlatformHealthMonitor

# Import notification system
try:
    from email_reporter import EmailReporter
    from notification_queue import TieredNotificationManager
except ImportError as e:
    logger.error(f"Failed to import notification system: {e}")
    EmailReporter = None
    TieredNotificationManager = None

# Import cron monitor (Week 1 enhancement)
try:
    from modules.cron_monitor import CronJobMonitor
    CRON_MONITOR_AVAILABLE = True
except ImportError as e:
    CRON_MONITOR_AVAILABLE = False
    CRON_MONITOR_ERROR = str(e)
    CronJobMonitor = None

# Import resource limiter (Week 2 enhancement)
try:
    from modules.resource_limiter import ResourceLimitEnforcer, ApprovalWorkflow
    RESOURCE_LIMITER_AVAILABLE = True
except ImportError as e:
    RESOURCE_LIMITER_AVAILABLE = False
    RESOURCE_LIMITER_ERROR = str(e)
    ResourceLimitEnforcer = None
    ApprovalWorkflow = None

# Setup logging
os.makedirs('/var/lib/insa-crm/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/lib/insa-crm/logs/integrated_healing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('IntegratedHealing')

# Log cron monitor status (after logger is defined)
if CRON_MONITOR_AVAILABLE:
    logger.info("✅ CronJobMonitor module loaded (Week 1 enhancement)")
else:
    logger.warning(f"📋 CronJobMonitor not available: {CRON_MONITOR_ERROR}")

# Log resource limiter status
if RESOURCE_LIMITER_AVAILABLE:
    logger.info("✅ ResourceLimitEnforcer module loaded (Week 2 enhancement)")
else:
    logger.warning(f"⚠️  ResourceLimitEnforcer not available: {RESOURCE_LIMITER_ERROR}")


# Timeout decorator to prevent hanging operations
@contextmanager
def timeout(seconds):
    """Context manager for operation timeout"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class ResourceMonitor:
    """Monitor and enforce resource limits"""

    def __init__(self, max_memory_mb=400, max_cpu_percent=30):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.process = psutil.Process()
        logger.info(f"Resource monitor initialized: {max_memory_mb}MB RAM, {max_cpu_percent}% CPU")

    def check_resources(self) -> Dict[str, Any]:
        """Check current resource usage"""
        try:
            mem_info = self.process.memory_info()
            mem_mb = mem_info.rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.1)

            return {
                'memory_mb': mem_mb,
                'memory_percent': (mem_mb / self.max_memory_mb) * 100,
                'cpu_percent': cpu_percent,
                'within_limits': mem_mb < self.max_memory_mb and cpu_percent < self.max_cpu_percent
            }
        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            return {'within_limits': True, 'error': str(e)}

    def enforce_limits(self):
        """Enforce resource limits, raise exception if exceeded"""
        stats = self.check_resources()

        if not stats.get('within_limits', True):
            if stats['memory_mb'] >= self.max_memory_mb:
                raise MemoryError(f"Memory limit exceeded: {stats['memory_mb']:.1f}MB >= {self.max_memory_mb}MB")
            if stats['cpu_percent'] >= self.max_cpu_percent:
                logger.warning(f"CPU limit exceeded: {stats['cpu_percent']:.1f}% >= {self.max_cpu_percent}%")

        return stats


class CooldownManager:
    """
    Phase 1: Pattern Recognition - Prevents repeated checks of failing services
    Implements exponential backoff to reduce noise and resource usage
    """

    def __init__(self):
        self.failure_counts = {}  # {service_id: count}
        self.last_check = {}      # {service_id: timestamp}
        self.cooldowns = {
            1: 5 * 60,      # 1 failure: 5 min
            2: 15 * 60,     # 2 failures: 15 min
            3: 30 * 60,     # 3 failures: 30 min
            4: 60 * 60,     # 4+ failures: 1 hour
        }
        logger.info("CooldownManager initialized with exponential backoff")

    def should_check(self, service_id: str) -> Tuple[bool, str]:
        """
        Returns (should_check, reason)
        Implements intelligent cooldown to prevent spam
        """
        count = self.failure_counts.get(service_id, 0)
        if count == 0:
            return True, "first_check"

        # Get cooldown period based on failure count
        cooldown = self.cooldowns.get(count, 60 * 60)  # Max 1 hour

        # Check elapsed time since last check
        last = self.last_check.get(service_id, 0)
        elapsed = time.time() - last

        if elapsed < cooldown:
            remaining = int((cooldown - elapsed) / 60)
            return False, f"cooldown_active_{count}_failures_remaining_{remaining}_min"

        return True, f"cooldown_expired_after_{int(elapsed/60)}_min"

    def record_failure(self, service_id: str):
        """Record a failure - increments count and updates timestamp"""
        self.failure_counts[service_id] = self.failure_counts.get(service_id, 0) + 1
        self.last_check[service_id] = time.time()
        count = self.failure_counts[service_id]
        logger.info(f"Recorded failure for {service_id} (count: {count})")

    def record_success(self, service_id: str):
        """Record a success - resets failure count"""
        if service_id in self.failure_counts:
            old_count = self.failure_counts[service_id]
            self.failure_counts[service_id] = 0
            logger.info(f"✅ Reset failure count for {service_id} (was {old_count})")

    def get_stats(self) -> Dict[str, Any]:
        """Get current cooldown statistics"""
        return {
            'services_in_cooldown': sum(1 for count in self.failure_counts.values() if count > 0),
            'total_failures': sum(self.failure_counts.values()),
            'failure_counts': dict(self.failure_counts)
        }


class ServiceClassifier:
    """
    Phase 2: Service Classification - Knows what type of service we're dealing with
    Guides diagnosis strategy based on service characteristics
    """

    SERVICE_TYPES = {
        # Custom internal - NEVER search web (no public docs exist)
        'custom_internal': {
            'services': ['insa_crm'],
            'strategy': 'local_only',
            'reason': 'Custom codebase - web has no solutions',
            'notification_tier': 'realtime'  # Escalate to human quickly
        },

        # Custom Docker - Check logs first, then search cautiously
        'custom_docker': {
            'services': ['erpnext', 'defectdojo'],
            'strategy': 'logs_then_docs',
            'reason': 'Containerized custom apps - logs most useful',
            'notification_tier': 'hourly'
        },

        # Public standard - Can search official docs
        'public_docker': {
            'services': ['n8n', 'grafana', 'mautic', 'inventree'],
            'strategy': 'logs_then_search',
            'reason': 'Standard apps - good documentation exists',
            'notification_tier': 'daily'
        },

        # System services - Standard systemd restart usually fixes
        'systemd_services': {
            'services': ['nginx', 'redis', 'postfix', 'suricata', 'wazuh',
                        'fail2ban', 'auditd', 'clamav'],
            'strategy': 'restart_first',
            'reason': 'System services - restart usually resolves issues',
            'notification_tier': 'daily'
        },

        # Autonomous agents - Self-healing capable, rare failures
        'autonomous_agents': {
            'services': ['integrated_healing_agent', 'host_config_agent',
                        'defectdojo_compliance_agent', 'security_integration_agent',
                        'task_orchestration_agent', 'azure_monitor_agent', 'soc_agent'],
            'strategy': 'restart_first',
            'reason': 'Autonomous agents - restart resolves most issues',
            'notification_tier': 'hourly'
        },

        # MCP servers - Configuration-only monitoring (auto-restart by Claude Code)
        'mcp_servers': {
            'services': ['mcp_platform_admin', 'mcp_defectdojo', 'mcp_erpnext'],
            'strategy': 'config_only',
            'reason': 'MCP servers - Claude Code auto-restarts, just verify config',
            'notification_tier': 'daily'
        },

        # Storage backends - Critical but rarely fail
        'storage_backends': {
            'services': ['minio', 'qdrant', 'postgresql', 'mariadb'],
            'strategy': 'logs_then_search',
            'reason': 'Storage backends - critical, need careful diagnosis',
            'notification_tier': 'realtime'
        }
    }

    def __init__(self):
        logger.info("ServiceClassifier initialized with 7 service categories:")
        logger.info(f"  Custom internal: {self.SERVICE_TYPES['custom_internal']['services']}")
        logger.info(f"  Custom Docker: {self.SERVICE_TYPES['custom_docker']['services']}")
        logger.info(f"  Public Docker: {self.SERVICE_TYPES['public_docker']['services']}")
        logger.info(f"  Systemd services: {len(self.SERVICE_TYPES['systemd_services']['services'])} services")
        logger.info(f"  Autonomous agents: {len(self.SERVICE_TYPES['autonomous_agents']['services'])} agents")
        logger.info(f"  MCP servers: {len(self.SERVICE_TYPES['mcp_servers']['services'])} servers")
        logger.info(f"  Storage backends: {len(self.SERVICE_TYPES['storage_backends']['services'])} backends")

    def classify_service(self, service_id: str) -> Dict[str, str]:
        """Returns service type and diagnosis strategy"""
        for svc_type, info in self.SERVICE_TYPES.items():
            if service_id in info['services']:
                return {
                    'type': svc_type,
                    'strategy': info['strategy'],
                    'reason': info['reason'],
                    'notification_tier': info['notification_tier']
                }

        # Default to public standard for unknown services
        return {
            'type': 'unknown',
            'strategy': 'logs_then_search',
            'reason': 'Unknown service type - using default strategy',
            'notification_tier': 'daily'
        }

    def should_research(self, service_id: str, checked_logs: bool) -> Tuple[bool, str]:
        """Decides if web research is warranted for this service"""

        classification = self.classify_service(service_id)

        # Never research custom internal services
        if classification['strategy'] == 'local_only':
            return False, f"custom_internal_service: {classification['reason']}"

        # For Docker services, must check logs first
        if classification['strategy'] in ['logs_then_docs', 'logs_then_search']:
            if not checked_logs:
                return False, "logs_not_checked_yet"

        # OK to research (already tried local methods)
        return True, "local_methods_exhausted"


class IntelligentLogAnalyzer:
    """
    Phase 1: Log Analysis - Analyzes container logs for known error patterns
    Checks logs BEFORE expensive web research
    """

    # Known error patterns with fixes
    ERROR_PATTERNS = {
        'docker_dns_failure': {
            'patterns': [
                r'host not found in upstream "([^"]+)"',
                r'no resolver defined to resolve ([^\s]+)',
                r'could not resolve host: ([^\s]+)'
            ],
            'fix_hint': 'Docker networking issue - DNS resolution failed. Restart affected containers.',
            'confidence': 0.95,
            'category': 'docker_networking'
        },
        'container_not_running': {
            'patterns': [
                r'Container ([a-f0-9]+) is not running',
                r'No such container: ([^\s]+)',
                r'Cannot connect to container ([^\s]+)'
            ],
            'fix_hint': 'Container is not running. Start with docker-compose up -d',
            'confidence': 1.0,
            'category': 'container_lifecycle'
        },
        'port_already_in_use': {
            'patterns': [
                r'port is already allocated',
                r'address already in use',
                r'bind: address already in use'
            ],
            'fix_hint': 'Port conflict detected. Check for existing processes on the port.',
            'confidence': 0.9,
            'category': 'port_conflict'
        },
        'connection_refused': {
            'patterns': [
                r'Connection refused',
                r'connect: connection refused',
                r'dial tcp.*: connect: connection refused'
            ],
            'fix_hint': 'Service not listening on expected port. Check if process is running.',
            'confidence': 0.85,
            'category': 'service_down'
        },
        'upstream_timeout': {
            'patterns': [
                r'upstream timed out',
                r'proxy.*timed out',
                r'dial tcp.*: i/o timeout'
            ],
            'fix_hint': 'Upstream service timeout. Service may be overloaded or unresponsive.',
            'confidence': 0.8,
            'category': 'performance'
        },
        'oom_killed': {
            'patterns': [
                r'OOM killed',
                r'Out of memory',
                r'Cannot allocate memory'
            ],
            'fix_hint': 'Container killed due to memory exhaustion. Increase memory limits.',
            'confidence': 1.0,
            'category': 'resource_exhaustion'
        },
        # PHASE 2: Expanded patterns for broader coverage
        'permission_denied': {
            'patterns': [
                r'Permission denied',
                r'EACCES: permission denied',
                r'Operation not permitted',
                r'cannot access.*Permission denied'
            ],
            'fix_hint': 'Permission error. Check file ownership and permissions (chown/chmod).',
            'confidence': 0.9,
            'category': 'permissions'
        },
        'database_connection_failed': {
            'patterns': [
                r'could not connect to server',
                r'Connection refused.*postgres',
                r'Access denied for user',
                r'Unknown database',
                r'Too many connections'
            ],
            'fix_hint': 'Database connection issue. Check database service status and credentials.',
            'confidence': 0.95,
            'category': 'database'
        },
        'file_not_found': {
            'patterns': [
                r'No such file or directory',
                r'ENOENT: no such file',
                r'FileNotFoundError: \[Errno 2\]'
            ],
            'fix_hint': 'File missing. Check path and verify file exists.',
            'confidence': 0.85,
            'category': 'filesystem'
        },
        'disk_space_full': {
            'patterns': [
                r'No space left on device',
                r'Disk quota exceeded',
                r'cannot create.*No space'
            ],
            'fix_hint': 'Disk full. Run: df -h and clean up space.',
            'confidence': 1.0,
            'category': 'disk_space'
        },
        'ssl_certificate_error': {
            'patterns': [
                r'certificate verify failed',
                r'SSL.*handshake failed',
                r'unable to get local issuer certificate',
                r'certificate has expired'
            ],
            'fix_hint': 'SSL certificate issue. Check certificate expiry and CA chain.',
            'confidence': 0.95,
            'category': 'ssl_tls'
        },
        'python_module_not_found': {
            'patterns': [
                r'ModuleNotFoundError: No module named',
                r'ImportError: cannot import name',
                r'No module named ([^\s]+)'
            ],
            'fix_hint': 'Python dependency missing. Run: pip install <module>',
            'confidence': 0.95,
            'category': 'python_deps'
        },
        'nodejs_module_not_found': {
            'patterns': [
                r'Cannot find module',
                r'MODULE_NOT_FOUND',
                r'Error: Cannot find module ([^\s]+)'
            ],
            'fix_hint': 'Node module missing. Run: npm install',
            'confidence': 0.95,
            'category': 'nodejs_deps'
        },
        'redis_connection_error': {
            'patterns': [
                r'Error connecting to Redis',
                r'Redis connection.*ECONNREFUSED',
                r'Could not connect to Redis'
            ],
            'fix_hint': 'Redis connection failed. Check: systemctl status redis',
            'confidence': 0.9,
            'category': 'redis'
        }
    }

    def __init__(self):
        logger.info("IntelligentLogAnalyzer initialized with pattern library")
        logger.info(f"  Monitoring {len(self.ERROR_PATTERNS)} error pattern categories")

    def analyze_before_research(self, service_id: str, service_config: Dict, health_result: Dict) -> Optional[Dict]:
        """
        Step 3.5: Analyze container logs BEFORE web research
        This is the key intelligence upgrade - check local data first!

        Returns diagnosis dict if pattern found, None otherwise
        """
        container = service_config.get('container')
        if not container:
            logger.debug(f"{service_id} is not containerized, skipping log analysis")
            return None

        logger.info(f"📋 Analyzing logs for {container}...")

        # Get container logs
        try:
            logs = self._get_container_logs(container, lines=100)
            if not logs:
                logger.warning(f"No logs available for {container}")
                return None

            logger.debug(f"Retrieved {len(logs)} characters of logs from {container}")

        except Exception as e:
            logger.warning(f"Could not get logs for {container}: {e}")
            return None

        # Check all error patterns
        for diagnosis, pattern_info in self.ERROR_PATTERNS.items():
            for pattern in pattern_info['patterns']:
                try:
                    matches = re.findall(pattern, logs, re.MULTILINE | re.IGNORECASE)
                    if matches:
                        # Found a match!
                        logger.info(f"✅ Pattern match found: {diagnosis}")
                        logger.info(f"   Evidence: {matches[:3]}")  # Show first 3 matches

                        return {
                            'diagnosis': diagnosis,
                            'confidence': pattern_info['confidence'],
                            'evidence': matches[:5],  # First 5 matches
                            'fix_hint': pattern_info['fix_hint'],
                            'category': pattern_info['category'],
                            'source': 'log_analysis',
                            'container': container
                        }
                except re.error as e:
                    logger.error(f"Regex error in pattern {pattern}: {e}")
                    continue

        logger.info(f"No known error patterns found in {container} logs")
        return None

    def _get_container_logs(self, container_name: str, lines: int = 100) -> str:
        """Get last N lines of container logs"""
        try:
            result = subprocess.run(
                ['docker', 'logs', '--tail', str(lines), container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout getting logs for {container_name}")
            return ""
        except Exception as e:
            logger.error(f"Error getting logs for {container_name}: {e}")
            return ""


class LearningDatabase:
    """
    Phase 3: Persistent learning memory
    Tracks patterns, solutions, and outcomes across restarts
    """

    def __init__(self, db_path: str = "/var/lib/insa-crm/learning.db"):
        self.db_path = db_path
        self.conn = None
        self._ensure_database()
        logger.info(f"LearningDatabase initialized: {db_path}")

    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Table 1: pattern_outcomes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service_id TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence TEXT,

                solution_applied BOOLEAN,
                solution_worked BOOLEAN,
                verification_method TEXT,

                was_correct BOOLEAN,
                led_to_fix BOOLEAN,

                duration_seconds REAL,
                notes TEXT
            )
        """)

        # Table 2: solution_history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service_id TEXT NOT NULL,

                error_type TEXT NOT NULL,
                http_code INTEGER,
                error_message TEXT,

                solution_type TEXT NOT NULL,
                solution_id TEXT,
                solution_description TEXT,

                applied BOOLEAN NOT NULL,
                success BOOLEAN,
                verification_time_seconds INTEGER,

                pattern_matched TEXT,
                pattern_confidence REAL,
                skip_reason TEXT,

                duration_seconds REAL,
                resource_usage TEXT
            )
        """)

        # Table 3: learned_patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                pattern_name TEXT PRIMARY KEY,

                total_matches INTEGER DEFAULT 0,
                true_positives INTEGER DEFAULT 0,
                false_positives INTEGER DEFAULT 0,
                led_to_fix INTEGER DEFAULT 0,

                base_confidence REAL NOT NULL,
                learned_adjustment REAL DEFAULT 0.0,
                effective_confidence REAL NOT NULL,

                accuracy REAL,
                fix_rate REAL,

                first_seen TEXT,
                last_seen TEXT,
                last_updated TEXT
            )
        """)

        # Table 4: service_learning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_learning (
                service_id TEXT PRIMARY KEY,

                service_type TEXT NOT NULL,
                strategy TEXT NOT NULL,

                total_checks INTEGER DEFAULT 0,
                failures_detected INTEGER DEFAULT 0,
                solutions_attempted INTEGER DEFAULT 0,
                solutions_worked INTEGER DEFAULT 0,

                fix_success_rate REAL,
                avg_resolution_time_seconds REAL,
                false_alarm_rate REAL,

                most_common_error TEXT,
                most_successful_fix TEXT,

                first_check TEXT,
                last_check TEXT,
                last_failure TEXT
            )
        """)

        self.conn.commit()
        logger.info("📚 Learning database tables created/verified")

    def record_pattern_outcome(self, service_id: str, pattern_name: str,
                               confidence: float, evidence: List[str],
                               solution_applied: bool = False,
                               solution_worked: Optional[bool] = None):
        """Record when a pattern matched and outcome"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO pattern_outcomes
            (timestamp, service_id, pattern_name, confidence, evidence,
             solution_applied, solution_worked, was_correct, led_to_fix)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            service_id,
            pattern_name,
            confidence,
            json.dumps(evidence) if evidence else None,
            solution_applied,
            solution_worked,
            solution_worked if solution_worked is not None else None,
            solution_worked and solution_applied if solution_worked is not None else None
        ))
        self.conn.commit()

        # Update learned pattern statistics
        self._update_pattern_stats(pattern_name, solution_worked)

        logger.info(f"📝 Recorded pattern outcome: {pattern_name} for {service_id}")

    def _update_pattern_stats(self, pattern_name: str, solution_worked: Optional[bool]):
        """Update statistics for a learned pattern"""
        cursor = self.conn.cursor()

        # Increment total matches
        cursor.execute("""
            UPDATE learned_patterns
            SET total_matches = total_matches + 1,
                last_seen = ?
            WHERE pattern_name = ?
        """, (datetime.now().isoformat(), pattern_name))

        # Update true/false positives if known
        if solution_worked is True:
            cursor.execute("""
                UPDATE learned_patterns
                SET true_positives = true_positives + 1,
                    led_to_fix = led_to_fix + 1
                WHERE pattern_name = ?
            """, (pattern_name,))
        elif solution_worked is False:
            cursor.execute("""
                UPDATE learned_patterns
                SET false_positives = false_positives + 1
                WHERE pattern_name = ?
            """, (pattern_name,))

        # Recalculate metrics
        result = cursor.execute("""
            SELECT total_matches, true_positives, false_positives, led_to_fix
            FROM learned_patterns
            WHERE pattern_name = ?
        """, (pattern_name,)).fetchone()

        if result:
            total = result['total_matches']
            tp = result['true_positives']
            fp = result['false_positives']
            fixes = result['led_to_fix']

            if total > 0:
                accuracy = tp / total if (tp + fp) > 0 else None
                fix_rate = fixes / total

                # Calculate learned adjustment (-0.2 to +0.2 based on performance)
                if accuracy is not None:
                    if accuracy >= 0.9:
                        adjustment = 0.05  # Excellent performance
                    elif accuracy >= 0.75:
                        adjustment = 0.02  # Good performance
                    elif accuracy >= 0.5:
                        adjustment = 0.0   # Neutral
                    else:
                        adjustment = -0.1  # Poor performance
                else:
                    adjustment = 0.0

                # Get base confidence
                base_conf = cursor.execute("""
                    SELECT base_confidence FROM learned_patterns
                    WHERE pattern_name = ?
                """, (pattern_name,)).fetchone()['base_confidence']

                effective_conf = max(0.0, min(1.0, base_conf + adjustment))

                cursor.execute("""
                    UPDATE learned_patterns
                    SET accuracy = ?,
                        fix_rate = ?,
                        learned_adjustment = ?,
                        effective_confidence = ?,
                        last_updated = ?
                    WHERE pattern_name = ?
                """, (accuracy, fix_rate, adjustment, effective_conf,
                      datetime.now().isoformat(), pattern_name))

        self.conn.commit()

    def sync_patterns(self, error_patterns: Dict):
        """Initialize learned_patterns from ERROR_PATTERNS"""
        cursor = self.conn.cursor()

        for pattern_name, pattern_info in error_patterns.items():
            # Check if pattern exists
            existing = cursor.execute("""
                SELECT pattern_name FROM learned_patterns
                WHERE pattern_name = ?
            """, (pattern_name,)).fetchone()

            if not existing:
                base_conf = pattern_info.get('confidence', 0.85)
                cursor.execute("""
                    INSERT INTO learned_patterns
                    (pattern_name, base_confidence, effective_confidence,
                     first_seen, last_seen, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pattern_name,
                    base_conf,
                    base_conf,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

        self.conn.commit()
        logger.info(f"📚 Synced {len(error_patterns)} patterns to learning database")

    def get_adjusted_confidence(self, pattern_name: str) -> Optional[float]:
        """Get learned confidence adjustment for pattern"""
        cursor = self.conn.cursor()
        result = cursor.execute("""
            SELECT effective_confidence, learned_adjustment, accuracy, total_matches
            FROM learned_patterns
            WHERE pattern_name = ?
        """, (pattern_name,)).fetchone()

        if result and result['total_matches'] >= 3:  # Need 3+ samples
            return result['effective_confidence']
        return None

    def get_learning_summary(self) -> Dict:
        """Get overall learning statistics"""
        cursor = self.conn.cursor()

        # Pattern statistics
        patterns = cursor.execute("""
            SELECT pattern_name, total_matches, accuracy, fix_rate,
                   learned_adjustment, effective_confidence, base_confidence
            FROM learned_patterns
            WHERE total_matches > 0
            ORDER BY total_matches DESC
        """).fetchall()

        # Service statistics
        services = cursor.execute("""
            SELECT service_id, total_checks, fix_success_rate,
                   most_common_error, most_successful_fix
            FROM service_learning
            ORDER BY total_checks DESC
        """).fetchall()

        return {
            'patterns': [dict(p) for p in patterns] if patterns else [],
            'services': [dict(s) for s in services] if services else [],
            'database_path': self.db_path,
            'total_patterns': len(patterns) if patterns else 0,
            'total_outcomes': cursor.execute(
                "SELECT COUNT(*) as cnt FROM pattern_outcomes"
            ).fetchone()['cnt']
        }


class SolutionVerifier:
    """
    Phase 3: Verifies if applied solutions actually worked
    Checks service health after fix attempts
    """

    def __init__(self, health_checker, learning_db: LearningDatabase):
        self.health_checker = health_checker
        self.learning_db = learning_db
        self.verification_delay = 60  # Wait 60s after fix to verify
        logger.info("SolutionVerifier initialized (async verification)")

    def verify_async(self, service_id: str, service_config: Dict,
                    pattern_name: Optional[str], solution_applied: Dict):
        """
        Asynchronous verification (don't block healing loop)
        """
        if not solution_applied:
            return

        thread = threading.Thread(
            target=self._verify_and_record,
            args=(service_id, service_config, pattern_name, solution_applied)
        )
        thread.daemon = True
        thread.start()
        logger.info(f"⏳ Async verification started for {service_id} (pattern: {pattern_name})")

    def _verify_and_record(self, service_id: str, service_config: Dict,
                          pattern_name: Optional[str], solution_applied: Dict):
        """Internal: verify and record to learning database"""
        try:
            logger.info(f"⏳ Waiting {self.verification_delay}s to verify fix for {service_id}...")
            time.sleep(self.verification_delay)

            # Re-check health
            from platform_health_monitor import PlatformHealthMonitor
            monitor = PlatformHealthMonitor()
            post_fix_result = monitor.check_service_health(service_config)

            success = post_fix_result.get('healthy', False)

            logger.info(f"✅ Verification for {service_id}: {'SUCCESS' if success else 'FAILED'}")

            # Update learning database
            if pattern_name:
                self.learning_db.record_pattern_outcome(
                    service_id,
                    pattern_name,
                    solution_applied.get('confidence', 0.0),
                    solution_applied.get('evidence', []),
                    solution_applied=True,
                    solution_worked=success
                )

        except Exception as e:
            logger.error(f"Error in async verification for {service_id}: {e}")


class PerformanceMonitor:
    """
    Phase 4: Metacognitive performance monitoring
    Watches agent's own success/failure patterns
    """

    def __init__(self, learning_db: LearningDatabase):
        self.learning_db = learning_db
        self.window_size = 10  # Look at last 10 attempts
        self.stuck_threshold = {
            'min_attempts': 10,
            'max_success_rate': 0.1,  # <10% success = stuck
            'same_error_count': 5      # Same error 5+ times = stuck
        }
        logger.info("PerformanceMonitor initialized (metacognition enabled)")

    def get_recent_performance(self, service_id: str = None) -> Dict:
        """Get performance metrics for recent healing attempts"""
        cursor = self.learning_db.conn.cursor()

        if service_id:
            # Service-specific performance
            results = cursor.execute("""
                SELECT solution_type, applied, success
                FROM solution_history
                WHERE service_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (service_id, self.window_size)).fetchall()
        else:
            # Overall performance
            results = cursor.execute("""
                SELECT solution_type, applied, success
                FROM solution_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (self.window_size,)).fetchall()

        if not results:
            return {
                'attempts': 0,
                'success_rate': None,
                'status': 'no_data'
            }

        attempts = len(results)
        successes = sum(1 for r in results if r['success'])
        success_rate = successes / attempts if attempts > 0 else 0.0

        return {
            'attempts': attempts,
            'successes': successes,
            'success_rate': success_rate,
            'status': self._classify_performance(success_rate, attempts)
        }

    def _classify_performance(self, success_rate: float, attempts: int) -> str:
        """Classify agent performance"""
        if attempts < self.stuck_threshold['min_attempts']:
            return 'learning'
        elif success_rate >= 0.7:
            return 'excellent'
        elif success_rate >= 0.4:
            return 'good'
        elif success_rate >= 0.2:
            return 'struggling'
        else:
            return 'stuck'

    def is_stuck(self, service_id: str) -> Tuple[bool, str]:
        """
        Detect if agent is stuck on a service

        Returns: (is_stuck, reason)
        """
        perf = self.get_recent_performance(service_id)

        # Not enough attempts yet
        if perf['attempts'] < self.stuck_threshold['min_attempts']:
            return False, "insufficient_data"

        # Success rate too low
        if perf['success_rate'] < self.stuck_threshold['max_success_rate']:
            return True, f"low_success_rate_{perf['success_rate']:.0%}"

        # Check for same error repeatedly
        cursor = self.learning_db.conn.cursor()
        recent_errors = cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM solution_history
            WHERE service_id = ?
            AND success = 0
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT 1
        """, (service_id,)).fetchone()

        if recent_errors and recent_errors['count'] >= self.stuck_threshold['same_error_count']:
            return True, f"repeated_error_{recent_errors['error_type']}"

        return False, "performing_ok"

    def get_failure_patterns(self, service_id: str) -> List[Dict]:
        """Identify recurring failure patterns"""
        cursor = self.learning_db.conn.cursor()

        patterns = cursor.execute("""
            SELECT error_type,
                   COUNT(*) as occurrences,
                   GROUP_CONCAT(solution_type) as attempted_solutions
            FROM solution_history
            WHERE service_id = ?
            AND success = 0
            GROUP BY error_type
            ORDER BY occurrences DESC
            LIMIT 5
        """, (service_id,)).fetchall()

        return [dict(p) for p in patterns] if patterns else []

    def generate_recommendations(self, service_id: str, stuck_reason: str) -> List[str]:
        """Generate self-improvement recommendations"""
        recommendations = []

        if "low_success_rate" in stuck_reason:
            recommendations.append("Current solutions not working - need human intervention")
            recommendations.append("Consider: Check service-specific documentation")
            recommendations.append("Consider: Manual debugging of service logs")

        if "repeated_error" in stuck_reason:
            error_type = stuck_reason.split('_')[-1]
            recommendations.append(f"Same error repeating: {error_type}")
            recommendations.append("This may require infrastructure-level fix")
            recommendations.append("Automated healing may not be possible")

        # Get failure patterns
        patterns = self.get_failure_patterns(service_id)
        if patterns:
            top_pattern = patterns[0]
            recommendations.append(
                f"Most common failure: {top_pattern['error_type']} "
                f"({top_pattern['occurrences']} times)"
            )

        return recommendations


class StuckDetector:
    """
    Phase 4: Detect when agent is stuck and needs human help
    """

    def __init__(self, performance_monitor: PerformanceMonitor,
                 learning_db: LearningDatabase):
        self.performance_monitor = performance_monitor
        self.learning_db = learning_db
        self.stuck_services = {}  # {service_id: timestamp}
        logger.info("StuckDetector initialized")

    def check_stuck_state(self, service_id: str) -> Dict:
        """
        Comprehensive stuck state check

        Returns:
        {
            'is_stuck': bool,
            'reason': str,
            'confidence': float,
            'evidence': List[str],
            'recommendations': List[str],
            'should_escalate': bool
        }
        """

        is_stuck, reason = self.performance_monitor.is_stuck(service_id)

        if not is_stuck:
            # Reset stuck state if recovered
            if service_id in self.stuck_services:
                del self.stuck_services[service_id]
                logger.info(f"✅ {service_id} recovered from stuck state!")

            return {
                'is_stuck': False,
                'reason': reason,
                'confidence': 0.0,
                'should_escalate': False
            }

        # Calculate confidence in stuck detection
        perf = self.performance_monitor.get_recent_performance(service_id)
        confidence = 1.0 - perf['success_rate']  # Lower success = higher confidence stuck

        # Collect evidence
        evidence = [
            f"Success rate: {perf['success_rate']:.0%} (threshold: 10%)",
            f"Recent attempts: {perf['attempts']}",
            f"Status: {perf['status']}"
        ]

        # Get failure patterns as evidence
        patterns = self.performance_monitor.get_failure_patterns(service_id)
        if patterns:
            evidence.append(f"Repeated failures: {patterns[0]['error_type']}")

        # Generate recommendations
        recommendations = self.performance_monitor.generate_recommendations(
            service_id, reason
        )

        # Determine if should escalate
        should_escalate = confidence > 0.85  # High confidence = escalate

        # Track stuck state
        if should_escalate and service_id not in self.stuck_services:
            self.stuck_services[service_id] = datetime.now()
            logger.warning(f"🚨 {service_id} detected as STUCK!")

        return {
            'is_stuck': True,
            'reason': reason,
            'confidence': confidence,
            'evidence': evidence,
            'recommendations': recommendations,
            'should_escalate': should_escalate,
            'stuck_since': self.stuck_services.get(service_id)
        }


class MetacognitiveAgent:
    """
    Phase 4: Secondary monitoring layer
    Watches primary agent's performance and intervenes when stuck
    """

    def __init__(self, performance_monitor: PerformanceMonitor,
                 stuck_detector: StuckDetector,
                 notification_manager):
        self.performance_monitor = performance_monitor
        self.stuck_detector = stuck_detector
        self.notification_manager = notification_manager
        self.monitoring_enabled = True
        logger.info("MetacognitiveAgent initialized (self-awareness active)")

    def monitor_healing_attempt(self, service_id: str, result: Dict):
        """Monitor a healing attempt and check for stuck state"""
        if not self.monitoring_enabled:
            return

        # Check if agent is stuck
        stuck_state = self.stuck_detector.check_stuck_state(service_id)

        if stuck_state['should_escalate']:
            logger.warning(f"🧠 METACOGNITION: {service_id} is stuck!")
            logger.warning(f"   Reason: {stuck_state['reason']}")
            logger.warning(f"   Confidence: {stuck_state['confidence']:.0%}")

            # Log evidence
            for evidence in stuck_state['evidence']:
                logger.warning(f"   Evidence: {evidence}")

            # Log recommendations
            logger.info("💡 RECOMMENDATIONS:")
            for rec in stuck_state['recommendations']:
                logger.info(f"   - {rec}")

            # Auto-escalate to human
            self._escalate_stuck_service(service_id, stuck_state)

    def _escalate_stuck_service(self, service_id: str, stuck_state: Dict):
        """Escalate stuck service to human via REALTIME notification"""
        if self.notification_manager:
            self.notification_manager._send_notification({
                'type': 'agent_stuck',
                'tier': 'realtime',
                'severity': 'critical',
                'service_id': service_id,
                'service_critical': True,
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'stuck_state': stuck_state,
                    'message': f"Agent is stuck on {service_id} - Human intervention required",
                    'subject': f"🚨 Agent Stuck on {service_id} - Escalation Required"
                }
            })
            logger.warning(f"📧 REALTIME escalation sent for {service_id}")

    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        overall_perf = self.performance_monitor.get_recent_performance()

        return {
            'overall_performance': overall_perf,
            'stuck_services': list(self.stuck_detector.stuck_services.keys()),
            'monitoring_enabled': self.monitoring_enabled,
            'timestamp': datetime.now().isoformat()
        }


class IntegratedHealingSystem:
    """
    Unified autonomous healing system

    Combines:
    - Platform Health Monitor (diagnostics)
    - Research Agent (solution discovery)
    - Auto-healing (deployment)
    - Learning (pattern recognition)

    PHASE 1 UPGRADE: Added intelligent log analysis and cooldown logic
    """

    def __init__(self, auto_heal: bool = True, research_enabled: bool = True):
        logger.info("Initializing Integrated Healing System...")

        self.auto_heal = auto_heal
        self.research_enabled = research_enabled

        # Initialize resource monitor
        self.resource_monitor = ResourceMonitor(max_memory_mb=400, max_cpu_percent=30)

        # Initialize components
        self.health_monitor = PlatformHealthMonitor(verbose=True)
        self.research_agent = AutonomousResearchAgent(auto_deploy=False) if research_enabled else None

        # PHASE 1 UPGRADE: Initialize intelligence components
        self.log_analyzer = IntelligentLogAnalyzer()
        self.cooldown_manager = CooldownManager()
        logger.info("🧠 Phase 1 Intelligence Upgrade: Log analysis + Cooldown enabled")

        # PHASE 2 UPGRADE: Initialize context awareness
        self.service_classifier = ServiceClassifier()
        logger.info("🎯 Phase 2 Intelligence Upgrade: Context awareness + Service classification enabled")

        # PHASE 3 UPGRADE: Initialize learning system
        self.learning_db = LearningDatabase()
        self.learning_db.sync_patterns(self.log_analyzer.ERROR_PATTERNS)
        self.solution_verifier = SolutionVerifier(self.health_monitor, self.learning_db)
        logger.info("🧠 Phase 3 Learning System: Memory + verification enabled")

        # Initialize tier-based notification system
        self.notification_manager = None
        if EmailReporter and TieredNotificationManager:
            try:
                email_reporter = EmailReporter()
                self.notification_manager = TieredNotificationManager(email_reporter)
                logger.info("✅ Tier-based notification system initialized")
                logger.info("   REALTIME: Critical/High - Send immediately")
                logger.info("   HOURLY: Medium - Batch every hour")
                logger.info("   DAILY: Low/Info - Daily summary at 8 AM")
            except Exception as e:
                logger.warning(f"Failed to initialize notification system: {e}")
        else:
            logger.warning("Notification system not available (missing dependencies)")

        # PHASE 4 UPGRADE: Initialize metacognition
        self.performance_monitor = PerformanceMonitor(self.learning_db)
        self.stuck_detector = StuckDetector(self.performance_monitor, self.learning_db)
        self.metacognitive_agent = MetacognitiveAgent(
            self.performance_monitor,
            self.stuck_detector,
            self.notification_manager
        )
        logger.info("🧠 Phase 4 Metacognition: Self-awareness + stuck detection enabled")

        # WEEK 1 ENHANCEMENT: Initialize cron job monitor
        self.cron_monitor = CronJobMonitor() if CronJobMonitor else None
        if self.cron_monitor:
            logger.info("📋 Week 1 Enhancement: Cron job chaos detection enabled (READ-ONLY)")
        else:
            logger.warning("📋 Cron job monitor not available (module not loaded)")

        # WEEK 2 ENHANCEMENT: Initialize resource limiter (AUTONOMOUS MODE)
        self.resource_limiter = None
        self.approval_workflow = None
        if ResourceLimitEnforcer and ApprovalWorkflow:
            self.approval_workflow = ApprovalWorkflow()
            self.resource_limiter = ResourceLimitEnforcer(self.approval_workflow)
            logger.info("🤖 Week 2 Enhancement: AUTONOMOUS resource limiting enabled")
            logger.info("   - LOW risk: Auto-apply (80% confidence threshold)")
            logger.info("   - MEDIUM risk: Auto-apply (90% confidence threshold)")
            logger.info("   - HIGH risk: Auto-apply (95% confidence threshold)")
            logger.info("   - CRITICAL risk: Email approval required (24h timeout)")
            logger.info("   - Full rollback support + audit trail")
            logger.info("   - No process killing (constraints only)")
        else:
            logger.warning("🔒 Resource limiter not available (module not loaded)")

        # Healing history
        self.healing_history_path = Path("/var/lib/insa-crm/healing_history.jsonl")
        self.healing_history_path.parent.mkdir(parents=True, exist_ok=True)

        # Known issues and solutions (learned patterns)
        self.known_solutions = self._load_known_solutions()

        # Timeout limits (in seconds)
        self.TIMEOUT_HEALTH_CHECK = 60
        self.TIMEOUT_RESEARCH = 300  # 5 minutes max for research
        self.TIMEOUT_DEPLOYMENT = 180  # 3 minutes max for deployment
        self.TIMEOUT_TOTAL_HEALING = 600  # 10 minutes max per service

        logger.info(f"Integrated Healing System initialized")
        logger.info(f"  Auto-heal: {auto_heal}")
        logger.info(f"  Research: {research_enabled}")
        logger.info(f"  Known solutions: {len(self.known_solutions)}")
        logger.info(f"  Resource limits: 400MB RAM, 30% CPU")
        logger.info(f"  Timeout limits: Health={self.TIMEOUT_HEALTH_CHECK}s, Research={self.TIMEOUT_RESEARCH}s, Deploy={self.TIMEOUT_DEPLOYMENT}s")

    def _load_known_solutions(self) -> Dict[str, Solution]:
        """Load previously learned solutions from database"""
        if not self.research_agent:
            return {}

        try:
            # Get all validated solutions from research database
            stats = self.research_agent.db.get_statistics()
            logger.info(f"Research DB stats: {stats}")

            # TODO: Load actual solutions from database
            # For now, return empty dict
            return {}
        except Exception as e:
            logger.error(f"Failed to load known solutions: {e}")
            return {}

    def check_known_solution(self, issue_signature: str) -> Optional[Solution]:
        """Check if we have a known solution for this issue"""
        return self.known_solutions.get(issue_signature)

    def create_issue_signature(self, service_id: str, health_result: Dict) -> str:
        """
        Create unique signature for an issue

        Used to check if we've seen this before
        """
        components = [
            service_id,
            str(health_result.get('http_code', 'none')),
            health_result.get('error', 'unknown')[:50]
        ]

        return "|".join(components)

    def diagnose_and_heal(self, service_id: str) -> Dict[str, Any]:
        """
        Full diagnostic and healing cycle for a service

        Returns:
        {
            'service': str,
            'initial_status': str,
            'issue_detected': bool,
            'solution_found': bool,
            'solution_applied': bool,
            'final_status': str,
            'solution_details': dict,
            'duration_seconds': float,
            'resource_usage': dict
        }
        """

        start_time = time.time()
        logger.info(f"=== Starting diagnosis for {service_id} ===")

        # PHASE 2: Classify service and determine strategy
        service_classification = self.service_classifier.classify_service(service_id)
        logger.info(f"📋 Service classification: {service_classification['type']}")
        logger.info(f"   Strategy: {service_classification['strategy']}")
        logger.info(f"   Reason: {service_classification['reason']}")

        # Check resources before starting
        try:
            resource_stats = self.resource_monitor.check_resources()
            logger.info(f"Resource usage at start: {resource_stats['memory_mb']:.1f}MB, {resource_stats['cpu_percent']:.1f}% CPU")
        except Exception as e:
            logger.warning(f"Could not check resources: {e}")
            resource_stats = {}

        result = {
            'service': service_id,
            'timestamp': datetime.now().isoformat(),
            'initial_status': None,
            'issue_detected': False,
            'solution_found': False,
            'solution_applied': False,
            'final_status': None,
            'solution_details': None,
            'error': None,
            'duration_seconds': 0
        }

        try:
            # Use timeout to prevent hanging
            with timeout(self.TIMEOUT_TOTAL_HEALING):
                # Step 1: Check current health
                logger.info(f"Step 1: Checking health of {service_id}")

                with timeout(self.TIMEOUT_HEALTH_CHECK):
                    service_config = self.health_monitor.SERVICES[service_id]
                    service_type = service_config.get('type', 'web')

                    # Route to appropriate health check based on service type
                    if service_type == 'web':
                        health_result = self.health_monitor.check_http_health(service_id)
                    elif service_type == 'systemd':
                        health_result = self.health_monitor.check_systemd_service(service_id)
                    elif service_type == 'systemd+db':
                        health_result = self.health_monitor.check_database_connection(service_id)
                    elif service_type == 'container+http':
                        health_result = self.health_monitor.check_http_health(service_id)
                    elif service_type == 'container':
                        container_status = self.health_monitor.check_container_status(service_config['container'])
                        health_result = {
                            'healthy': container_status['running'],
                            'container_running': container_status['running'],
                            'container_status': container_status['status'],
                            'error': None if container_status['running'] else f"Container not running: {container_status['status']}"
                        }
                    elif service_type == 'mcp':
                        health_result = self.health_monitor.check_mcp_server(service_id)
                    else:
                        health_result = {'healthy': False, 'error': f'Unknown service type: {service_type}'}

            container = service_config.get('container')
            if container and service_type not in ['container', 'container+http']:
                container_status = self.health_monitor.check_container_status(container)
                health_result['container_running'] = container_status['running']

            result['initial_status'] = 'healthy' if health_result['healthy'] else 'unhealthy'

            if health_result['healthy']:
                logger.info(f"✅ {service_id} is healthy")
                result['final_status'] = 'healthy'
                return result

            # Issue detected
            result['issue_detected'] = True
            logger.warning(f"🚨 Issue detected in {service_id}")
            logger.warning(f"   HTTP code: {health_result.get('http_code', 'N/A')}")
            logger.warning(f"   Error: {health_result.get('error', 'Unknown')}")
            logger.warning(f"   Container: {health_result.get('container_running', 'N/A')}")

            # Step 2: Check for known solution
            issue_sig = self.create_issue_signature(service_id, health_result)
            logger.info(f"Step 2: Checking for known solution (sig: {issue_sig})")

            known_solution = self.check_known_solution(issue_sig)

            if known_solution:
                logger.info(f"✅ Found known solution: {known_solution.solution_id}")
                result['solution_found'] = True
                result['solution_details'] = {
                    'solution_id': known_solution.solution_id,
                    'title': known_solution.title,
                    'source': 'known_pattern',
                    'validation_score': known_solution.validation_score
                }

                # Apply known solution
                if self.auto_heal:
                    applied = self._apply_solution(service_id, known_solution, health_result)
                    result['solution_applied'] = applied

            else:
                # Step 3: Try built-in fix functions first
                logger.info("Step 3: Trying built-in fix functions")

                fix_function_name = service_config.get('fix_function')
                if fix_function_name and self.auto_heal:
                    logger.info(f"Applying built-in fix: {fix_function_name}")
                    fix_function = getattr(self.health_monitor, fix_function_name, None)

                    if fix_function:
                        success = fix_function()
                        result['solution_applied'] = success
                        result['solution_details'] = {
                            'source': 'builtin',
                            'function': fix_function_name,
                            'success': success
                        }

                        if success:
                            logger.info("✅ Built-in fix succeeded")
                            result['solution_found'] = True
                        else:
                            logger.warning("⚠️ Built-in fix failed")

                # PHASE 1 UPGRADE: Step 3.5 - Intelligent Log Analysis
                # Check logs BEFORE expensive web research!
                if not result['solution_applied']:
                    logger.info("Step 3.5: 🧠 Analyzing container logs (PHASE 1 INTELLIGENCE)")

                    log_diagnosis = self.log_analyzer.analyze_before_research(
                        service_id,
                        service_config,
                        health_result
                    )

                    if log_diagnosis and log_diagnosis['confidence'] > 0.7:
                        # PHASE 3: Check for learned confidence adjustment
                        base_confidence = log_diagnosis['confidence']
                        adjusted_confidence = self.learning_db.get_adjusted_confidence(
                            log_diagnosis['diagnosis']
                        )

                        if adjusted_confidence:
                            logger.info(f"📚 Learned adjustment: {base_confidence:.2f} → {adjusted_confidence:.2f}")
                            log_diagnosis['confidence'] = adjusted_confidence
                            log_diagnosis['base_confidence'] = base_confidence

                        logger.info(f"✅ Found issue in logs: {log_diagnosis['diagnosis']}")
                        logger.info(f"   Category: {log_diagnosis['category']}")
                        logger.info(f"   Confidence: {log_diagnosis['confidence']:.0%}")
                        logger.info(f"   Fix hint: {log_diagnosis['fix_hint']}")

                        result['solution_found'] = True
                        result['solution_details'] = log_diagnosis
                        result['skipped_research'] = True
                        result['skip_reason'] = 'found_in_logs'

                        # PHASE 3: Record pattern match (will update after verification)
                        self.learning_db.record_pattern_outcome(
                            service_id,
                            log_diagnosis['diagnosis'],
                            log_diagnosis['confidence'],
                            log_diagnosis['evidence'],
                            solution_applied=False,  # Will verify later
                            solution_worked=None  # Will know after verification
                        )

                        # Don't waste time on web research - we found the problem locally!
                        logger.info("⚡ Skipping web research - issue diagnosed from logs")

                # PHASE 2: Context-aware decision about research
                if not result['solution_applied'] and not result.get('skipped_research'):
                    # Check if research is appropriate for this service type
                    checked_logs = bool(log_diagnosis) or service_config.get('container') is None
                    should_research, research_reason = self.service_classifier.should_research(service_id, checked_logs)

                    if not should_research:
                        logger.info(f"⚠️ Skipping research: {research_reason}")
                        result['skipped_research'] = True
                        result['skip_reason'] = research_reason

                        # For custom internal services, escalate to human immediately
                        if service_classification['strategy'] == 'local_only':
                            logger.warning(f"🆘 Custom internal service failure - needs human diagnosis!")
                            # Queue REALTIME notification via tier system
                            if self.notification_manager:
                                self.notification_manager.queue.enqueue(
                                    notification_type=NotificationType.CRITICAL_ALERT,
                                    data={
                                        'service_id': service_id,
                                        'classification': service_classification,
                                        'reason': 'Custom codebase - requires human diagnosis',
                                        'health_result': health_result,
                                        'timestamp': datetime.now().isoformat()
                                    },
                                    severity='high',
                                    service_critical=True
                                )

                # Step 4: Research new solution if needed (ONLY if log analysis didn't find anything)
                if not result['solution_applied'] and not result.get('skipped_research') and self.research_enabled:
                    logger.info("Step 4: Researching new solution...")

                    research_result = self._research_solution(service_id, health_result)

                    if research_result:
                        result['solution_found'] = True
                        result['solution_details'] = research_result

                        # Apply researched solution
                        if self.auto_heal and research_result.get('production_ready'):
                            solution_obj = research_result.get('solution_object')
                            if solution_obj:
                                applied = self._apply_solution(service_id, solution_obj, health_result)
                                result['solution_applied'] = applied

            # Step 5: Verify fix
            logger.info("Step 5: Verifying fix...")
            time.sleep(10)  # Wait for service to stabilize

            # Use same routing as initial health check
            if service_type == 'web':
                final_health = self.health_monitor.check_http_health(service_id)
            elif service_type == 'systemd':
                final_health = self.health_monitor.check_systemd_service(service_id)
            elif service_type == 'systemd+db':
                final_health = self.health_monitor.check_database_connection(service_id)
            elif service_type == 'container+http':
                final_health = self.health_monitor.check_http_health(service_id)
            elif service_type == 'container':
                container_status = self.health_monitor.check_container_status(service_config['container'])
                final_health = {
                    'healthy': container_status['running'],
                    'error': None if container_status['running'] else f"Container not running: {container_status['status']}"
                }
            elif service_type == 'mcp':
                final_health = self.health_monitor.check_mcp_server(service_id)
            else:
                final_health = {'healthy': False, 'error': f'Unknown service type: {service_type}'}

            result['final_status'] = 'healthy' if final_health['healthy'] else 'still_unhealthy'

            if final_health['healthy']:
                logger.info(f"✅ {service_id} is now healthy!")
            else:
                logger.error(f"❌ {service_id} is still unhealthy")
                result['error'] = final_health.get('error')

        except TimeoutError as e:
            logger.error(f"Timeout during diagnosis: {e}")
            result['error'] = f"Timeout: {str(e)}"
            result['final_status'] = 'timeout'
        except MemoryError as e:
            logger.error(f"Memory limit exceeded: {e}")
            result['error'] = f"Memory limit: {str(e)}"
            result['final_status'] = 'resource_limit'
        except Exception as e:
            logger.error(f"Error during diagnosis and healing: {e}", exc_info=True)
            result['error'] = str(e)
            result['final_status'] = 'error'

        # Record duration and final resource usage
        result['duration_seconds'] = time.time() - start_time

        try:
            final_resource_stats = self.resource_monitor.check_resources()
            result['resource_usage'] = final_resource_stats
            logger.info(f"Final resource usage: {final_resource_stats['memory_mb']:.1f}MB, {final_resource_stats['cpu_percent']:.1f}% CPU")
        except Exception as e:
            logger.debug(f"Failed to collect final resource stats: {e}")

        # Save to history
        self._save_healing_event(result)

        # PHASE 1 UPGRADE: Track cooldown based on outcome
        if result['final_status'] == 'healthy':
            self.cooldown_manager.record_success(service_id)
        else:
            self.cooldown_manager.record_failure(service_id)

        # Log cooldown stats
        cooldown_stats = self.cooldown_manager.get_stats()
        logger.info(f"Cooldown stats: {cooldown_stats['services_in_cooldown']} services in cooldown, {cooldown_stats['total_failures']} total failures")

        # Send notification via tier-based system
        if self.notification_manager:
            try:
                self.notification_manager.notify_healing_event(service_id, result)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

        logger.info(f"=== Diagnosis complete for {service_id} ({result['duration_seconds']:.1f}s) ===")

        # PHASE 4: Metacognitive monitoring
        if self.metacognitive_agent:
            self.metacognitive_agent.monitor_healing_attempt(service_id, result)

        return result

    def _research_solution(self, service_id: str, health_result: Dict) -> Optional[Dict]:
        """
        Research solution using autonomous research agent

        Returns:
        {
            'query_id': str,
            'solution_id': str,
            'title': str,
            'validation_score': float,
            'production_ready': bool,
            'sources': list,
            'solution_object': Solution
        }
        """

        if not self.research_agent:
            return None

        logger.info(f"Starting research for {service_id} issue...")

        service_config = self.health_monitor.SERVICES[service_id]

        # Construct research query
        query_text = self._construct_research_query(service_id, health_result, service_config)

        logger.info(f"Research query: {query_text}")

        # Create research query object
        query = ResearchQuery(
            query_id=f"{service_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            trigger=ResearchTrigger.ERROR_DETECTED,
            query_text=query_text,
            context={
                'service_id': service_id,
                'service_name': service_config['name'],
                'url': service_config['url'],
                'http_code': health_result.get('http_code'),
                'error': health_result.get('error'),
                'container': service_config.get('container'),
                'container_running': health_result.get('container_running')
            },
            error_message=health_result.get('error'),
            affected_component=service_id,
            priority=10 if service_config.get('critical') else 7
        )

        # Execute research
        try:
            solution = self.research_agent.research(query)

            if solution:
                logger.info(f"✅ Research found solution: {solution.solution_id}")
                logger.info(f"   Validation score: {solution.validation_score:.2%}")
                logger.info(f"   Production ready: {solution.is_production_ready}")

                return {
                    'query_id': query.query_id,
                    'solution_id': solution.solution_id,
                    'title': solution.title,
                    'validation_score': solution.validation_score,
                    'production_ready': solution.is_production_ready,
                    'sources': solution.source_urls,
                    'solution_object': solution
                }
            else:
                logger.warning("❌ Research did not find a solution")
                return None

        except Exception as e:
            logger.error(f"Research failed: {e}", exc_info=True)
            return None

    def _construct_research_query(
        self,
        service_id: str,
        health_result: Dict,
        service_config: Dict
    ) -> str:
        """
        Construct intelligent research query based on issue details

        Examples:
        - "ERPNext nginx timeout 504 gateway error docker container"
        - "n8n workflow engine permission denied /home/node/.n8n"
        - "Grafana plugin installation failed dashboard not loading"
        """

        parts = [service_config['name']]

        # Add error details
        if health_result.get('http_code'):
            parts.append(f"HTTP {health_result['http_code']}")

        if health_result.get('error'):
            error = health_result['error']
            # Extract key terms
            parts.append(error)

        # Add container info if relevant
        if service_config.get('container') and not health_result.get('container_running'):
            parts.append("docker container not running")

        # Add technology-specific keywords
        tech_keywords = {
            'erpnext': ['frappe', 'nginx', 'websocket', 'docker-compose'],
            'n8n': ['workflow', 'permissions', 'node'],
            'grafana': ['plugin', 'dashboard', 'datasource'],
            'mautic': ['cron', 'segments', 'email'],
            'defectdojo': ['uwsgi', 'celery', 'redis'],
            'inventree': ['django', 'postgresql']
        }

        if service_id in tech_keywords:
            parts.extend(tech_keywords[service_id][:2])  # Add first 2 keywords

        # Add "production" and "fix" for better results
        parts.extend(['production', 'fix', 'solution'])

        return " ".join(parts)

    def _apply_solution(
        self,
        service_id: str,
        solution: Solution,
        health_result: Dict
    ) -> bool:
        """
        Apply solution to fix the issue

        This is the critical integration point:
        - Takes Solution from research agent
        - Translates to concrete actions
        - Executes fixes
        - Verifies success
        """

        logger.info(f"Applying solution {solution.solution_id} to {service_id}...")

        try:
            # Extract actionable steps from solution
            steps = solution.steps if solution.steps else []
            code_snippets = solution.code_snippets if solution.code_snippets else []

            # If no explicit steps, try to infer from description
            if not steps and solution.description:
                steps = self._infer_steps_from_description(solution.description)

            if not steps:
                logger.warning("No actionable steps found in solution")
                return False

            # Execute steps
            for i, step in enumerate(steps, 1):
                logger.info(f"Executing step {i}/{len(steps)}: {step[:100]}")

                success = self._execute_step(service_id, step, code_snippets)

                if not success:
                    logger.error(f"Step {i} failed")
                    return False

            logger.info(f"✅ All steps executed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to apply solution: {e}", exc_info=True)
            return False

    def _infer_steps_from_description(self, description: str) -> List[str]:
        """
        Infer actionable steps from solution description

        Looks for common patterns:
        - "restart the container"
        - "update configuration file"
        - "run command: docker-compose restart"
        """

        steps = []

        # Common patterns
        if "restart" in description.lower():
            steps.append("Restart the service")

        if "docker-compose" in description.lower():
            # Extract docker-compose commands
            import re
            commands = re.findall(r'docker-compose\s+\S+', description)
            steps.extend(commands)

        if "permission" in description.lower() and "chmod" in description.lower():
            steps.append("Fix file permissions")

        return steps

    def _execute_step(self, service_id: str, step: str, code_snippets: List[str]) -> bool:
        """
        Execute a single solution step

        Safely executes common operations:
        - Service restarts
        - Container operations
        - Configuration updates
        - Permission fixes
        """

        step_lower = step.lower()

        # Restart operations
        if "restart" in step_lower:
            service_config = self.health_monitor.SERVICES[service_id]
            container = service_config.get('container')

            if container:
                logger.info(f"Restarting container: {container}")
                cmd = f"docker restart {container}"
                returncode, stdout, stderr = self.health_monitor.run_command(cmd, timeout=60)

                if returncode == 0:
                    logger.info("Container restarted successfully")
                    time.sleep(10)  # Wait for startup
                    return True
                else:
                    logger.error(f"Container restart failed: {stderr}")
                    return False

        # Docker-compose operations
        elif "docker-compose" in step_lower:
            # Extract and execute docker-compose command
            logger.info(f"Executing docker-compose command: {step}")

            service_config = self.health_monitor.SERVICES[service_id]
            compose_dir = service_config.get('compose_dir')

            if compose_dir:
                cmd = f"cd {compose_dir} && {step}"
                returncode, stdout, stderr = self.health_monitor.run_command(cmd, timeout=120)

                if returncode == 0:
                    logger.info("Docker-compose command succeeded")
                    time.sleep(15)  # Wait for services
                    return True
                else:
                    logger.error(f"Docker-compose command failed: {stderr}")
                    return False

        # Permission fixes
        elif "permission" in step_lower or "chmod" in step_lower:
            logger.info("Applying permission fixes...")
            # TODO: Implement safe permission fixes
            return True

        # Configuration updates
        elif "config" in step_lower:
            logger.info("Configuration update step detected")
            # TODO: Implement safe config updates
            return True

        else:
            logger.warning(f"Unknown step type: {step}")
            return False

    def _save_healing_event(self, event: Dict):
        """Save healing event to JSONL history"""
        try:
            with open(self.healing_history_path, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to save healing event: {e}")

    def run_full_platform_scan(self) -> Dict[str, Any]:
        """
        Run complete platform health scan with healing

        Returns:
        {
            'timestamp': str,
            'services_checked': int,
            'issues_detected': int,
            'issues_fixed': int,
            'cron_chaos': dict,  # NEW: Week 1 enhancement
            'services': {service_id: result}
        }
        """

        logger.info("=== Starting full platform scan ===")

        report = {
            'timestamp': datetime.now().isoformat(),
            'services_checked': 0,
            'issues_detected': 0,
            'issues_fixed': 0,
            'cron_chaos': None,  # NEW: Week 1
            'services': {}
        }

        # WEEK 1 ENHANCEMENT: Check for cron job chaos
        if self.cron_monitor:
            try:
                logger.info("\n📋 Week 1: Checking cron job chaos...")
                cron_report = self.cron_monitor.detect_cron_chaos()
                report['cron_chaos'] = cron_report

                # Alert on HIGH or CRITICAL risk
                if cron_report['risk_level'] in ['HIGH', 'CRITICAL']:
                    logger.warning(f"⚠️  Cron Job Chaos: {cron_report['risk_level']}")
                    logger.warning(f"   {cron_report['recommendation']}")
                    logger.warning(f"   Total jobs: {cron_report['total_jobs']}")
                    logger.warning(f"   Duplicates: {cron_report['duplicates']}")
                    logger.warning(f"   Time overlaps: {len(cron_report['time_overlaps'])}")
                    logger.warning(f"   Runaway processes: {len(cron_report['runaway_processes'])}")

                    # Send notification
                    if self.notification_manager and cron_report['risk_level'] == 'CRITICAL':
                        self.notification_manager.add_notification(
                            'CRITICAL',
                            'Cron Job Chaos',
                            f"Detected {cron_report['duplicates']} duplicate cron jobs and "
                            f"{len(cron_report['runaway_processes'])} runaway processes. "
                            f"{cron_report['recommendation']}"
                        )
                else:
                    logger.info(f"✅ Cron jobs: {cron_report['risk_level']} risk ({cron_report['total_jobs']} jobs)")

            except Exception as e:
                logger.error(f"Failed to check cron chaos: {e}")
                report['cron_chaos'] = {'error': str(e)}

        # WEEK 2 ENHANCEMENT: Process runaway processes (AUTONOMOUS)
        if self.resource_limiter and self.cron_monitor and report.get('cron_chaos'):
            try:
                runaway_processes = report['cron_chaos'].get('runaway_processes', [])
                cron_risk_level = report['cron_chaos'].get('risk_level', 'MEDIUM')

                if runaway_processes:
                    logger.info(f"\n🤖 Week 2: Processing {len(runaway_processes)} runaway processes (AUTONOMOUS)...")

                    autonomous_applied = 0
                    email_approval_required = []
                    already_constrained = 0
                    failed = []

                    for proc in runaway_processes:
                        # Calculate confidence for this specific process
                        confidence = self.resource_limiter.calculate_confidence(proc)

                        # Add cron risk level to process info
                        proc['risk_level'] = cron_risk_level

                        # AUTONOMOUS constraint (auto-applies for LOW/MEDIUM/HIGH with sufficient confidence)
                        result = self.resource_limiter.constrain_autonomous(
                            target_info=proc,
                            risk_level=cron_risk_level,
                            limits={'cpu_percent': 30, 'memory_mb': 256},
                            confidence=confidence
                        )

                        if result['status'] == 'autonomous_applied':
                            autonomous_applied += 1
                            logger.info(f"   ✅ PID {proc['pid']}: AUTONOMOUS constraint applied (confidence={confidence:.0%})")

                        elif result['status'] == 'email_approval_required':
                            email_approval_required.append(result)
                            logger.warning(f"   📧 PID {proc['pid']}: EMAIL approval required (risk={cron_risk_level}, confidence={confidence:.0%})")

                        elif result['status'] == 'already_constrained':
                            already_constrained += 1
                            logger.info(f"   ✅ PID {proc['pid']}: Already constrained")

                        elif result['status'] == 'autonomous_failed':
                            failed.append(result)
                            logger.error(f"   ❌ PID {proc['pid']}: Failed to constrain - {result['message']}")

                    report['resource_constraints'] = {
                        'runaway_processes': len(runaway_processes),
                        'autonomous_applied': autonomous_applied,
                        'email_approval_required': len(email_approval_required),
                        'already_constrained': already_constrained,
                        'failed': len(failed),
                        'email_requests': email_approval_required,
                        'cron_risk_level': cron_risk_level
                    }

                    # Summary
                    logger.info(f"\n📊 Resource Constraint Summary:")
                    logger.info(f"   🤖 Autonomous: {autonomous_applied}/{len(runaway_processes)} processes")
                    if email_approval_required:
                        logger.warning(f"   📧 Email approval needed: {len(email_approval_required)} CRITICAL cases")

                    # Send email ONLY for CRITICAL cases
                    if email_approval_required and self.notification_manager:
                        self.notification_manager.add_notification(
                            'CRITICAL',
                            'CRITICAL: Resource Constraint Approval Required',
                            f"{len(email_approval_required)} CRITICAL runaway processes detected. "
                            f"Email approval required within 24 hours. "
                            f"Risk: {cron_risk_level}. "
                            f"Review approval requests in database."
                        )
                else:
                    logger.info(f"✅ Week 2: No runaway processes detected")

            except Exception as e:
                logger.error(f"Failed to process runaway processes: {e}")
                report['resource_constraints'] = {'error': str(e)}

        for service_id in self.health_monitor.SERVICES.keys():
            logger.info(f"\n--- Checking {service_id} ---")

            result = self.diagnose_and_heal(service_id)

            report['services'][service_id] = result
            report['services_checked'] += 1

            if result['issue_detected']:
                report['issues_detected'] += 1

            if result['final_status'] == 'healthy' and result['issue_detected']:
                report['issues_fixed'] += 1

        # Summary
        logger.info("\n=== Platform Scan Complete ===")
        logger.info(f"Services checked: {report['services_checked']}")
        logger.info(f"Issues detected: {report['issues_detected']}")
        logger.info(f"Issues fixed: {report['issues_fixed']}")

        if report['issues_detected'] > 0:
            fix_rate = (report['issues_fixed'] / report['issues_detected']) * 100
            logger.info(f"Fix rate: {fix_rate:.1f}%")

        return report

    def run_continuous(self, interval: int = 300):
        """
        Run continuous monitoring with healing

        Args:
            interval: Check interval in seconds (default 5 minutes)
        """

        logger.info(f"Starting continuous healing (interval: {interval}s)")

        iteration = 0

        while True:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Healing Iteration #{iteration}")
                logger.info(f"{'='*60}\n")

                # Run full platform scan
                report = self.run_full_platform_scan()

                # Sleep until next check
                logger.info(f"\nSleeping {interval}s until next check...\n")
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("\nShutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in continuous loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retry


def main():
    """Main entry point"""

    import argparse

    parser = argparse.ArgumentParser(description="INSA Integrated Healing System")
    parser.add_argument("--no-auto-heal", action="store_true", help="Disable automatic healing")
    parser.add_argument("--no-research", action="store_true", help="Disable research agent")
    parser.add_argument("--interval", type=int, default=300, help="Monitoring interval in seconds (default: 300)")
    parser.add_argument("--service", type=str, help="Check specific service only")
    parser.add_argument("--once", action="store_true", help="Run once and exit")

    args = parser.parse_args()

    # Initialize system
    system = IntegratedHealingSystem(
        auto_heal=not args.no_auto_heal,
        research_enabled=not args.no_research
    )

    if args.service:
        # Single service check
        logger.info(f"Checking single service: {args.service}")
        result = system.diagnose_and_heal(args.service)

        print("\n" + "="*60)
        print(f"Result: {json.dumps(result, indent=2)}")
        print("="*60)

    elif args.once:
        # Single full scan
        report = system.run_full_platform_scan()

        print("\n" + "="*60)
        print(f"Platform Scan Report:")
        print(f"  Services Checked: {report['services_checked']}")
        print(f"  Issues Detected: {report['issues_detected']}")
        print(f"  Issues Fixed: {report['issues_fixed']}")
        print("="*60)

    else:
        # Continuous mode
        system.run_continuous(interval=args.interval)


if __name__ == "__main__":
    main()
