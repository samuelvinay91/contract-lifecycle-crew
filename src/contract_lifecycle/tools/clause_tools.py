"""Regex-based clause extraction and comparison utilities.

These tools operate purely on contract text without requiring any
external API calls, making them suitable for offline/demo use.
"""

from __future__ import annotations

import re
import uuid
from difflib import SequenceMatcher
from typing import Any

import structlog

from contract_lifecycle.models import Clause

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Clause section patterns (case-insensitive, multi-line)
# ---------------------------------------------------------------------------

_SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "TERM": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:TERM|RENEWAL|DURATION)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "PAYMENT": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:PAYMENT|COMPENSATION|FEES|PRICING)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "CONFIDENTIALITY": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:CONFIDENTIALITY|CONFIDENTIAL|NON-DISCLOSURE)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "INDEMNIFICATION": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:INDEMNIFICATION|INDEMNIFY)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "TERMINATION": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*TERMINATION[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "LIABILITY": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:LIMITATION OF LIABILITY|LIABILITY)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "IP": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:INTELLECTUAL PROPERTY|IP OWNERSHIP)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "WARRANTY": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:WARRANTY|WARRANTIES)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "GOVERNING_LAW": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:GOVERNING LAW|JURISDICTION|APPLICABLE LAW)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "FORCE_MAJEURE": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*FORCE MAJEURE[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "NON_COMPETE": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:NON-COMPETE|NON COMPETE|NONCOMPETE)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "NON_SOLICITATION": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:NON-SOLICITATION|NON SOLICITATION)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "SLA": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:SERVICE LEVEL|SLA|UPTIME)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "DATA_PROTECTION": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:DATA PROTECTION|DATA PRIVACY|GDPR)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "EQUITY": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:EQUITY|STOCK OPTION|SHARES)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "BENEFITS": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*BENEFITS[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "SCOPE": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:SCOPE OF SERVICES|SCOPE|DUTIES|POSITION)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "DEFINITION": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*(?:DEFINITION|DEFINITIONS)[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "OBLIGATIONS": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*OBLIGATIONS[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "REMEDIES": re.compile(
        r"(?:^|\n)\s*\d+\.?\s*REMEDIES[^\n]*\n(.*?)(?=\n\s*\d+\.\s+[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
}

# Risk flag patterns applied to extracted clause text
_RISK_FLAG_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("unlimited_liability", re.compile(r"unlimited|no limit|without limit", re.IGNORECASE)),
    ("auto_renewal", re.compile(r"automatically renew|auto[- ]?renew", re.IGNORECASE)),
    ("unilateral_termination", re.compile(
        r"(?:provider|vendor|company)\s+may\s+terminate.*?without\s+cause", re.IGNORECASE
    )),
    ("broad_non_compete", re.compile(r"(?:worldwide|global|any market)", re.IGNORECASE)),
    ("long_non_compete", re.compile(
        r"(?:thirty-six|36|twenty-four|24|48|forty-eight)\s*(?:\(\d+\))?\s*months?\s*(?:following|after)",
        re.IGNORECASE,
    )),
    ("one_sided_indemnification", re.compile(
        r"(?:customer|client|employee)\s+shall\s+indemnify(?!.*?(?:each party|mutual))",
        re.IGNORECASE,
    )),
    ("broad_confidentiality", re.compile(
        r"ALL\s+information\s+(?:disclosed\s+)?(?:by\s+either\s+party\s+)?in\s+ANY\s+form",
        re.IGNORECASE,
    )),
    ("ip_favors_provider", re.compile(
        r"(?:owned\s+exclusively\s+by\s+(?:provider|vendor|company))",
        re.IGNORECASE,
    )),
    ("high_interest_rate", re.compile(r"(?:1\.5%|2%|1\.75%)\s*per\s*month", re.IGNORECASE)),
    ("missing_data_protection", re.compile(r"GDPR|data\s+protection|CCPA", re.IGNORECASE)),
]


def extract_clauses(text: str) -> list[Clause]:
    """Extract structured clauses from raw contract text using regex.

    Scans the contract text for known section headings and extracts the
    body of each section. Applies risk-flag heuristics to each extracted
    clause.

    Args:
        text: The full contract text.

    Returns:
        A list of :class:`Clause` objects with populated risk flags.
    """
    clauses: list[Clause] = []
    seen_sections: set[str] = set()

    for section_name, pattern in _SECTION_PATTERNS.items():
        match = pattern.search(text)
        if match and section_name not in seen_sections:
            seen_sections.add(section_name)
            clause_text = match.group(1).strip()
            if not clause_text:
                continue

            # Detect risk flags
            risk_flags: list[str] = []
            for flag_name, flag_pattern in _RISK_FLAG_PATTERNS:
                if flag_pattern.search(clause_text):
                    risk_flags.append(flag_name)

            # Determine if clause is standard (no risk flags = standard)
            is_standard = len(risk_flags) == 0

            clause = Clause(
                id=str(uuid.uuid4())[:8],
                title=section_name.replace("_", " ").title(),
                text=clause_text,
                section=section_name,
                is_standard=is_standard,
                risk_flags=risk_flags,
            )
            clauses.append(clause)
            logger.debug(
                "clause_extracted",
                section=section_name,
                flags=risk_flags,
                length=len(clause_text),
            )

    logger.info("clauses_extracted", total=len(clauses))
    return clauses


def compare_versions(v1: str, v2: str) -> list[str]:
    """Compare two contract text versions and return a list of changes.

    Uses :class:`SequenceMatcher` to identify added, removed, and
    modified blocks.

    Args:
        v1: Original contract text.
        v2: Revised contract text.

    Returns:
        Human-readable list of change descriptions.
    """
    changes: list[str] = []
    lines_v1 = v1.splitlines()
    lines_v2 = v2.splitlines()

    matcher = SequenceMatcher(None, lines_v1, lines_v2)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        elif tag == "replace":
            for old_line in lines_v1[i1:i2]:
                changes.append(f"Removed: {old_line.strip()}")
            for new_line in lines_v2[j1:j2]:
                changes.append(f"Added: {new_line.strip()}")
        elif tag == "insert":
            for new_line in lines_v2[j1:j2]:
                changes.append(f"Added: {new_line.strip()}")
        elif tag == "delete":
            for old_line in lines_v1[i1:i2]:
                changes.append(f"Removed: {old_line.strip()}")

    return changes


def check_standard_terms(clause: Clause) -> bool:
    """Check whether a clause uses standard/safe terms.

    A clause is considered standard if it has no risk flags and its text
    does not match known risky patterns.

    Args:
        clause: The clause to check.

    Returns:
        ``True`` if the clause appears to use standard terms.
    """
    if clause.risk_flags:
        return False

    # Additional heuristic checks
    risky_phrases = [
        "unlimited",
        "without limitation",
        "sole discretion",
        "irrevocable",
        "perpetual license",
        "worldwide",
        "any and all claims",
    ]
    text_lower = clause.text.lower()
    for phrase in risky_phrases:
        if phrase in text_lower:
            return False

    return True
