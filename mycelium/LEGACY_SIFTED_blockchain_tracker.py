import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List


LEDGER_DIR = "humanitarian_logs"
LEDGER_FILE = os.path.join(LEDGER_DIR, "humanitarian_ledger.jsonl")


def _ensure_ledger_dir() -> None:
    os.makedirs(LEDGER_DIR, exist_ok=True)


def _load_last_block() -> Optional[Dict[str, Any]]:
    """Return the last block in the local ledger, if any."""
    if not os.path.exists(LEDGER_FILE):
        return None

    last_line = None
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                last_line = line

    if not last_line:
        return None

    try:
        return json.loads(last_line)
    except json.JSONDecodeError:
        return None


def _hash_block(block: Dict[str, Any]) -> str:
    """Create a SHA-256 hash of a block's core content."""
    # We exclude the hash field itself if present
    data = {k: v for k, v in block.items() if k != "hash"}
    encoded = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def record_transaction(
    zone: str,
    organization: str,
    fiat_amount: float,
    crypto_amount: float,
    currency: str,
    wallet: str,
    tx_reference: str,
    smart_contract: Optional[Dict[str, Any]] = None,
    impact: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Append a transparent, blockchain-style block to the local ledger.

    This is not a real blockchain; it is an append-only hash-linked
    ledger that can be inspected by anyone for transparency.
    """
    _ensure_ledger_dir()
    previous_block = _load_last_block()
    previous_hash = previous_block["hash"] if previous_block else "GENESIS"

    block = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "zone": zone,
        "organization": organization,
        "fiat_amount": round(float(fiat_amount), 2),
        "crypto_amount": crypto_amount,
        "currency": currency,
        "wallet": wallet,
        "tx_reference": tx_reference,
        "previous_hash": previous_hash,
        "smart_contract": smart_contract or {},
        "impact": impact or {},
        "network": "local_humanitarian_chain",
        "version": 1,
    }

    block["hash"] = _hash_block(block)

    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(block, ensure_ascii=False) + "\n")

    return block


def summarize_ledger() -> Dict[str, Any]:
    """Return a simple summary of all aid transactions in the ledger."""
    if not os.path.exists(LEDGER_FILE):
        return {"total_fiat": 0.0, "by_zone": {}, "blocks": 0}

    total_fiat = 0.0
    by_zone: Dict[str, float] = {}
    blocks = 0

    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                blk = json.loads(line)
            except json.JSONDecodeError:
                continue
            blocks += 1
            amt = float(blk.get("fiat_amount", 0.0))
            total_fiat += amt
            zone = blk.get("zone", "unknown")
            by_zone[zone] = by_zone.get(zone, 0.0) + amt

    return {
        "total_fiat": round(total_fiat, 2),
        "by_zone": {z: round(a, 2) for z, a in by_zone.items()},
        "blocks": blocks,
    }


def get_ledger() -> List[Dict[str, Any]]:
    """Return the full ledger as a list of blocks."""
    if not os.path.exists(LEDGER_FILE):
        return []

    blocks: List[Dict[str, Any]] = []
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                blocks.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return blocks


if __name__ == "__main__":
    # Simple CLI check
    summary = summarize_ledger()
    print("Humanitarian ledger summary:")
    print(json.dumps(summary, indent=2))

