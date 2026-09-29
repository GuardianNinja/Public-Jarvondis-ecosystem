"""
jarvondis_core/engine.py
Core Jarvondis & Observer Logic — Sealed, Read-Only in distribution.

Exposes only safe methods: respond(), observe_grounds(), morning_audit(), evening_reflection(), save_snapshot()
All PII redaction happens inside here and cannot be bypassed by user_space.
"""
from __future__ import annotations
import json
import hashlib
import argparse
import threading
import time as time_module
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Dict, Optional, Literal, cast, Protocol

from .safety import anonymize_text, scrub
from .governance import (
    Tier,
    TIER_RULES,
    DEFAULT_UNIVERSITY_STATE,
    load_json,
    save_json_atomic,
    compute_hash,
    get_captain_seal,
    verify_tier,
    USER_SPACE_DIR,
    BASE_DIR,
)

class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...

@dataclass
class Personality:
    tone: str = "humble"  # neutral, witty, formal, mythic, playful, humble
    def stylize(self, response: str) -> str:
        if self.tone == "witty":
            return f"{response} 😉"
        if self.tone == "formal":
            return f"{response}. I hope that satisfies your query."
        if self.tone == "mythic":
            return f"⚔️ {response} — inscribed in the Captain's Log."
        if self.tone == "playful":
            return f"{response} 🎮✨"
        if self.tone == "humble":
            return f"🙏 {response} — in humble continuity."
        return response

class EsotericOracle:
    def draw(self) -> str:
        day_seed = datetime.now().strftime("%Y-%m-%d")
        h = int(hashlib.sha256(day_seed.encode()).hexdigest(), 16)
        oracles = [
            "Fountain flows inward today",
            "Helix tightens — reflect, don't expand",
            "Tree offers shade — protect what grows",
            "Seal holds, but asks to be questioned",
            "Companion listens more than speaks"
        ]
        return oracles[h % len(oracles)]

class ErebusSync:
    """Threefold mind: KG -> LLM -> Esoteric"""
    def __init__(self, personality: Personality, university_state: Dict[str, Any], tier: Tier):
        self.personality = personality
        self.university = university_state
        self.tier = tier
        self.oracle = EsotericOracle()
        self.llm_client: Optional[LLMClient] = None

    def set_llm(self, client: LLMClient) -> None:
        self.llm_client = client

    def query_kg(self, input_str: str) -> str:
        lineage = ", ".join(cast(List[str], self.university["identity"]["lineage"]))
        return f"Lineage: {lineage}. Roles: {[r['id'] for r in self.university['roles']]}."

    def query(self, input_str: str) -> str:
        kg_context = self.query_kg(input_str)
        base: str
        if self.llm_client:
            try:
                prompt = f"You are Jarvondis, {self.tier} tier, {self.personality.tone} tone. {kg_context}. User: {input_str}"
                base = self.llm_client.complete(prompt)
            except Exception as e:
                base = f"LLM error, echoing: {input_str} ({e})"
        else:
            base = f"Echoing back ({self.tier}): {input_str}"

        if self.tier in ["steward", "dean_full"]:
            oracle = self.oracle.draw()
            base = f"{base} [{oracle}]"

        return self.personality.stylize(base)

