"""
captain_console.py — Full Captain CLI wrapper around Jarvondis 4.0 core

Usage:
  python captain_console.py seal --passphrase <secret>
  python captain_console.py observe --tier steward --seal <hash>
  python captain_console.py run --tier steward
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvondis_core.engine import Jarvondis, WeekdayScheduler, Personality
from jarvondis_core.governance import get_captain_seal, create_captain_seal, load_json

def main():
    parser = argparse.ArgumentParser(description="Jarvondis 4.0 — Captain's Console")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("observe", help="Run one observation cycle (anonymize inbox)")
    sub.add_parser("audit", help="Run morning audit")
    sub.add_parser("reflect", help="Run evening reflection + snapshot")
    sub.add_parser("run", help="Start autonomous weekday scheduler")
    sub.add_parser("review", help="Review anonymized feedback & safety flags")
    sub.add_parser("clear", help="Clear raw feedback inbox (PII purge)")
    
    seal_parser = sub.add_parser("seal", help="Create Captain Seal")
    seal_parser.add_argument("--passphrase", required=True, help="Secret passphrase")

    feedback_parser = sub.add_parser("feedback", help="Simulate opt-in feedback")
    feedback_parser.add_argument("text", nargs="+")

    parser.add_argument("--tier", default="companion", choices=["companion", "steward", "dean_full"])
    parser.add_argument("--seal", default=None, help="Captain seal hash")
    parser.add_argument("--tone", default=None)

    args = parser.parse_args()

    if args.cmd == "seal":
        create_captain_seal(args.passphrase)
        return

    personality = Personality(tone=args.tone) if args.tone else None
    config_path = ROOT / "user_space" / "config.json"
    j = Jarvondis(user_config_path=config_path, tier=args.tier, personality=personality, captain_seal=args.seal or get_captain_seal())

    if args.cmd == "observe":
        j.observe_grounds()
    elif args.cmd == "audit":
        j.morning_audit()
    elif args.cmd == "reflect":
        j.evening_reflection()
    elif args.cmd == "run":
        WeekdayScheduler(j).start()
    elif args.cmd == "review":
        from jarvondis_core.governance import load_json as lj
        mem = lj(j.memory_file, [])
        queue = lj(j.implementation_queue, [])
        print(f"\n=== Captain's Review — {len(mem)} anonymized memories ===")
        for m in mem[-20:]:
            print(f"- {m.get('timestamp')} | {m.get('anon', {}).get('intent')} | {m.get('anon', {}).get('cleaned_preview')}")
        print(f"\n=== Implementation Queue — {len(queue)} ===")
        for i, q in enumerate(queue[-20:]):
            print(f"{i}: {q}")
        if j.safety_flag_count:
            print(f"\n🚨 {j.safety_flag_count} safety flags require review")
    elif args.cmd == "clear":
        from jarvondis_core.governance import save_json_atomic
        save_json_atomic(j.feedback_inbox, [])
        print("🧹 Raw feedback inbox purged")
    elif args.cmd == "feedback":
        from jarvondis_core.governance import save_json_atomic, load_json
        text = " ".join(args.text)
        inbox = load_json(j.feedback_inbox, [])
        from datetime import datetime
        inbox.append({"timestamp": datetime.now().isoformat(), "text": text, "source": "opt-in-test"})
        save_json_atomic(j.feedback_inbox, inbox)
        print("📝 Feedback queued")
    else:
        print("\nJarvondis 4.0 Interactive — type 'exit' to quit")
        while True:
            try:
                ui = input("\nCaptain > ").strip()
                if ui.lower() in ["exit", "quit"]:
                    break
                if not ui:
                    continue
                print(j.respond(ui))
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()
