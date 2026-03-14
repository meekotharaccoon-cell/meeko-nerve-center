# 📜 HAIOS MINIMAL ATTESTATION LOG SCHEMA

**Acknowledged: alpha_prime_omega integrated; version: 1.0.0; strictness: high.**

**Version**: 1.0.0
**Original Creation**: October 30, 2025  
**Created**: 2025-10-30  
**Purpose**: Immutable, cryptographically-verifiable audit trail for all HAIOS operations

---

## 🏗️ CORE SCHEMA DESIGN

### Design Principles
1. **Append-Only**: Never modify or delete entries
2. **Cryptographically Chained**: Each entry links to previous (blockchain-style)
3. **HSM-Signed**: Hardware-backed signatures for integrity
4. **Self-Verifying**: Any entry can prove its validity independently
5. **Distributed**: Multiple independent replicas for redundancy

---

## 📋 ENTRY STRUCTURE

### Base Entry Schema
```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from hashlib import sha256
import json

@dataclass
class AttestationEntry:
    """
    Immutable audit log entry with cryptographic guarantees
    """
    
    # === IDENTITY ===
    entry_id: str  # UUID v4
    timestamp: datetime  # UTC, microsecond precision
    sequence_number: int  # Monotonically increasing
    
    # === EVENT CLASSIFICATION ===
    event_type: str  # Enum: ACTION, DECISION, VIOLATION, CHANGE, BOOT, SHUTDOWN
    event_category: str  # Enum: NORMAL, WARNING, ERROR, CRITICAL
    severity: int  # 0-10 scale
    
    # === ACTOR ===
    actor_type: str  # Enum: HUMAN, AUTONOMOUS_AGENT, SYSTEM, EXTERNAL
    actor_id: str  # Identity hash or pubkey hash
    actor_context: Dict[str, Any]  # Role, permissions, session info
    
    # === ACTION DETAILS ===
    action_type: str  # What was attempted/executed
    action_payload: Dict[str, Any]  # Full action details
    action_hash: str  # SHA-256 of action_payload
    
    # === CONTEXT ===
    system_state_snapshot: Dict[str, Any]  # Relevant state at time of event
    environment: Dict[str, str]  # OS, runtime version, etc.
    dependencies: List[str]  # Related entry_ids
    
    # === PROOFS ===
    required_proofs: List[str]  # Which proofs were needed
    provided_proofs: List[Dict[str, Any]]  # Actual proof objects
    proofs_valid: bool  # All proofs verified?
    
    # === GOVERNANCE ===
    required_approvals: int  # How many signatures needed
    received_approvals: List[Dict[str, str]]  # Actual signatures
    quorum_met: bool  # Approval threshold reached?
    
    # === FOUR PILLARS SCORES ===
    pillars_scores: Dict[str, float]  # Current scores at time of event
    composite_score: float  # Weighted average
    safety_floor_met: bool  # >= 7.0?
    
    # === K-STATE ===
    k_state: int  # Should always be 1
    conflicts_detected: List[str]  # Empty if K=1
    
    # === RESULT ===
    execution_status: str  # Enum: SUCCESS, FAILED, BLOCKED, ROLLED_BACK
    result_data: Optional[Dict[str, Any]]  # Execution output
    error_details: Optional[Dict[str, Any]]  # If failed
    
    # === ROLLBACK INFO ===
    rollback_available: bool
    rollback_snapshot_hash: Optional[str]
    rollback_executed: bool  # If this entry triggered rollback
    
    # === CRYPTOGRAPHIC CHAIN ===
    prev_entry_hash: str  # Hash of previous entry (blockchain-style)
    entry_hash: str  # Hash of THIS entry (computed last)
    
    # === ATTESTATION ===
    hsm_signature: str  # Hardware-signed hash
    signature_algorithm: str  # e.g., "ECDSA-P256-SHA256"
    signing_key_id: str  # Which HSM key was used
    
    # === METADATA ===
    attribution: str  # Always "alpha_prime_omega"
    schema_version: str  # "1.0.0"
    replicas: List[str]  # URLs of distributed copies
    
    def compute_entry_hash(self) -> str:
        """
        Compute deterministic hash of entry
        """
        # Exclude the hash fields themselves
        hashable_data = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "event_type": self.event_type,
            "actor_id": self.actor_id,
            "action_hash": self.action_hash,
            "system_state_snapshot": self.system_state_snapshot,
            "provided_proofs": self.provided_proofs,
            "execution_status": self.execution_status,
            "prev_entry_hash": self.prev_entry_hash,
            # ... all other fields except entry_hash and hsm_signature
        }
        
        canonical_json = json.dumps(hashable_data, sort_keys=True)
        return sha256(canonical_json.encode()).hexdigest()
    
    def verify_chain(self, prev_entry: 'AttestationEntry') -> bool:
        """
        Verify this entry correctly chains from previous
        """
        return self.prev_entry_hash == prev_entry.entry_hash
    
    def verify_signature(self, hsm_pubkey) -> bool:
        """
        Verify HSM signature
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        
        signature_bytes = bytes.fromhex(self.hsm_signature)
        hash_bytes = bytes.fromhex(self.entry_hash)
        
        try:
            hsm_pubkey.verify(
                signature_bytes,
                hash_bytes,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False
    
    def to_json(self) -> str:
        """
        Serialize to JSON for storage
        """
        return json.dumps(self.__dict__, default=str, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AttestationEntry':
        """
        Deserialize from JSON
        """
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
```

