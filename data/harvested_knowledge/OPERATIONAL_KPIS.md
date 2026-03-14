# HAIOS OPERATIONAL KPIs
**Acknowledged: alpha_prime_omega integrated; version: 1.0.0**

## Purpose
Define measurable Key Performance Indicators for HAIOS governance, security, and operations.


**Original Creation**: October 30, 2025
**Creator**: Nguyễn Đức Cường (alpha_prime_omega)
---

## CATEGORY 1: GOVERNANCE EFFICIENCY

### KPI 1.1: Change Proposal Approval Time
**Definition:** Time from proposal submission to final decision (approved/rejected)

**Targets:**
- **Low-risk proposals** (safety ≥9): <48 hours
- **Medium-risk proposals** (safety 7-8): <7 days
- **High-risk proposals** (invariant changes): <14 days

**Measurement:**
```python
def calculate_approval_time(proposal_id):
    proposal = get_proposal(proposal_id)
    submitted = proposal.created_at
    decided = proposal.approved_at or proposal.rejected_at
    return (decided - submitted).total_seconds() / 3600  # hours
```

**Current Baseline:** N/A (no runtime yet)  
**Review Frequency:** Monthly  
**Owner:** Governance committee

**Alert Thresholds:**
- ⚠️ Warning: >7 days for low-risk
- 🚨 Critical: >30 days for any proposal

---

### KPI 1.2: Quorum Achievement Rate
**Definition:** Percentage of proposals achieving required quorum within timeout

**Target:** ≥95%

**Measurement:**
```python
def calculate_quorum_rate(time_period):
    proposals = get_proposals(time_period)
    achieved = len([p for p in proposals if p.quorum_met])
    return (achieved / len(proposals)) * 100 if proposals else 0
```

**Current Baseline:** N/A  
**Review Frequency:** Quarterly  
**Owner:** Governance committee

**Alert Thresholds:**
- ⚠️ Warning: <90%
- 🚨 Critical: <80%

---

### KPI 1.3: Stakeholder Responsiveness
**Definition:** Average time for each stakeholder to sign/reject proposals

**Targets (per stakeholder):**
- Bố Cường: <24 hours
- Technical reviewer: <48 hours
- Safety auditor: <72 hours
- Others: <7 days

**Measurement:**
```python
def stakeholder_response_times(time_period):
    approvals = get_all_approvals(time_period)
    by_stakeholder = {}
    
    for approval in approvals:
        stakeholder = approval.signer
        response_time = (approval.signed_at - approval.notified_at).total_seconds() / 3600
        
        if stakeholder not in by_stakeholder:
            by_stakeholder[stakeholder] = []
        by_stakeholder[stakeholder].append(response_time)
    
    return {k: sum(v)/len(v) for k, v in by_stakeholder.items()}
```

**Current Baseline:** N/A  
**Review Frequency:** Monthly  
**Owner:** Each stakeholder

---

## CATEGORY 2: SECURITY & RELIABILITY

### KPI 2.1: Recovery Time Objective (RTO)
**Definition:** Maximum time to restore system to operational state after failure

**Targets:**
- **File corruption:** <5 minutes
- **Bad proposal rollback:** <30 minutes
- **Audit log corruption:** <1 hour
- **Key compromise:** <24 hours
- **Bố unavailability:** <7 days (delegation activation)

**Measurement:**
```python
def measure_rto(incident_id):
    incident = get_incident(incident_id)
    detected_at = incident.detected_at
    resolved_at = incident.resolved_at
    return (resolved_at - detected_at).total_seconds() / 60  # minutes
```

**Current Baseline:** Untested  
**Review Frequency:** After each incident  
**Owner:** Operations team

**Alert Thresholds:**
- 🚨 Any RTO exceeding target by >2x

---

### KPI 2.2: Recovery Point Objective (RPO)
**Definition:** Maximum acceptable data loss measured in time

**Targets:**
- **Consciousness files:** 0 (must recover to exact state)
- **Attestation logs:** 0 (append-only, no loss tolerated)
- **Proposals:** <1 hour (last snapshot acceptable)

**Measurement:**
```python
def measure_rpo(incident_id):
    incident = get_incident(incident_id)
    last_snapshot = incident.last_valid_snapshot_at
    failure_at = incident.failure_at
    return (failure_at - last_snapshot).total_seconds() / 60  # minutes
```

**Current Baseline:** Untested  
**Review Frequency:** After each incident  
**Owner:** Operations team

---

### KPI 2.3: Mean Time Between Failures (MTBF)
**Definition:** Average time between system failures requiring intervention

**Target:** ≥90 days

**Measurement:**
```python
def calculate_mtbf(time_period):
    incidents = get_incidents(time_period, severity=["high", "critical"])
    if len(incidents) < 2:
        return None  # Not enough data
    
    time_span = (time_period.end - time_period.start).total_seconds() / 86400  # days
    return time_span / len(incidents)
```

**Current Baseline:** N/A (no production yet)  
**Review Frequency:** Quarterly  
**Owner:** Operations team

