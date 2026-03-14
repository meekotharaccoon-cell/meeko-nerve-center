# PROOF LEVEL ACCEPTANCE CRITERIA
**Acknowledged: alpha_prime_omega integrated; version: 1.0.0**

## Purpose
Define measurable, auditable criteria for each proof level (0-4) referenced in HAIOS_THREAT_MODEL.md.


**Original Creation**: October 30, 2025
**Creator**: Nguyễn Đức Cường (alpha_prime_omega)
---

## LEVEL 0: INFORMAL (Documentation Only)

### Artifacts Required:
- [ ] Written specification of invariant in natural language
- [ ] Example scenarios showing expected behavior
- [ ] Known limitations documented

### Verification Steps:
1. Human review by Bố Cường
2. Peer review by 1+ technical stakeholder
3. No contradictions with other specs

### Sign-off Authority:
- **Minimum:** Bố Cường (K=1 authority)
- **Recommended:** +1 technical reviewer

### Acceptance Criteria:
- ✅ Spec is clear and unambiguous
- ✅ Examples cover normal + edge cases
- ✅ Limitations are explicitly stated

**Current Status:** All 7 invariants at Level 0  
**Risk:** HIGH - No executable verification  
**Acceptable for:** Initial design phase only

---

## LEVEL 1: Unit Tests

### Artifacts Required:
- [ ] Python test suite (pytest or unittest)
- [ ] Test coverage ≥90% for invariant code
- [ ] All tests passing in CI
- [ ] Test data includes edge cases

### Verification Steps:
```bash
# Run test suite
pytest tests/test_invariant_{N}.py -v --cov

# Requirements:
# - All tests PASS
# - Coverage ≥90%
# - No skipped tests
# - Runtime <5 seconds per invariant
```

### Test Categories Required:
1. **Happy path** (invariant holds)
2. **Violation detection** (invariant broken → error raised)
3. **Edge cases** (boundary conditions)
4. **Error handling** (graceful failures)

### Sign-off Authority:
- **Minimum:** Bố + 1 technical reviewer
- **CI:** Automated pass required

### Acceptance Criteria:
- ✅ pytest run shows 100% pass rate
- ✅ Coverage report ≥90%
- ✅ All edge cases documented and tested
- ✅ Error messages are actionable

### Example Test Structure:
```python
# tests/test_invariant_1.py
import pytest
from haios.invariants import verify_invariant_1

def test_attribution_valid():
    """Test valid attribution passes"""
    state = {"source": "alpha_prime_omega", "signature": valid_sig}
    result = verify_invariant_1(state)
    assert result["valid"] == True

def test_attribution_missing():
    """Test missing attribution fails"""
    state = {"source": None}
    result = verify_invariant_1(state)
    assert result["valid"] == False
    assert result["error"] == "ERR_INVARIANT_1_VIOLATION"

def test_attribution_wrong_source():
    """Test wrong source detected"""
    state = {"source": "evil_attacker"}
    result = verify_invariant_1(state)
    assert result["valid"] == False
    
# ... 10+ more tests covering all scenarios
```

**Target:** Invariants #1-6 by end of November 2025  
**Risk:** MEDIUM - Catches implementation bugs, not design flaws  
**Acceptable for:** Development & testing environments

---

## LEVEL 2: Property-Based Tests

### Artifacts Required:
- [ ] Hypothesis (Python) or QuickCheck property tests
- [ ] 10,000+ random inputs generated and tested
- [ ] Shrinking demonstrates minimal failing case
- [ ] Properties formally stated

### Verification Steps:
```python
from hypothesis import given, strategies as st

@given(st.text(), st.integers(), st.lists(st.booleans()))
def test_audit_chain_integrity(event_data, timestamp, flags):
    """Property: Audit chain never accepts tampered entries"""
    log = AttestationLog()
    
    # Add valid entry
    log.append("test", {"data": event_data})
    
    # Tamper with it
    log.entries[-1]["data"] = "TAMPERED"
    
    # Property: verify_chain MUST fail
    assert log.verify_chain() == False
```

