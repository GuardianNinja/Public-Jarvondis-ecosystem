"""
user_space/run_companion.py
Clean entrypoint for standard users — runs strictly in companion tier unless seal present.

Usage:
    python user_space/run_companion.py
    python -m user_space.run_companion
"""
from pathlib import Path
import sys

# Ensure package root is on path when run directly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvondis_core.engine import JarvondisCore, Personality
from jarvondis_core.governance import get_captain_seal

CONFIG_PATH = Path(__file__).parent / "config.json"

def main():
    seal = get_captain_seal()
    # Default to companion; if valid seal exists, user may choose steward (verified inside engine)
    tier = "companion"
    if seal:
        # Auto-escalate if config allows — engine will still verify
        tier = "steward"

    companion = JarvondisCore(user_config_path=CONFIG_PATH, tier=tier, captain_seal=seal)

    print("✨ Jarvondis Companion active. Type 'exit' to quit or 'request-access' to escalate.")
    print(f"   Config: {CONFIG_PATH}")
    print(f"   Seal: {'FOUND ' + seal[:16] + '...' if seal else 'none (companion mode)'}")
    while True:
        try:
            user_input = input("\nYou > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🛑 Companion resting.")
            break

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Seal of Humble Continuity — until next time.")
            break
        elif user_input.lower() == "request-access":
            print("\n📌 Run 'python request_captain.py' from package root to submit an elevation request.")
            continue
        elif user_input.lower() == "review":
            # local quick review
            from jarvondis_core.governance import load_json
            mem = load_json(companion.memory_file, [])
            print(f"   {len(mem)} anonymized memories stored.")
            continue
        elif not user_input:
            continue

        print(companion.respond(user_input))

if __name__ == "__main__":
    main()
