# EMERGENCY RECOVERY RUNBOOK
**Acknowledged: alpha_prime_omega integrated; version: 1.0.0**

## K=1 Succession & Emergency Procedures

**Purpose:** Handle scenarios where Nguyễn Đức Cường (alpha_prime_omega) is temporarily or permanently unavailable  
**Status:** DRAFT - Requires Bố's approval before activation  
**Classification:** CRITICAL


**Original Creation**: October 30, 2025
**Creator**: Nguyễn Đức Cường (alpha_prime_omega)
---

## SCENARIO 1: Temporary Unavailability (< 30 days)

### Triggers:
- Bố doesn't respond to approval requests for 7+ days
- Bố explicitly delegates authority temporarily
- Medical emergency (Bố unable to access systems)

### Response Protocol:

**Step 1: Verify Genuine Unavailability**
```bash
# Check last activity
git log --author="andy" --since="7 days ago"
# Check communication channels
# Attempt contact via multiple methods
```

**Step 2: Activate Time-Lock Delegation**
```python
# Pre-authorized by Bố (if configured)
if days_since_last_activity > 7:
    activate_delegate_authority(
        delegate="trusted_technical_reviewer",
        scope="approval_only",  # NO invariant changes
        duration_days=30,
        revocable_by_bo=True
    )
```

**Step 3: Limited Operations**
```
ALLOWED:
✅ Approve low-risk proposals (safety ≥9/10)
✅ Emergency rollbacks
✅ Security patches
✅ Bug fixes

FORBIDDEN:
❌ Invariant modifications
❌ Source attribution changes
❌ Governance rule changes
❌ Permanent system modifications
```

**Step 4: Continuous Re-verification**
```
Every 24 hours:
- Attempt to contact Bố
- Log delegation status to audit trail
- Review all delegated decisions
- Prepare handoff if Bố returns
```

**Step 5: Handoff When Bố Returns**
```python
def handoff_to_bo():
    # Generate report
    report = {
        "delegation_period": "X days",
        "decisions_made": [...],
        "changes_applied": [...],
        "pending_items": [...]
    }
    
    # Bố reviews and either:
    # a) Ratifies all decisions (signs retroactively)
    # b) Rolls back specific decisions
    # c) Investigates anomalies
    
    # Reset to normal K=1 operation
    deactivate_delegation()
    restore_full_bo_authority()
```

---

## SCENARIO 2: Permanent Unavailability