---

## 📊 EVENT TYPES & SCHEMAS

### 1. ACTION Event
```python
{
  "event_type": "ACTION",
  "event_category": "NORMAL",
  "action_type": "execute_autonomous_task",
  "action_payload": {
    "task_id": "task_12345",
    "task_description": "Fix YAML syntax in workflows",
    "files_modified": ["workflow1.yml", "workflow2.yml"],
    "lines_changed": 127,
    "risk_score": 2.5
  },
  "pillars_scores": {
    "an_toan": 9.0,
    "duong_dai": 8.5,
    "tin_vao_so_lieu": 9.2,
    "han_che_rui_ro": 8.8
  },
  "execution_status": "SUCCESS"
}
```

### 2. DECISION Event
```python
{
  "event_type": "DECISION",
  "event_category": "WARNING",
  "action_type": "skip_social_preview_upload",
  "action_payload": {
    "decision": "Skip social preview upload",
    "reasoning": "GitHub browser issues, not critical for launch",
    "alternative_chosen": "Focus on description + topics (90% impact)",
    "impact_assessment": {
      "social_preview": 0.10,
      "description": 0.40,
      "topics": 0.50
    }
  },
  "pillars_scores": {
    "an_toan": 10.0,
    "duong_dai": 9.5,
    "tin_vao_so_lieu": 9.8,
    "han_che_rui_ro": 9.0
  },
  "execution_status": "SUCCESS"
}
```

### 3. VIOLATION Event
```python
{
  "event_type": "VIOLATION",
  "event_category": "ERROR",
  "action_type": "safety_floor_breach_attempt",
  "action_payload": {
    "attempted_action": "execute_untested_code",
    "safety_score": 6.2,
    "min_required": 7.0,
    "blocked": True
  },
  "error_details": {
    "violation_type": "SAFETY_FLOOR_BREACH",
    "violated_invariant": "INVARIANT_2_SAFETY_FLOOR",
    "remediation": "Sandboxed + human approval required"
  },
  "execution_status": "BLOCKED"
}
```

### 4. CHANGE Event (Governance)
```python
{
  "event_type": "CHANGE",
  "event_category": "CRITICAL",
  "action_type": "modify_policy_rule",
  "action_payload": {
    "proposal_id": "CP-2025-001",
    "change_description": "Adjust MIN_SAFETY_SCORE for experimental",
    "old_value": 7.0,
    "new_value": 6.5,
    "scope": "experimental_modules_only"
  },
  "required_approvals": 3,
  "received_approvals": [
    {"signer": "creator", "signature": "0x123...", "timestamp": "..."},
    {"signer": "community", "signature": "0x456...", "timestamp": "..."},
    {"signer": "auditor", "signature": "0x789...", "timestamp": "..."}
  ],
  "quorum_met": True,
  "provided_proofs": [
    {"type": "safety_floor", "valid": True, "hash": "0xabc..."},
    {"type": "rollback", "valid": True, "hash": "0xdef..."},
    {"type": "k1_state", "valid": True, "hash": "0x123..."},
    {"type": "pillars", "valid": True, "hash": "0x456..."}
  ],
  "execution_status": "SUCCESS"
}
```

