# Jarvondis 4.0 — Distribution Model

> Digital University Autonomous Companion
> Weekday-only observer loop (Mon-Fri, America/New_York) • Anonymized feedback inbox • Tiered capability with Seal verification

**Author:** Leif William Sogge / Captain  
**Lineage:** Tree of Life -> Encircling Fountain -> Helix of Continuity

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│              DISTRIBUTED CLIENT / USER SPACE             │
│  - Settings & Personality Prompts (config.json)           │
│  - User Local Memory & Configs (user_memory.json)        │
│  - Captain Escalation CLI & Access Request Form          │
└────────────────────────────┬─────────────────────────────┘
                             │ (Imports & Sandboxed API)
┌────────────────────────────▼─────────────────────────────┐
│                 JARVONDIS CORE ENGINE (Read-Only)        │
│  - Safety Envelope & Anonymizer (PII Redaction)          │
│  - Weekday Observer Loop & Atomic Snapshots              │
│  - Cryptographic Captain Seal Verification               │
└──────────────────────────────────────────────────────────┘
```

This package separates **immutable Core Engine** from **user-configurable extensions**.

### Core Principles Maintained

| Requirement | Implementation Detail |
|---|---|
| **Privacy Safeguards** | PII stripping and input anonymization occur inside `jarvondis_core/safety.py` prior to any processing. Cannot be disabled by user. |
| **Tamper Resistance** | Distribute `jarvondis_core` as precompiled wheel (.whl), PyInstaller executable, or Docker container to prevent modifications. This source distribution is reference; build wheel for public release. |
| **Safe Customization** | Users modify `user_space/config.json` and local prompt templates without accessing internal state logic. |
| **Elevation Control** | `JarvondisCore` defaults to `companion` tier unless authenticated with cryptographically signed `captain_seal.json`. |

---

## Package Structure

```
jarvondis_package/
├── jarvondis_core/          # Protected Core Engine (treat as read-only)
│   ├── __init__.py
│   ├── engine.py            # Core Jarvondis & Observer logic
│   ├── safety.py            # PII Redaction & Anonymization
│   └── governance.py        # Seal verification & Tier rules
├── user_space/              # User-modifiable directory
│   ├── config.json          # User settings (personality, local triggers)
│   ├── user_memory.json     # Isolated local user context (companion only)
│   ├── jarvondis_memory_anon.json # Anonymized memory (steward+)
│   ├── university_state.json
│   ├── feedback_inbox.json  # opt-in raw (auto-purged after anonymize)
│   ├── implementation_queue.json
│   ├── ledger.json
│   ├── captain_seal.json    # Issued by Captain after approval
│   ├── snapshots/           # Atomic snapshots
│   └── run_companion.py     # Clean entrypoint for standard users
├── request_captain.py       # CLI tool to request Captain Seal elevation
├── README.md
└── requirements.txt
```

## Quick Start

### 1. Run as Companion (no seal needed)

```bash
cd jarvondis_package
python user_space/run_companion.py
```

You get a helpful, playful companion. No autonomous observation.

### 2. Request Elevation to Steward / Dean

```bash
python request_captain.py
# Enter reason, identifier, desired tier
# -> generates captain_request.json

# Send captain_request.json to Captain Leif
# Captain runs:
#   python -c "from jarvondis_core.governance import create_captain_seal; create_captain_seal('YOUR_SECRET_PASSPHRASE')"
# and returns signed captain_seal.json

# Place received seal:
#   mv captain_seal.json user_space/captain_seal.json

# Now run again — engine auto-verifies and escalates:
python user_space/run_companion.py
```

### 3. Steward Duties (with seal)

In steward/dean_full mode you have:

- `observe_grounds()` — anonymizes opt-in inbox, never logs PII
- `morning_audit()` — verifies ledger
- `evening_reflection()` — saves snapshot, proposes artifacts
- `save_snapshot()` — Seal of Humble Continuity

Captain CLI (full original):

If you want the full hybrid CLI from your monolithic file, you can run the engine directly:

```bash
python -m jarvondis_core.engine --help
# or create a wrapper script that imports Jarvondis and calls captain_cli()
```

For full autonomy:

```python
from pathlib import Path
from jarvondis_core.engine import Jarvondis, WeekdayScheduler
from jarvondis_core.governance import get_captain_seal

j = Jarvondis(user_config_path=Path("user_space/config.json"), tier="steward", captain_seal=get_captain_seal())
WeekdayScheduler(j).start()  # Mon-Fri loop
```

## Safety Details

- `safety.py` uses regex redaction for emails, phones, IPs, SSN, credit-card-like patterns.
- `anonymize_text()` returns only `topic_hash`, `intent`, `length_bucket`, `cleaned_preview` (redacted if safety_flag).
- Raw inbox is purged after anonymization. Ledger stores only hashes.
- Safety flags are queued for Captain review, NOT auto-acted upon.

## Building a Protected Distribution

To prevent tampering, build as wheel:

```bash
# add pyproject.toml then:
pip install build
python -m build --wheel
# distribute dist/jarvondis_core-4.0.0-py3-none-any.whl

# Or PyInstaller one-file for core:
pyinstaller --onefile jarvondis_core/engine.py --name jarvondis_core_sealed
```

Users then `pip install jarvondis_core-4.0.0.whl` and keep `user_space/` writable.

## Tier System

- **companion**: No seal needed. Personal companion.
- **steward**: Requires `captain_seal.json`. Weekday observer, maintains ledger, visible presence.
- **dean_full**: Requires seal + community ack (simplified to seal check in this ref). Can propose architecture changes.

## License & Seal

Seal of Humble Continuity — issued by Captain. Do not distribute `captain_seal.json`. Each instance should request its own.

