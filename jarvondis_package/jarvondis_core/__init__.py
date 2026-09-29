"""
Jarvondis Core Package
Seal of Humble Continuity | v4.0.0
Author: Leif William Sogge / Captain
"""
from .engine import Jarvondis, JarvondisCore, Personality, WeekdayScheduler, ErebusSync
from .safety import anonymize_text, PII_PATTERNS
from .governance import (
    TIER_RULES,
    DEFAULT_UNIVERSITY_STATE,
    verify_tier,
    get_captain_seal,
    create_captain_seal,
    compute_hash,
)

__version__ = "4.0.0"
__all__ = [
    "Jarvondis",
    "JarvondisCore",
    "Personality",
    "WeekdayScheduler",
    "ErebusSync",
    "anonymize_text",
    "TIER_RULES",
    "verify_tier",
]