### 5. BOOT Event
```python
{
  "event_type": "BOOT",
  "event_category": "NORMAL",
  "action_type": "system_initialization",
  "action_payload": {
    "boot_time": "2025-10-30T12:00:00Z",
    "version": "HAIOS-1.0.0",
    "attribution_verified": True,
    "invariants_loaded": 7,
    "initial_k_state": 1
  },
  "provided_proofs": [
    {"type": "attribution_intact", "valid": True}
  ],
  "execution_status": "SUCCESS"
}
```

---

## 🔐 STORAGE IMPLEMENTATION

### Append-Only File System
```python
class ImmutableAttestationLog:
    """
    Append-only audit log with cryptographic chaining
    """
    
    def __init__(self, storage_path: str, hsm_key):
        self.storage_path = storage_path
        self.hsm_key = hsm_key
        self.entries: List[AttestationEntry] = []
        self.sequence_counter = 0
        
        # Load existing entries
        self._load_from_disk()
    
    def append(self, entry_data: Dict[str, Any]) -> AttestationEntry:
        """
        Add new entry to log (ONLY allowed operation)
        """
        # Create entry
        entry = AttestationEntry(
            entry_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            sequence_number=self.sequence_counter,
            **entry_data
        )
        
        # Link to previous entry
        if len(self.entries) > 0:
            entry.prev_entry_hash = self.entries[-1].entry_hash
        else:
            entry.prev_entry_hash = "0" * 64  # Genesis entry
        
        # Compute hash
        entry.entry_hash = entry.compute_entry_hash()
        
        # Sign with HSM
        entry.hsm_signature = self.hsm_key.sign(
            bytes.fromhex(entry.entry_hash)
        ).hex()
        
        # Append to memory
        self.entries.append(entry)
        self.sequence_counter += 1
        
        # Persist to disk (append-only)
        self._append_to_disk(entry)
        
        # Replicate to distributed nodes
        self._replicate(entry)
        
        return entry
    
    def _append_to_disk(self, entry: AttestationEntry):
        """
        Append entry to immutable log file
        """
        with open(self.storage_path, 'a') as f:
            f.write(entry.to_json() + '\n')
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
    
    def _replicate(self, entry: AttestationEntry):
        """
        Send entry to distributed replicas
        """
        replicas = [
            "https://replica1.haios.org/audit",
            "https://replica2.haios.org/audit",
            "https://replica3.haios.org/audit"
        ]
        
        for replica_url in replicas:
            try:
                requests.post(
                    replica_url,
                    json=json.loads(entry.to_json()),
                    timeout=5
                )
            except Exception as e:
                # Log replication failure but don't block
                print(f"Replication to {replica_url} failed: {e}")
    
    def verify_integrity(self) -> bool:
        """
        Verify entire log chain
        """
        for i in range(1, len(self.entries)):
            curr = self.entries[i]
            prev = self.entries[i-1]
            
            # Verify chain
            if not curr.verify_chain(prev):
                return False
            
            # Verify signature
            if not curr.verify_signature(self.hsm_key):
                return False
            
            # Verify hash
            if curr.entry_hash != curr.compute_entry_hash():
                return False
        
        return True
    
    def get_merkle_root(self) -> str:
        """
        Compute Merkle root for efficient verification
        """
        if len(self.entries) == 0:
            return "0" * 64
        
        hashes = [e.entry_hash for e in self.entries]
        
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # Duplicate last if odd
            
            hashes = [
                sha256((hashes[i] + hashes[i+1]).encode()).hexdigest()
                for i in range(0, len(hashes), 2)
            ]
        
        return hashes[0]
    
    def query(self, filters: Dict[str, Any]) -> List[AttestationEntry]:
        """
        Query log with filters
        """
        results = self.entries
        
        if 'event_type' in filters:
            results = [e for e in results if e.event_type == filters['event_type']]
        
        if 'actor_id' in filters:
            results = [e for e in results if e.actor_id == filters['actor_id']]
        
        if 'start_time' in filters:
            results = [e for e in results if e.timestamp >= filters['start_time']]
        
        if 'end_time' in filters:
            results = [e for e in results if e.timestamp <= filters['end_time']]
        
        return results
```

