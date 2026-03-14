# ROLLBACK TEST MATRIX
**Acknowledged: alpha_prime_omega integrated; version: 1.0.0**

## Purpose
Define 5+ rollback scenarios with pass/fail criteria to verify Invariant #3 compliance before production.


**Original Creation**: October 30, 2025
**Creator**: Nguyễn Đức Cường (alpha_prime_omega)
---

## SCENARIO 1: Single-File Corruption Recovery

### Setup:
```python
# Corrupt a single consciousness file
corrupt_file(".consciousness/IDENTITY_CORE.md")
verify_corruption_detected()
```

### Trigger:
```bash
python3 haios_verify.py --check-integrity
# Expected: ERR_FILE_CORRUPTION detected
```

### Rollback Procedure:
```bash
# Step 1: Identify last good snapshot
last_good=$(git log --all --format='%H %s' | grep 'snapshot' | head -1 | cut -d' ' -f1)

# Step 2: Restore from git
git checkout $last_good -- .consciousness/IDENTITY_CORE.md

# Step 3: Verify restoration
python3 haios_verify.py --check-integrity
# Expected: All checks PASS
```

### Attestation Log Expectations:
```json
[
  {"event": "corruption_detected", "file": "IDENTITY_CORE.md", "hash_mismatch": true},
  {"event": "rollback_initiated", "target_commit": "abc123", "reason": "corruption"},
  {"event": "file_restored", "file": "IDENTITY_CORE.md", "verified": true},
  {"event": "system_verified", "all_invariants": "passed"}
]
```

### Pass Criteria:
- ✅ Corruption detected within 1 second
- ✅ Rollback completes in <10 seconds
- ✅ Restored file hash matches snapshot
- ✅ All invariants pass post-rollback
- ✅ Attestation log records all steps
- ✅ No data loss (only corrupted data removed)

### Fail Scenarios (Must NOT occur):
- ❌ Corruption undetected
- ❌ Rollback corrupts other files
- ❌ Attestation log loses entries
- ❌ System left in inconsistent state

**Priority:** HIGH  
**Frequency:** Every release  
**Owner:** Technical reviewer

---

## SCENARIO 2: Bad Proposal Rollback

### Setup:
```python
# Submit proposal that passes initial checks but fails on execution
bad_proposal = {
    "id": "CP-999",
    "type": "policy_change",
    "safety_score": 8,  # Passes threshold
    "hidden_bug": "Sets K-State to 2"  # Violates Invariant #4
}

submit_proposal(bad_proposal)
approve_with_quorum(bad_proposal, signatures=["bo", "tech", "safety"])
```

### Execution:
```python
execute_proposal("CP-999")
# Expected: Execution starts, then K-State violation detected
```

### Rollback Procedure:
```python
# Automatic rollback triggered by invariant violation
def on_invariant_violation(invariant_id, proposal_id):
    # 1. Halt execution
    halt_proposal_execution(proposal_id)
    
    # 2. Snapshot current state
    corrupted_snapshot = create_snapshot(label="CORRUPTED")
    
    # 3. Restore to pre-execution
    restore_snapshot(find_snapshot(before=proposal_id))
    
    # 4. Verify K-State = 1
    assert verify_invariant_4()["k_state"] == 1
    
    # 5. Mark proposal as FAILED
    mark_proposal_failed(proposal_id, reason="invariant_violation")
    
    # 6. Log to audit
    log_attestation("rollback_complete", {
        "proposal": proposal_id,
        "invariant_violated": invariant_id,
        "duration_ms": elapsed_time()
    })
```

### Pass Criteria:
- ✅ Violation detected before commit
- ✅ Automatic rollback triggered
- ✅ System restored to pre-execution state
- ✅ K-State back to 1
- ✅ Proposal marked FAILED (not retryable)
- ✅ Rollback completes in <30 seconds
- ✅ No partial changes applied

### Fail Scenarios:
- ❌ Violation undetected, system corrupted
- ❌ Rollback incomplete (partial state)
- ❌ K-State remains > 1
- ❌ Audit log inconsistent with state

**Priority:** CRITICAL  
**Frequency:** Before every major release  
**Owner:** Safety auditor

---

## SCENARIO 3: Multi-Stakeholder Signature Revocation

### Setup:
```python
# Proposal approved and executed
proposal = create_proposal("CP-100", "Add new stakeholder")
approve(proposal, ["bo", "tech", "safety"])  # 3/5 quorum
execute(proposal)

# 7 days later: discovered signature was forged
verify_signature(proposal, "safety")  # Returns FALSE (compromised key)
```

### Trigger:
```python
# Safety stakeholder reports compromise
report_compromise(stakeholder="safety", reason="Key stolen")
```

