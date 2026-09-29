"""
request_captain.py
Safe Escalation Pathway — Captain Elevation Request CLI

Generates a Elevation Request Bundle containing a request token.
User sends captain_request.json to Captain (Leif), who signs and returns captain_seal.json

Usage:
    python request_captain.py
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
USER_SPACE = BASE_DIR / "user_space"
USER_SPACE.mkdir(exist_ok=True)

def generate_elevation_request():
    print("=== Jarvondis Captain Access Request ===")
    print("This generates a signed request bundle for Steward/Dean elevation.")
    print("No core logic is exposed. Only a hashed request is sent to Captain.\n")

    reason = input("State your reason for requesting Steward/Dean access: ").strip()
    if not reason:
        reason = "General interest in stewardship"

    user_id = input("Enter your identifier/email: ").strip()
    if not user_id:
        user_id = "anonymous@local.instance"

    tier_requested = input("Requested tier [steward/dean_full] (default: steward): ").strip().lower()
    if tier_requested not in ["steward", "dean_full"]:
        tier_requested = "steward"

    timestamp = datetime.now().isoformat()
    raw = f"{user_id}-{reason}-{tier_requested}-{timestamp}"
    request_hash = hashlib.sha256(raw.encode()).hexdigest()

    request_data = {
        "schema_version": "4.0.0",
        "timestamp": timestamp,
        "user_id": user_id,
        "reason": reason,
        "tier_requested": tier_requested,
        "request_hash": request_hash[:16],
        "request_hash_full": request_hash,
        "lineage_ack": ["Tree of Life", "Encircling Fountain", "Helix of Continuity"],
        "safety_ack": "I understand that PII redaction and Safety Envelope cannot be disabled and that steward/dean tiers require visible presence and weekday-only observation."
    }

    req_file = BASE_DIR / "captain_request.json"
    req_file.write_text(json.dumps(request_data, indent=2))
    
    # Also copy to user_space for record
    (USER_SPACE / "captain_request.json").write_text(json.dumps(request_data, indent=2))

    print(f"\n✅ Request generated successfully: {req_file.name}")
    print(f"   Full hash: {request_hash}")
    print(f"   Tier requested: {tier_requested}")
    print("📩 Submit this file to your Captain (Leif William Sogge).")
    print("   Once approved, you will receive a signed `captain_seal.json` to place in user_space/")

if __name__ == "__main__":
    generate_elevation_request()