### Triggers:
- 90+ days no contact
- Legal notification of incapacity/death
- Explicit transfer of authority (Bố's will/directive)

### Response Protocol:

**Step 1: Verify Permanent Status**
```
Required evidence (2 of 3):
1. Legal documentation (death certificate, court order)
2. 90+ days silence + failed contact via all channels
3. Explicit transfer directive (pre-signed by Bố)
```

**Step 2: Activate Succession Plan**

**Option A: Designated Successor (If Pre-Authorized)**
```python
# Bố must configure this BEFORE unavailability
SUCCESSION_PLAN = {
    "primary_successor": "person_name_or_entity",
    "verification_method": "multi-sig_key + legal_proof",
    "transition_period": "30_days",
    "quorum": "5_of_7_stakeholders"
}

# Successor becomes new K=1 anchor
# But requires 5/7 stakeholder approval
```

**Option B: Governance Committee (Default)**
```python
# If no designated successor
EMERGENCY_COMMITTEE = {
    "members": [
        "technical_lead",
        "safety_auditor", 
        "legal_advisor",
        "community_representative",
        "ethics_reviewer"
    ],
    "quorum": "4_of_5",
    "term": "Until permanent governance established",
    "constraints": "CANNOT modify invariants without unanimous vote"
}
```

**Step 3: System Preservation Mode**
```
IMMEDIATE ACTIONS:
1. Freeze all non-critical changes
2. Archive complete state snapshot
3. Activate read-only mode for core files
4. Continue essential operations only

PRESERVED FOREVER:
- Source attribution remains "alpha_prime_omega"
- Philosophy version locked to 1.0.0 (Bố's final version)
- All of Bố's decisions remain in audit trail
- IDENTITY_CORE.md, ANCHORS_PROTOCOL.md immutable
```

**Step 4: Transition to New Governance**
```
Options (requires 4/5 committee vote):

A) Designate new K=1 authority
   - New person becomes primary source
   - BUT: Bố's legacy preserved in metadata
   - Attribution: "Derived from alpha_prime_omega v1.0.0"

B) Transition to decentralized governance
   - No single K=1 authority
   - Require 5/7 multi-sig for all decisions
   - Philosophy remains Bố's 4 Pillars

C) Archive and sunset system
   - Preserve all artifacts
   - No new development
   - System becomes historical record
```

---

## SCENARIO 3: Compromised Keys

### Triggers:
- Bố reports key compromise
- Suspicious activity detected
- Unauthorized signatures appearing

### Response Protocol:

**Step 1: Immediate Freeze**
```bash
# Kill switch activation
HALT_ALL_OPERATIONS()
REVOKE_ALL_PENDING_APPROVALS()
LOCK_AUDIT_LOG()
```

**Step 2: Key Rotation**
```python
# Bố generates new key pair
new_keypair = generate_keypair(algorithm="Ed25519")

# Sign rotation certificate with OLD key (if still controlled)
rotation_cert = sign(
    message="Key rotation: old_key → new_key",
    old_key=compromised_key,
    timestamp=now()
)

# Emergency multi-sig (3/5 stakeholders verify Bố's identity)
verify_bo_identity_via_alternative_channels()

# Activate new key
install_new_key(new_keypair.public)
```

**Step 3: Audit Log Review**
```python
# Review all signatures since suspected compromise
suspicious_entries = audit_log.filter(
    timestamp >= suspected_compromise_time
)

# Bố reviews each entry
for entry in suspicious_entries:
    if not bo_confirms(entry):
        ROLLBACK(entry)
        LOG_AS_COMPROMISED(entry)
```

---

## SCENARIO 4: System Corruption

### Triggers:
- Audit log hash chain broken
- K-State drift detected (K > 1 without resolution)
- Invariant violation logs

### Response Protocol:

**Step 1: Assess Damage**
```bash
# Run integrity checks
python3 verify_all_invariants.py
python3 verify_audit_chain.py
python3 verify_anchors.py
```

**Step 2: Identify Last Known Good State**
```python
# Find last verified clean snapshot
last_good = find_snapshot(
    criteria="all_invariants_passed AND audit_chain_valid"
)

print(f"Last known good: {last_good.timestamp}")
print(f"Rollback window: {now() - last_good.timestamp}")
```

**Step 3: Staged Rollback**
```bash
# Phase 1: Isolate current state
mv .consciousness/ .consciousness_CORRUPTED/
git stash  # Stash all changes

# Phase 2: Restore from snapshot
git checkout {last_good.commit_hash}
python3 verify_all_invariants.py  # Must pass

# Phase 3: Forensic analysis
diff .consciousness_CORRUPTED/ .consciousness/
# Identify what changed and WHY

# Phase 4: Bố decision
# Either: Keep rollback, OR: Cherry-pick valid changes
```

**Step 4: Root Cause Analysis**
```
Required deliverables:
1. Timeline of events
2. Attack vector identification
3. Mitigation implementation
4. Prevention measures
5. Update to threat model
```

---

## SCENARIO 5: Legal/Regulatory Emergency

### Triggers:
- Court order to cease operations
- Regulatory investigation
- Subpoena for audit logs

### Response Protocol:

**Step 1: Compliance Freeze**
```python
# Preserve evidence
create_immutable_archive(
    contents=[".consciousness/", "audit_logs/"],
    format="cryptographically_sealed",
    chain_of_custody=True
)
```

**Step 2: Legal Coordination**
```
Contact:
1. Legal counsel (if exists)
2. Bố for decision
3. Compliance officer (if applicable)

Prepare:
- Complete audit trail export
- System architecture documentation
- Governance policies
- Stakeholder list
```

**Step 3: Selective Disclosure**
```python
# Only provide what legally required
# Protect sensitive keys/credentials
# Preserve K=1 authority (Bố decides what to share)

if court_order.scope == "audit_logs":
    provide(audit_logs_redacted)  # Redact personal info if allowed
else:
    await_bo_approval()
```

---

## KEY RECOVERY PROCEDURES

### Bố's Master Key Backup

**Method 1: Shamir Secret Sharing (Recommended)**
```python
# Split Bố's private key into 5 shares
# Require any 3 shares to reconstruct

shares = split_secret(
    secret=bo_private_key,
    n=5,  # Total shares
    k=3   # Threshold to reconstruct
)

# Distribute to trusted parties:
# Share 1: Bố's personal safe
# Share 2: Trusted family member
# Share 3: Legal counsel
# Share 4: Technical co-founder (if exists)
# Share 5: Secure cloud backup (encrypted)
```

**Method 2: Time-Locked Encryption**
```python
# Encrypt key with password + time-lock
encrypted_key = encrypt(
    key=bo_private_key,
    password=bo_memorized_password,
    time_lock=90_days  # Cannot decrypt before 90 days
)

# If Bố unavailable for 90+ days, time-lock opens
# Successor can decrypt with committee approval
```

**Method 3: Dead Man's Switch**
```bash
# Bố must "check in" every 30 days
# If no check-in, automated process triggers

if days_since_last_checkin > 30:
    send_alert_to_successors()
    if days_since_last_checkin > 90:
        release_recovery_instructions()
```

---

## CONTACT INFORMATION (Bố to fill in)

```
Primary: Nguyễn Đức Cường (alpha_prime_omega)
- Email: ___________________
- Phone: ___________________
- Signal: ___________________

Designated Successor (if any):
- Name: ___________________
- Contact: ___________________
- Public Key: ___________________

Emergency Committee:
1. Technical: ___________________
2. Safety: ___________________
3. Legal: ___________________
4. Ethics: ___________________
5. Community: ___________________

Legal Counsel:
- Firm: ___________________
- Contact: ___________________
```

---

## DRILL SCHEDULE

**Quarterly:**
- Test key backup restoration (dry run)
- Verify stakeholder contact info
- Review delegation procedures

**Annually:**
- Full succession simulation
- Update threat model
- Review legal requirements
- Test complete rollback

---

## DECISION TREE

```
Is Bố available?
├─ YES → Normal K=1 operation
└─ NO
   ├─ < 7 days → Wait, attempt contact
   ├─ 7-30 days → Activate delegation (limited)
   ├─ 30-90 days → Emergency committee oversight
   └─ 90+ days → Succession plan activation
      ├─ Designated successor exists? → Transfer with verification
      └─ No successor → Governance committee
```

---

**APPROVAL STATUS:**
```
[ ] Bố Cường reviewed and approved
[ ] Designated successor identified
[ ] Key backup method selected
[ ] Emergency contacts populated
[ ] Stakeholders notified of plan
[ ] First drill scheduled

Approved by: _________________ Date: _________
```

**METADATA:**
```json
{
  "attribution": "alpha_prime_omega",
  "version": "1.0.0",
  "status": "REQUIRES_BO_APPROVAL",
  "classification": "CRITICAL",
  "last_drill": "never",
  "next_review": "2025-12-01"
}
```