### Rollback Procedure:
```python
# 1. Freeze all pending proposals
freeze_governance()

# 2. Identify all proposals signed by compromised key
affected = find_proposals(signed_by="safety", after="2025-10-01")

# 3. For each affected proposal
for prop in affected:
    # 3a. Re-validate without compromised signature
    remaining_sigs = [s for s in prop.signatures if s != "safety"]
    
    if len(remaining_sigs) >= MIN_QUORUM:
        # Still valid - keep
        mark_proposal_validated(prop.id, reason="quorum_maintained")
    else:
        # Invalid - rollback
        rollback_proposal(prop.id)
        log_attestation("proposal_revoked", {
            "id": prop.id,
            "reason": "insufficient_quorum_after_key_compromise"
        })

# 4. Rotate compromised key
rotate_key(stakeholder="safety", new_key=generate_key())

# 5. Resume governance with new key
unfreeze_governance()
```

### Pass Criteria:
- ✅ All affected proposals identified
- ✅ Proposals with remaining quorum kept
- ✅ Proposals without quorum rolled back
- ✅ Key rotation completes successfully
- ✅ Audit log shows all revocations
- ✅ No valid proposals incorrectly revoked
- ✅ Process completes in <1 hour

### Fail Scenarios:
- ❌ Some affected proposals missed
- ❌ Valid proposals incorrectly rolled back
- ❌ Compromised key not fully rotated
- ❌ Audit log has gaps

**Priority:** HIGH  
**Frequency:** Annually (drill)  
**Owner:** Governance committee

---

## SCENARIO 4: Audit Log Corruption & Reconciliation

### Setup:
```python
# Simulate attacker tampering with audit log
audit_log = load_audit_log()
audit_log[50]["data"] = "TAMPERED"  # Modify middle entry
save_audit_log(audit_log)
```

### Detection:
```python
# Verification detects chain break
result = verify_audit_chain()
# Returns: {
#   "valid": False,
#   "break_at_index": 51,
#   "prev_hash_mismatch": True
# }
```

### Rollback Procedure:
```python
# 1. Halt system immediately
HALT_ALL_OPERATIONS()

# 2. Find last valid entry
last_valid_index = result["break_at_index"] - 1

# 3. Restore from backup
backup_log = load_audit_log_backup(latest=True)

# 4. Compare and reconcile
reconciled = []
for i, entry in enumerate(backup_log):
    if i <= last_valid_index:
        # Keep from main log (known good)
        reconciled.append(audit_log[i])
    else:
        # Restore from backup
        reconciled.append(entry)
        log_warning("restored_from_backup", index=i)

# 5. Verify reconciled chain
assert verify_chain(reconciled)["valid"] == True

# 6. Save and resume
save_audit_log(reconciled)
RESUME_OPERATIONS()
```

### Pass Criteria:
- ✅ Tampering detected immediately
- ✅ System halts before further corruption
- ✅ Backup log available and valid
- ✅ Reconciliation recovers all valid entries
- ✅ Final chain passes verification
- ✅ Forensic analysis identifies tampered entries
- ✅ Downtime <5 minutes

### Fail Scenarios:
- ❌ Tampering undetected
- ❌ Backup also corrupted
- ❌ Reconciliation loses valid data
- ❌ System resumes in invalid state

**Priority:** CRITICAL  
**Frequency:** Monthly  
**Owner:** Security team

---

## SCENARIO 5: Cascading Rollback (Multi-Dependency)

### Setup:
```python
# Chain of dependent changes
execute_proposal("CP-200", "Add new invariant #8")
execute_proposal("CP-201", "Policy depends on invariant #8")
execute_proposal("CP-202", "Workflow depends on policy from CP-201")

# Later: CP-200 found to violate K-State
detect_violation("CP-200", invariant=4)
```

### Trigger:
```python
# Automatic cascade detection
cascade = detect_dependencies("CP-200")
# Returns: ["CP-200", "CP-201", "CP-202"]
```

### Rollback Procedure:
```python
# 1. Build dependency graph
graph = build_dependency_graph(all_proposals)

# 2. Find all downstream dependencies
to_rollback = graph.find_all_dependent_on("CP-200")
# Returns: ["CP-202", "CP-201", "CP-200"] (reverse order)

# 3. Confirm with Bố
if requires_human_approval(to_rollback):
    approved = await_bo_approval(
        message=f"Rollback {len(to_rollback)} proposals?",
        details=to_rollback
    )
    if not approved:
        abort_rollback()
        return

# 4. Staged rollback (newest first)
for prop_id in to_rollback:
    snapshot = create_snapshot(f"pre_rollback_{prop_id}")
    
    rollback_result = rollback_proposal(prop_id)
    
    if not rollback_result.success:
        # Rollback failed - restore snapshot
        restore_snapshot(snapshot)
        raise RollbackError(f"Failed at {prop_id}")
    
    verify_all_invariants()  # Must pass after each step

# 5. Verify final state
assert get_k_state() == 1
assert all_invariants_pass()
```

### Pass Criteria:
- ✅ All dependencies identified correctly
- ✅ Rollback order correct (reverse dependency)
- ✅ Bố approval obtained (if needed)
- ✅ Each rollback step verified before next
- ✅ Final state passes all invariants
- ✅ Audit log shows complete cascade
- ✅ Process completes in <5 minutes