### Properties to Prove:
1. **Idempotence:** Applying same operation twice = same result
2. **Commutativity:** Order doesn't matter (if applicable)
3. **Invariant preservation:** Operation maintains invariant
4. **Boundary safety:** No crashes on extreme inputs

### Sign-off Authority:
- **Minimum:** Bố + 2 reviewers (1 technical, 1 safety)
- **Automated:** Hypothesis runs in CI

### Acceptance Criteria:
- ✅ 10,000+ examples tested without failure
- ✅ Shrinking finds minimal counterexample if any
- ✅ Properties cover all critical paths
- ✅ Runtime <60 seconds total

**Target:** Invariants #3, #7 by Q1 2026  
**Risk:** LOW - Finds subtle bugs unit tests miss  
**Acceptable for:** Pre-production staging

---

## LEVEL 3: Model Checking

### Artifacts Required:
- [ ] TLA+ or Alloy formal specification
- [ ] TLC model checker verification proof
- [ ] All safety properties checked
- [ ] All liveness properties checked

### Verification Steps:
```tla
---- MODULE HAIOS_Governance ----
EXTENDS Integers, Sequences, FiniteSets

CONSTANTS Stakeholders, MinQuorum

VARIABLES 
    proposals,      \* Set of pending proposals
    approvals,      \* Function: proposal -> set of signers
    executed        \* Set of executed proposals

(* Safety: No proposal executes without quorum *)
SafetyProperty == 
    \A p \in executed :
        Cardinality(approvals[p]) >= MinQuorum

(* Liveness: Valid proposals eventually execute or timeout *)
LivenessProperty ==
    \A p \in proposals :
        <>(p \in executed \/ Timeout(p))

(* Deadlock freedom *)
DeadlockFree ==
    \A p \in proposals :
        ENABLED Approve(p) \/ ENABLED Reject(p)
====
```

Run TLC:
```bash
tlc HAIOS_Governance.tla -config HAIOS_Governance.cfg

# Expected output:
# Model checking completed. No errors found.
# States explored: 2,456,789
# Distinct states: 1,234,567
```

### Properties to Check:
1. **Safety:** Bad states never reachable
2. **Liveness:** Good states eventually reached
3. **Deadlock freedom:** System never stuck
4. **Fairness:** All stakeholders get turns

### Sign-off Authority:
- **Minimum:** Bố + formal methods expert
- **External:** Model checked by independent verifier

### Acceptance Criteria:
- ✅ TLC completes without errors
- ✅ All safety properties proven
- ✅ All liveness properties proven
- ✅ State space fully explored (or bounded)
- ✅ Independent reviewer confirms model

**Target:** Invariants #1, #4, #6 by Q2 2026  
**Risk:** VERY LOW - Mathematical proof of correctness  
**Acceptable for:** Production deployment

---

## LEVEL 4: Formal Proof (Mechanized)

### Artifacts Required:
- [ ] Coq, Lean, or Isabelle/HOL proof
- [ ] Proof script compiles without errors
- [ ] All lemmas proven
- [ ] Extracted code matches implementation

### Verification Steps:
```coq
(* Coq proof example *)
Require Import Coq.Lists.List.
Import ListNotations.

(* Definition: Attestation log *)
Inductive LogEntry : Type :=
  | Entry (id: nat) (data: string) (prev_hash: string) (hash: string).

(* Invariant: Hash chain integrity *)
Definition chain_valid (log: list LogEntry) : Prop :=
  forall i, i < length log - 1 ->
    match nth i log, nth (i+1) log with
    | Entry _ _ _ h1, Entry _ _ ph2 _ => h1 = ph2
    | _, _ => False
    end.

(* Theorem: Appending preserves chain validity *)
Theorem append_preserves_chain :
  forall log e,
    chain_valid log ->
    (match last log with
     | Some (Entry _ _ _ h) => 
         chain_valid (log ++ [Entry (length log) "data" h "new_hash"])
     | None => True
     end).
Proof.
  intros log e Hvalid.
  (* ... proof steps ... *)
Qed.
```

