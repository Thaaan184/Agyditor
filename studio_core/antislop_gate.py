"""Programmatic Anti-Slop & Anti-Slop-Copywriting Delivery Gate scanner for HTML compositions and video copy."""

import re

BANNED_BUZZWORDS = [
    "revolutionary",
    "ai-powered",
    "ai powered",
    "seamless",
    "cutting-edge",
    "cutting edge",
    "next-level",
    "next level",
    "game-changer",
    "game changer",
    "unlock the power",
    "in today's fast-paced",
    "in an era of",
    "let's dive in",
]

FAKE_STAT_PATTERNS = [
    r"\b10[,\.]?000\+\s*users\b",
    r"\b99\.9%\s*uptime\b",
    r"\bsoc\s*2\s*compliant\b",
    r"\biso\s*27001\b",
]


def audit_antislop_deliverable(html_text: str, copy_strings: list[str]) -> dict:
    """Scans HTML composition and copy strings against core antislop and antislop-copywriting rules."""
    violations: list[str] = []
    combined_copy = "\n".join(copy_strings) + "\n" + html_text

    # R-02: Zero em dashes or en dashes
    if "\u2014" in combined_copy:
        violations.append("R-02 FAIL: Forbidden em dash (U+2014) detected in output.")
    if "\u2013" in combined_copy:
        violations.append("R-02 FAIL: Forbidden en dash (U+2013) detected in output.")

    # R-16: Banned AI marketing buzzwords
    lower_copy = combined_copy.lower()
    for buzz in BANNED_BUZZWORDS:
        if buzz in lower_copy:
            violations.append(f"R-16 FAIL: Forbidden AI marketing buzzword '{buzz}' detected.")

    # R-17 / R-36: Fake template statistics
    for pat in FAKE_STAT_PATTERNS:
        if re.search(pat, lower_copy):
            violations.append(f"R-17/R-36 FAIL: Unverified template statistic matching '{pat}' detected.")

    # R-01: Default blue-to-purple AI slop gradient check
    if "linear-gradient" in lower_copy and "#8b5cf6" in lower_copy and "#3b82f6" in lower_copy:
        violations.append("R-01 FAIL: Generic AI blue-to-purple default gradient detected.")

    return {
        "passed": len(violations) == 0,
        "violations": violations,
    }