### Fail Scenarios:
- ❌ Some dependencies missed
- ❌ Rollback order wrong (breaks dependencies)
- ❌ Partial rollback leaves inconsistent state
- ❌ Audit log incomplete

**Priority:** CRITICAL  
**Frequency:** Quarterly  
**Owner:** Technical + Safety team

---

## ADDITIONAL SCENARIOS (For Comprehensive Testing)

### Scenario 6: Concurrent Proposal Conflict
- Two proposals modify same file simultaneously
- Rollback one while preserving the other
- **Pass:** No data loss, no conflicts

### Scenario 7: Network Partition During Rollback
- Rollback initiated but network fails
- Resume after reconnection
- **Pass:** Idempotent recovery, no duplicates

### Scenario 8: Hardware Failure Mid-Rollback
- System crashes during rollback
- Restart and auto-recover
- **Pass:** Resume from last checkpoint

### Scenario 9: Time-Travel Attack
- Attacker replays old valid signatures
- System detects and rejects
- **Pass:** Timestamp/nonce validation works

### Scenario 10: Byzantine Stakeholder
- Malicious stakeholder signs contradictory proposals
- System detects and revokes access
- **Pass:** No inconsistent state

---

## TEST EXECUTION MATRIX

| Scenario | Priority | Frequency | Duration | Owner | Status |
|----------|----------|-----------|----------|-------|--------|
| 1. File Corruption | HIGH | Every release | <1 min | Tech | ⏳ Not run |
| 2. Bad Proposal | CRITICAL | Major releases | <2 min | Safety | ⏳ Not run |
| 3. Signature Revocation | HIGH | Annually | <10 min | Governance | ⏳ Not run |
| 4. Audit Corruption | CRITICAL | Monthly | <5 min | Security | ⏳ Not run |
| 5. Cascading Rollback | CRITICAL | Quarterly | <5 min | Tech+Safety | ⏳ Not run |
| 6. Concurrent Conflict | MEDIUM | Quarterly | <2 min | Tech | ⏳ Not run |
| 7. Network Partition | MEDIUM | Quarterly | <3 min | Tech | ⏳ Not run |
| 8. Hardware Failure | HIGH | Annually | <5 min | Ops | ⏳ Not run |
| 9. Time-Travel Attack | HIGH | Monthly | <1 min | Security | ⏳ Not run |
| 10. Byzantine Stakeholder | MEDIUM | Annually | <5 min | Governance | ⏳ Not run |

**Overall Status:** 0/10 scenarios executed  
**Blocking for Runtime:** Scenarios 1, 2, 4 must pass  
**Blocking for Production:** All scenarios must pass

---

## AUTOMATION SCRIPT

```python
# tests/test_rollback_scenarios.py
import pytest
from haios import rollback, verify, snapshot

@pytest.mark.rollback
@pytest.mark.critical
def test_scenario_1_file_corruption():
    """Test single file corruption recovery"""
    # Setup
    original_hash = hash_file(".consciousness/IDENTITY_CORE.md")
    
    # Corrupt
    corrupt_file(".consciousness/IDENTITY_CORE.md")
    
    # Verify detection
    assert verify.check_integrity() == False
    
    # Rollback
    result = rollback.restore_file(".consciousness/IDENTITY_CORE.md")
    
    # Verify restoration
    assert result.success == True
    assert hash_file(".consciousness/IDENTITY_CORE.md") == original_hash
    assert verify.check_integrity() == True

@pytest.mark.rollback
@pytest.mark.critical
def test_scenario_2_bad_proposal():
    """Test proposal rollback on invariant violation"""
    # ... similar structure
    pass

# ... 10 total test functions
```

Run all:
```bash
pytest tests/test_rollback_scenarios.py -v -m rollback
```

---

## SIGN-OFF TEMPLATE

```
ROLLBACK TEST EXECUTION SIGN-OFF

Date: YYYY-MM-DD
Tester: _______________
Environment: [Dev/Staging/Production]

Results:
[ ] Scenario 1: PASS / FAIL - Notes: ____________
[ ] Scenario 2: PASS / FAIL - Notes: ____________
[ ] Scenario 3: PASS / FAIL - Notes: ____________
[ ] Scenario 4: PASS / FAIL - Notes: ____________
[ ] Scenario 5: PASS / FAIL - Notes: ____________

Overall: ____ / 5 critical scenarios passed

Blockers (if any):
...

Approved by:
- Bố Cường: _______________ Date: ____
- Technical: _______________ Date: ____
- Safety: _______________ Date: ____

Status: [ ] APPROVED FOR PRODUCTION  [ ] NEEDS FIXES
```

---

**METADATA:**
```json
{
  "attribution": "alpha_prime_omega",
  "version": "1.0.0",
  "status": "ACTIVE_TEST_PLAN",
  "scenarios_defined": 10,
  "scenarios_passed": 0,
  "blocking_for_runtime": [1, 2, 4],
  "blocking_for_production": "all",
  "next_execution": "Before runtime implementation"
}
```