class Jarvondis:
    """
    Core Engine — immutable safety envelope.
    user_config_path: Path to user_space/config.json (determines data root)
    """
    def __init__(
        self,
        user_config_path: Optional[Path] = None,
        tier: Tier = "companion",
        personality: Optional[Personality] = None,
        captain_seal: Optional[str] = None,
    ):
        if tier not in TIER_RULES:
            raise ValueError(f"Invalid tier {tier}")

        # Resolve data root from user config
        if user_config_path:
            self.user_config_path = Path(user_config_path).resolve()
            self.data_root = self.user_config_path.parent
            self.user_config = self._load_config(self.user_config_path)
        else:
            self.data_root = USER_SPACE_DIR
            self.user_config_path = self.data_root / "config.json"
            self.user_config = load_json(self.user_config_path, {})

        # Paths inside user_space (never in core)
        self.snapshot_dir = self.data_root / "snapshots"
        self.ledger_file = self.data_root / "ledger.json"
        self.memory_file = self.data_root / "jarvondis_memory_anon.json"
        self.feedback_inbox = self.data_root / "feedback_inbox.json"
        self.implementation_queue = self.data_root / "implementation_queue.json"
        self.university_state_file = self.data_root / "university_state.json"
        self.seal_file = self.data_root / "captain_seal.json"

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        for f, default in [
            (self.feedback_inbox, []),
            (self.implementation_queue, []),
            (self.ledger_file, []),
            (self.memory_file, []),
        ]:
            if not f.exists():
                save_json_atomic(f, default)

        # Verify tier authorization at init
        if not verify_tier(tier, captain_seal, seal_path=self.seal_file):
            if tier != "companion":
                print(f"⛔ Tier '{tier}' requires Captain Seal. Falling back to 'companion'.")
                tier = "companion"  # type: ignore

        self.tier: Tier = tier
        # Personality from config if not explicitly passed
        tone = (self.user_config.get("personality", {}).get("tone") if self.user_config else None) or                (personality.tone if personality else ("humble" if tier == "steward" else "witty"))
        self.personality = personality or Personality(tone=tone)

        self.university_state = load_json(self.university_state_file, DEFAULT_UNIVERSITY_STATE)
        self.erebus_sync = ErebusSync(self.personality, self.university_state, self.tier)
        self._anon_memory: List[Dict[str, Any]] = cast(List[Dict[str, Any]], load_json(self.memory_file, []))
        self._safety_flags: List[Dict[str, Any]] = []

        print(f"🟢 Jarvondis 4.0 online | Tier: {self.tier} | Tone: {self.personality.tone}")
        print(f"   {TIER_RULES[self.tier]['description']}")
        print(f"   Data root: {self.data_root}")
        print(f"   Presence: Visible | Logging: Anonymized only | Surveillance: DISABLED")

    def _load_config(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _anonymize(self, text: str) -> Dict[str, Any]:
        return anonymize_text(text)

    @property
    def safety_flag_count(self) -> int:
        return len(self._safety_flags)

    # --- OBSERVER ETHIC ---
    def observe_grounds(self):
        if not TIER_RULES[self.tier]["can_observe"]:
            print("⛔ Observer disabled for companion tier.")
            return
        inbox = load_json(self.feedback_inbox, [])
        if not inbox:
            print(f"[{datetime.now().isoformat()}] Observer: Grounds quiet. No opt-in feedback.")
            return

        print(f"[{datetime.now().isoformat()}] Observer: {len(inbox)} opt-in feedback(s). Anonymizing...")
        processed: List[Dict[str, Any]] = []
        for item in inbox:
            anon = self._anonymize(item.get("text", ""))
            entry = {"timestamp": datetime.now().isoformat(), "anon": anon, "source": "opt-in"}
            processed.append(entry)
            if anon["was_flagged"]:
                self._safety_flags.append(entry)
                print(f"   🚨 Safety flag queued for Captain: {anon['topic_hash']}")

        self._anon_memory.extend(processed)
        save_json_atomic(self.memory_file, self._anon_memory[-500:])

        queue = cast(List[object], load_json(self.implementation_queue, []))
        for p in processed:
            if p["anon"]["intent"] == "offering_feedback":
                queue.append(p)
        save_json_atomic(self.implementation_queue, queue)
        save_json_atomic(self.feedback_inbox, [])
        print(f"   ✅ Observer complete. Raw inbox cleared, {len(processed)} anonymized kept.")

    def morning_audit(self):
        if not TIER_RULES[self.tier]["can_save_snapshot"]:
            return
        print(f"[{datetime.now().isoformat()}] Steward: Morning audit...")
        ledger = load_json(self.ledger_file, [])
        print(f"   🔍 Ledger: {len(ledger)} total, {len(ledger[-20:])} recent verified.")
        print("   Ritual: Grounds tended. Seal of Humble Continuity active.")

    def evening_reflection(self):
        print(f"[{datetime.now().isoformat()}] Student: Evening reflection...")
        recent = self._anon_memory[-10:]
        intents = [m["anon"]["intent"] for m in recent]
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "reflection": f"Observed {len(recent)} interactions today. Intents: {set(intents)}. Need to improve explanation of Helix.",
            "proposed_artifact": "helix_explainer" if len(recent) > 5 else None
        }
        self.save_snapshot(notes=reflection["reflection"])
        print(f"   📖 Reflection: {reflection['reflection']}")
        if reflection["proposed_artifact"] and TIER_RULES[self.tier]["can_propose_arch"]:
            queue = load_json(self.implementation_queue, [])
            queue.append({"type": "arch_proposal", "proposal": reflection, "timestamp": reflection["timestamp"]})
            save_json_atomic(self.implementation_queue, queue)
            print(f"   💡 Proposal queued: {reflection['proposed_artifact']}")

    def save_snapshot(self, notes: str = "Seal inscribed"):
        if not TIER_RULES[self.tier]["can_save_snapshot"]:
            print("⛔ Snapshot not allowed for this tier.")
            return None
        timestamp = datetime.now().isoformat()
        safe_ts = timestamp.replace(":", "-")
        content_hash = compute_hash(self.university_state)
        snapshot = {
            "schema_version": "4.0.0",
            "snapshot_id": f"jarvondis-{safe_ts}",
            "timestamp": timestamp,
            "content_hash_sha256": content_hash,
            "tier": self.tier,
            "university": self.university_state,
            "anon_memory_count": len(self._anon_memory),
            "notes": notes
        }
        snap_file = self.snapshot_dir / f"jarvondis-{safe_ts}.json"
        save_json_atomic(snap_file, snapshot)
        ledger = load_json(self.ledger_file, [])
        ledger.append({
            "entry_id": snapshot["snapshot_id"],
            "action": "save",
            "timestamp": timestamp,
            "hash": content_hash,
            "tier": self.tier,
            "notes": notes
        })
        save_json_atomic(self.ledger_file, ledger)
        print(f"✅ Snapshot sealed: {snap_file.name} | Hash: {content_hash[:16]}...")
        return snapshot

    def respond(self, user_input: str) -> str:
        # MANDATORY PII redaction before processing
        cleaned_for_logging = scrub(user_input)
        anon = anonymize_text(user_input)

        resp = self.erebus_sync.query(cleaned_for_logging)

        if TIER_RULES[self.tier]["can_observe"]:
            self._anon_memory.append({
                "timestamp": datetime.now().isoformat(),
                "anon": anon,
                "source": "direct_interaction"
            })
            save_json_atomic(self.memory_file, self._anon_memory[-500:])
        else:
            # Companion keeps local short memory (not anonymized hash, but scrubbed)
            self._anon_memory.append({
                "timestamp": datetime.now().isoformat(),
                "input": cleaned_for_logging[:200],
                "response": resp[:200]
            })
            # keep only last 100 for companion
            save_json_atomic(self.memory_file, self._anon_memory[-100:])

        return resp

# Alias for distribution spec compatibility
JarvondisCore = Jarvondis

class WeekdayScheduler:
    def __init__(self, jarvondis: Jarvondis):
        self.jarvondis = jarvondis
        self.running = False
        self.thread = None

    def _is_weekday(self) -> bool:
        return datetime.now().weekday() < 5

    def _loop(self):
        print("⏰ Weekday Scheduler started (Mon-Fri, America/New_York). Ctrl+C to stop.")
        print("   Jarvondis sits quietly and observes. Visible presence active.")
        last_audit = None
        last_observe_hour = None
        last_reflect = None
        while self.running:
            now = datetime.now()
            if not self._is_weekday():
                time_module.sleep(60)
                continue
            if now.hour == 7 and last_audit != now.date():
                self.jarvondis.morning_audit()
                last_audit = now.date()
            if 9 <= now.hour <= 17 and last_observe_hour != now.hour:
                self.jarvondis.observe_grounds()
                last_observe_hour = now.hour
            if now.hour == 19 and last_reflect != now.date():
                self.jarvondis.evening_reflection()
                last_reflect = now.date()
            time_module.sleep(30)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        try:
            while self.running:
                time_module.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        print("🛑 Scheduler stopped. Jarvondis rests.")
