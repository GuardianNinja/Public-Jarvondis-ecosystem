"""
jarvondis_core/safety.py
Safety Envelope & Anonymizer — MANDATORY, cannot be disabled by user_space.

This is the immutable privacy guardrail. All user input must pass through
anonymize_text() before any processing or logging.
"""
from __future__ import annotations
import re
import hashlib
from typing import Dict, Any

PII_PATTERNS = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # email
    r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # phone US
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # ip
    r"\b(?:\d[ -]*?){13,16}\b",  # crude credit card-ish
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
]

def anonymize_text(text: str) -> Dict[str, Any]:
    """
    Observer ethic: strip PII, hash content, keep only intent & topic.
    Returns anonymized dict — never raw PII.
    """
    cleaned = text
    for pat in PII_PATTERNS:
        cleaned = re.sub(pat, "[REDACTED]", cleaned)

    lower = cleaned.lower()
    if any(w in lower for w in ["unsafe", "abuse", "harm", "hurt myself", "suicide", "kill"]):
        intent = "safety_flag"
    elif any(w in lower for w in ["help", "how do i", "can you", "what is", "explain"]):
        intent = "seeking_help"
    elif any(w in lower for w in ["idea", "suggest", "should", "could you add", "feature", "cool if", "wish"]):
        intent = "offering_feedback"
    else:
        intent = "casual"

    topic_hash = hashlib.sha256(cleaned.encode()).hexdigest()[:16]

    # Length bucketing to avoid fingerprinting
    length_bucket = f"{len(cleaned)//20*20}-{(len(cleaned)//20+1)*20} chars"

    if intent == "safety_flag":
        preview = "[SAFETY CONTENT REDACTED FOR CAPTAIN REVIEW]"
    else:
        preview = cleaned[:80] + "..." if len(cleaned) > 80 else cleaned

    return {
        "topic_hash": topic_hash,
        "intent": intent,
        "length_bucket": length_bucket,
        "cleaned_preview": preview,
        "was_flagged": intent == "safety_flag",
    }

def scrub(text: str) -> str:
    """Simple string-only scrub for respond() path."""
    cleaned = text
    for pat in PII_PATTERNS:
        cleaned = re.sub(pat, "[REDACTED]", cleaned)
    return cleaned