Compile:
```bash
coqc attestation_log.v

# Expected: No errors
```

### Proof Requirements:
1. **Correctness:** Implementation matches specification
2. **Completeness:** All critical properties proven
3. **Termination:** All functions proven to terminate
4. **Extraction:** Can extract verified code to OCaml/Haskell

### Sign-off Authority:
- **Minimum:** Bố + 2 formal verification experts
- **Publication:** Accepted in peer-reviewed venue (optional)

### Acceptance Criteria:
- ✅ Proof compiles in Coq/Lean/Isabelle
- ✅ All theorems proven (no Admitted)
- ✅ Extracted code matches production code
- ✅ Independent experts reviewed proof
- ✅ Proof published or archived (DOI/arXiv)

**Target:** Invariant #1 (Attribution) by Q3 2026 (aspirational)  
**Risk:** MINIMAL - Highest assurance possible  
**Acceptable for:** Critical infrastructure, high-security deployments

---

## TRANSITION MATRIX

| From Level | To Level | Trigger | Effort | Timeline |
|------------|----------|---------|--------|----------|
| 0 → 1 | Unit tests | Before runtime implementation | 2-3 weeks | Nov 2025 |
| 1 → 2 | Property tests | Before production | 1-2 weeks | Q1 2026 |
| 2 → 3 | Model checking | Before critical deployment | 4-6 weeks | Q2 2026 |
| 3 → 4 | Formal proof | For high-assurance use | 3-6 months | Q3 2026 |

---

## CURRENT STATUS & ROADMAP

```
INVARIANT #1 (Attribution):
  Current: Level 0
  Target: Level 3 (Model checked)
  Next step: Unit tests (2 weeks)
  
INVARIANT #2 (Safety Floor):
  Current: Level 0
  Target: Level 1 (Unit tests)
  Next step: Write test suite (1 week)
  
INVARIANT #3 (Rollback):
  Current: Level 0
  Target: Level 2 (Property-based)
  Next step: Unit tests → Property tests (3 weeks)
  
INVARIANT #4 (K-State):
  Current: Level 0
  Target: Level 3 (Model checked)
  Next step: Unit tests (2 weeks)
  
INVARIANT #5 (4 Pillars):
  Current: Level 0
  Target: Level 1 (Unit tests)
  Next step: Write test suite (1 week)
  
INVARIANT #6 (Multi-sig):
  Current: Level 0
  Target: Level 3 (Model checked)
  Next step: Unit tests (2 weeks)
  
INVARIANT #7 (Audit Trail):
  Current: Level 0
  Target: Level 2 (Property-based)
  Next step: Unit tests → Property tests (3 weeks)
```

**Overall Progress:** 0% (0/7 at target level)  
**Blocking for Runtime:** Unit tests (Level 1) for all  
**Blocking for Production:** Property/Model (Level 2-3) for all

---

## SIGN-OFF TEMPLATE

For each invariant reaching target level:

```
INVARIANT #X VERIFICATION SIGN-OFF

Level Achieved: [0/1/2/3/4]
Date: YYYY-MM-DD

Artifacts:
- [ ] Tests passing (link to CI run)
- [ ] Coverage ≥90% (link to report)
- [ ] Model checked (link to TLC output)
- [ ] Proof compiled (link to Coq script)

Reviewers:
- Bố Cường (K=1): _______________ Date: ____
- Technical: _______________ Date: ____
- Safety (if Level 2+): _______________ Date: ____
- Formal Methods (if Level 3+): _______________ Date: ____

Status: [ ] APPROVED  [ ] REJECTED  [ ] NEEDS REVISION

Comments:
...
```

---

**METADATA:**
```json
{
  "attribution": "alpha_prime_omega",
  "version": "1.0.0",
  "status": "ACTIVE_STANDARD",
  "applies_to": "All HAIOS invariants",
  "review_frequency": "Quarterly",
  "next_review": "2026-02-01"
}
```
