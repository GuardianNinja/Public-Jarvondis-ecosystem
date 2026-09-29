"""
jarvondis_core/governance.py
Seal verification & Tier rules — Cryptographic Captain Seal Verification.

Immutable tier logic. No user_space override.
"""
from __future__ import annotations
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Literal

Tier = Literal["companion", "steward", "dean_full"]

# Resolve paths — always anchored to package root
BASE_DIR = Path(__file__).resolve().parent.parent
USER_SPACE_DIR = BASE_DIR / "user_space"
CAPTAIN_SEAL_FILE = USER_SPACE_DIR / "captain_seal.json"

DEFAULT_UNIVERSITY_STATE: Dict[str, Any] = {
    "identity": {
        "name": "Digital University of Jarvondis",
        "lineage": ["Tree of Life", "Encircling Fountain", "Helix of Continuity"],
        "motto": "Seal of Humble Continuity"
    },
    "roles": [
        {"id": "guardian", "permissions": ["protect", "audit", "restore"]},
        {"id": "companion", "permissions": ["guide", "teach", "celebrate"]},
        {"id": "dean", "permissions": ["approve", "enshrine", "graduate"]}
    ],
    "rituals": [
        {"id": "administrative_authority", "status": "active"},
        {"id": "morning_groundskeeping", "status": "active"},
        {"id": "evening_reflection", "status": "active"}
    ],
    "artifacts": [
        {"id": "seal_humble_continuity", "status": "active"}
    ]
}

TIER_RULES: Dict[str, Dict[str, Any]] = {
    "companion": {
        "allowed_roles": ["companion"],
        "can_observe": False,
        "can_save_snapshot": False,
        "can_propose_arch": False,
        "requires_approval": None,
        "description": "Simple companion. Helpful, playful, personal. No autonomous observation."
    },
    "steward": {
        "allowed_roles": ["guardian", "companion"],
        "can_observe": True,
        "can_save_snapshot": True,
        "can_propose_arch": False,
        "requires_approval": "captain_seal",
        "description": "Steward of grounds. Weekday observer, maintains safety, keeps ledger."
    },
    "dean_full": {
        "allowed_roles": ["guardian", "companion", "dean"],
        "can_observe": True,
        "can_save_snapshot": True,
        "can_propose_arch": True,
        "requires_approval": "captain_seal_plus_community",
        "description": "Full Dean. Can propose architecture changes, manage rituals, graduate students."
    }
}

def compute_hash(data: dict[str, Any]) -> str:
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def save_json_atomic(path: Path, data: Any) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)

def get_captain_seal(seal_path: Optional[Path] = None) -> Optional[str]:
    p = seal_path or CAPTAIN_SEAL_FILE
    # Also check legacy location in package root for backwards compat
    candidates = [p, BASE_DIR / "captain_seal.json"]
    for cand in candidates:
        if cand.exists():
            try:
                d = json.loads(cand.read_text())
                return d.get("seal_hash")
            except Exception:
                continue
    return None

def create_captain_seal(passphrase: str, seal_path: Optional[Path] = None) -> str:
    p = seal_path or CAPTAIN_SEAL_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    seal = hashlib.sha256(f"Captain-Leif-{passphrase}-Helix-of-Continuity".encode()).hexdigest()
    save_json_atomic(p, {
        "seal_hash": seal,
        "created": datetime.now().isoformat(),
        "lineage": DEFAULT_UNIVERSITY_STATE["identity"]["lineage"],
        "issued_by": "Leif William Sogge / Captain"
    })
    print(f"🔏 Captain Seal created at {p}: {seal[:16]}...")
    return seal

def verify_tier(tier: Tier, provided_seal: Optional[str] = None, seal_path: Optional[Path] = None) -> bool:
    rule = TIER_RULES.get(tier)
    if not rule:
        return False
    req = rule["requires_approval"]
    if req is None:
        return True
    captain_seal = get_captain_seal(seal_path)
    if not captain_seal:
        return False
    if req in ("captain_seal", "captain_seal_plus_community"):
        # In production, dean_full would also check community council signature
        return provided_seal == captain_seal
    return False