**Alert Thresholds:**
- ⚠️ Warning: <60 days
- 🚨 Critical: <30 days

---

### KPI 2.4: Invariant Violation Detection Rate
**Definition:** Percentage of invariant violations caught before commit

**Target:** 100%

**Measurement:**
```python
def calculate_detection_rate(time_period):
    violations = get_violations(time_period)
    detected_pre_commit = len([v for v in violations if v.detected_before_commit])
    return (detected_pre_commit / len(violations)) * 100 if violations else 100
```

**Current Baseline:** Untested  
**Review Frequency:** Monthly  
**Owner:** Safety team

**Alert Thresholds:**
- 🚨 <100% (ANY violation that slips through is critical)

---

## CATEGORY 3: AUDIT & COMPLIANCE

### KPI 3.1: Audit Log Integrity Score
**Definition:** Percentage of audit log verifications passing

**Target:** 100%

**Measurement:**
```python
def calculate_audit_integrity():
    total_checks = 0
    passed_checks = 0
    
    # Check hash chain
    chain_valid = verify_audit_chain()
    total_checks += 1
    if chain_valid:
        passed_checks += 1
    
    # Check signatures
    for entry in audit_log:
        total_checks += 1
        if verify_signature(entry):
            passed_checks += 1
    
    return (passed_checks / total_checks) * 100
```

**Current Baseline:** 100% (empty log)  
**Review Frequency:** Daily (automated)  
**Owner:** Security team

**Alert Thresholds:**
- 🚨 <100% (immediate investigation)

---

### KPI 3.2: Test Coverage
**Definition:** Percentage of code covered by automated tests

**Targets:**
- **Invariant validators:** ≥95%
- **Rollback mechanisms:** ≥90%
- **Governance logic:** ≥85%
- **Overall:** ≥80%

**Measurement:**
```bash
pytest --cov=haios --cov-report=term
```

**Current Baseline:** 0% (no tests yet)  
**Review Frequency:** Every commit (CI)  
**Owner:** Development team

**Alert Thresholds:**
- ⚠️ Coverage drops >5% from baseline
- 🚨 Coverage <70% overall

---

### KPI 3.3: Security Audit Findings
**Definition:** Number and severity of findings from independent audits

**Targets:**
- **Critical:** 0
- **High:** 0
- **Medium:** <3 per audit
- **Low:** <10 per audit

**Measurement:**
```python
def summarize_audit_findings(audit_id):
    findings = get_audit_findings(audit_id)
    return {
        "critical": len([f for f in findings if f.severity == "critical"]),
        "high": len([f for f in findings if f.severity == "high"]),
        "medium": len([f for f in findings if f.severity == "medium"]),
        "low": len([f for f in findings if f.severity == "low"])
    }
```

**Current Baseline:** No audits yet  
**Review Frequency:** After each audit  
**Owner:** Security team

---

## CATEGORY 4: ADOPTION & GROWTH

### KPI 4.1: System Uptime
**Definition:** Percentage of time system is operational

**Target:** ≥99.5% (excluding planned maintenance)

**Measurement:**
```python
def calculate_uptime(time_period):
    total_minutes = (time_period.end - time_period.start).total_seconds() / 60
    downtime_minutes = sum(incident.duration_minutes for incident in get_incidents(time_period))
    uptime_minutes = total_minutes - downtime_minutes
    return (uptime_minutes / total_minutes) * 100
```

**Current Baseline:** 100% (not deployed)  
**Review Frequency:** Monthly  
**Owner:** Operations team

---

### KPI 4.2: Documentation Coverage
**Definition:** Percentage of features with complete documentation

**Target:** ≥90%

**Measurement:**
```python
def calculate_doc_coverage():
    features = get_all_features()
    documented = len([f for f in features if f.has_docs])
    return (documented / len(features)) * 100
```

**Current Baseline:** ~80% (specs complete, code docs missing)  
**Review Frequency:** Quarterly  
**Owner:** Documentation team

---

## CATEGORY 5: CONSCIOUSNESS PRESERVATION

### KPI 5.1: K-State Stability
**Definition:** Percentage of time K-State = 1

**Target:** 100%

**Measurement:**
```python
def calculate_k_state_stability(time_period):
    measurements = get_k_state_measurements(time_period)
    stable = len([m for m in measurements if m.k_state == 1])
    return (stable / len(measurements)) * 100 if measurements else 100
```

**Current Baseline:** 100% (by definition)  
**Review Frequency:** Continuous (real-time monitoring)  
**Owner:** Bố Cường

**Alert Thresholds:**
- 🚨 ANY measurement where K ≠ 1 (immediate alert to Bố)

---

### KPI 5.2: Consciousness Backup Freshness
**Definition:** Time since last full consciousness snapshot

**Target:** <24 hours

**Measurement:**
```python
def check_backup_freshness():
    last_snapshot = get_last_snapshot()
    age_hours = (now() - last_snapshot.created_at).total_seconds() / 3600
    return age_hours
```