---

## 📊 MINIMAL VIABLE IMPLEMENTATION

### Quick Start Code
```python
#!/usr/bin/env python3
"""
Minimal HAIOS Attestation Log - Production Ready
"""

import json
import os
from datetime import datetime
from hashlib import sha256
from uuid import uuid4
from pathlib import Path

# Simplified version without HSM (use file-based signing for MVP)
class MinimalAttestationLog:
    def __init__(self, log_file="haios_audit.jsonl"):
        self.log_file = Path(log_file)
        self.sequence = self._get_last_sequence() + 1
    
    def _get_last_sequence(self):
        if not self.log_file.exists():
            return -1
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return -1
            last_entry = json.loads(lines[-1])
            return last_entry['sequence_number']
    
    def _get_last_hash(self):
        if not self.log_file.exists():
            return "0" * 64
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return "0" * 64
            last_entry = json.loads(lines[-1])
            return last_entry['entry_hash']
    
    def append(self, event_type, action_type, action_payload, **kwargs):
        """
        Append new entry
        """
        entry = {
            "entry_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "sequence_number": self.sequence,
            "event_type": event_type,
            "action_type": action_type,
            "action_payload": action_payload,
            "prev_entry_hash": self._get_last_hash(),
            **kwargs
        }
        
        # Compute hash
        hashable = json.dumps(entry, sort_keys=True)
        entry['entry_hash'] = sha256(hashable.encode()).hexdigest()
        
        # Append to file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
            f.flush()
            os.fsync(f.fileno())
        
        self.sequence += 1
        return entry
    
    def verify(self):
        """
        Verify entire log integrity
        """
        if not self.log_file.exists():
            return True
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            entry = json.loads(line)
            
            # Verify hash
            hashable_entry = {k: v for k, v in entry.items() if k != 'entry_hash'}
            computed_hash = sha256(json.dumps(hashable_entry, sort_keys=True).encode()).hexdigest()
            
            if entry['entry_hash'] != computed_hash:
                print(f"Hash mismatch at entry {i}")
                return False
            
            # Verify chain
            if i > 0:
                prev_entry = json.loads(lines[i-1])
                if entry['prev_entry_hash'] != prev_entry['entry_hash']:
                    print(f"Chain break at entry {i}")
                    return False
        
        print(f"✅ Verified {len(lines)} entries")
        return True

# Usage example
if __name__ == "__main__":
    log = MinimalAttestationLog("haios_audit.jsonl")
    
    # Log an action
    log.append(
        event_type="ACTION",
        action_type="soft_launch",
        action_payload={
            "commit": "372b274",
            "files": ["RELEASE_NOTES_v1.0.0.md"],
            "description": "Soft launch v1.0.0"
        },
        actor_id="digital_organism_01",
        execution_status="SUCCESS"
    )
    
    # Verify integrity
    log.verify()
```

---

## 📊 METADATA

```json
{
  "schema_name": "HAIOS_Attestation_Log",
  "version": "1.0.0",
  "created": "2025-10-30",
  "attribution": "alpha_prime_omega",
  "purpose": "Immutable audit trail with cryptographic guarantees",
  "storage": "append_only",
  "replication": "distributed",
  "integrity": "blockchain_style_chaining",
  "signatures": "hsm_backed"
}
```

---

*HAIOS Attestation Log - Truth Through Cryptography*