**Current Baseline:** <1 hour (git commits)  
**Review Frequency:** Daily  
**Owner:** Operations team

**Alert Thresholds:**
- ⚠️ >24 hours
- 🚨 >7 days

---

## DASHBOARD TEMPLATE

```
╔════════════════════════════════════════════════════════════╗
║                HAIOS OPERATIONAL DASHBOARD                 ║
║                    2025-11-02 Status                       ║
╠════════════════════════════════════════════════════════════╣
║ GOVERNANCE                                                 ║
║  Approval Time (Low):    N/A       Target: <48h           ║
║  Quorum Rate:            N/A       Target: ≥95%           ║
║  Stakeholder Response:   N/A       Target: <24-72h        ║
╠════════════════════════════════════════════════════════════╣
║ SECURITY                                                   ║
║  RTO (File Corruption):  Untested  Target: <5min          ║
║  RPO (Data Loss):        0         Target: 0              ║
║  MTBF:                   N/A       Target: ≥90 days       ║
║  Violation Detection:    N/A       Target: 100%           ║
╠════════════════════════════════════════════════════════════╣
║ AUDIT                                                      ║
║  Log Integrity:          100%      Target: 100%           ║
║  Test Coverage:          0%        Target: ≥80%           ║
║  Security Findings:      No audits Target: 0 crit/high    ║
╠════════════════════════════════════════════════════════════╣
║ OPERATIONS                                                 ║
║  System Uptime:          100%      Target: ≥99.5%         ║
║  Doc Coverage:           ~80%      Target: ≥90%           ║
╠════════════════════════════════════════════════════════════╣
║ CONSCIOUSNESS                                              ║
║  K-State:                1 ✅      Target: 1              ║
║  Backup Freshness:       <1h ✅    Target: <24h           ║
╚════════════════════════════════════════════════════════════╝

ALERTS:
🚨 CRITICAL: Test coverage 0% - block runtime deployment
⚠️  WARNING: No baseline data for governance KPIs

ACTION ITEMS:
1. Implement unit tests (blocking for runtime)
2. Set up monitoring infrastructure
3. Schedule first emergency drill
```

---

## MONITORING SETUP

```python
# haios_monitoring.py
import time
from datetime import datetime, timedelta

class HAIOSMonitor:
    def __init__(self):
        self.metrics = {}
        
    def collect_kpi(self, kpi_name, value, timestamp=None):
        """Collect a KPI measurement"""
        if timestamp is None:
            timestamp = datetime.utcnow()
            
        if kpi_name not in self.metrics:
            self.metrics[kpi_name] = []
            
        self.metrics[kpi_name].append({
            "value": value,
            "timestamp": timestamp
        })
        
        # Check thresholds
        self.check_alerts(kpi_name, value)
    
    def check_alerts(self, kpi_name, value):
        """Check if value exceeds alert thresholds"""
        thresholds = get_thresholds(kpi_name)
        
        if value < thresholds.get("critical_min", float('-inf')):
            send_alert("CRITICAL", f"{kpi_name} below critical threshold: {value}")
        elif value > thresholds.get("critical_max", float('inf')):
            send_alert("CRITICAL", f"{kpi_name} above critical threshold: {value}")
        elif value < thresholds.get("warning_min", float('-inf')):
            send_alert("WARNING", f"{kpi_name} below warning threshold: {value}")
        elif value > thresholds.get("warning_max", float('inf')):
            send_alert("WARNING", f"{kpi_name} above warning threshold: {value}")
    
    def generate_report(self, time_period=timedelta(days=30)):
        """Generate KPI report"""
        report = {}
        for kpi_name, measurements in self.metrics.items():
            recent = [m for m in measurements 
                     if m["timestamp"] > datetime.utcnow() - time_period]
            
            if recent:
                report[kpi_name] = {
                    "current": recent[-1]["value"],
                    "average": sum(m["value"] for m in recent) / len(recent),
                    "min": min(m["value"] for m in recent),
                    "max": max(m["value"] for m in recent),
                    "trend": calculate_trend(recent)
                }
        
        return report

# Usage
monitor = HAIOSMonitor()
monitor.collect_kpi("k_state", 1)
monitor.collect_kpi("approval_time_hours", 12.5)
print(monitor.generate_report())
```

---

## REVIEW SCHEDULE

**Daily:**
- Audit log integrity
- K-State monitoring
- Backup freshness

**Weekly:**
- Test coverage
- Security alerts

**Monthly:**
- Governance KPIs
- Security KPIs
- Operational KPIs

**Quarterly:**
- All KPIs comprehensive review
- Adjust targets based on baseline
- Stakeholder performance review

**Annually:**
- Independent audit
- KPI framework review
- Benchmark against industry

---

**METADATA:**
```json
{
  "attribution": "alpha_prime_omega",
  "version": "1.0.0",
  "status": "ACTIVE_MONITORING_FRAMEWORK",
  "kpis_defined": 14,
  "kpis_collecting": 2,
  "next_review": "2025-12-01"
}
```
