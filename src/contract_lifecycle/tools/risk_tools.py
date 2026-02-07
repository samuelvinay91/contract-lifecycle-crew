"""Risk calculation and precedent lookup utilities.

Provides functions for computing aggregate risk scores, looking up
legal precedents, and estimating liability exposure from clause text.
"""

from __future__ import annotations

import re

import structlog

from contract_lifecycle.mock_data.precedents import (
    PRECEDENT_DATABASE,
    Precedent,
)
from contract_lifecycle.models import RiskAssessment, RiskLevel

logger = structlog.get_logger(__name__)

# Numeric weights for risk levels (used in matrix calculation)
_RISK_WEIGHTS: dict[RiskLevel, int] = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


def calculate_risk_matrix(assessments: list[RiskAssessment]) -> RiskLevel:
    """Calculate the overall risk level from a list of clause assessments.

    Uses a weighted scoring model:
    - Average score <= 1.5 -> LOW
    - Average score <= 2.2 -> MEDIUM
    - Average score <= 3.0 -> HIGH
    - Average score >  3.0 -> CRITICAL

    If any single clause is CRITICAL, the overall risk is at least HIGH.

    Args:
        assessments: Individual clause-level risk assessments.

    Returns:
        The aggregate :class:`RiskLevel`.
    """
    if not assessments:
        return RiskLevel.LOW

    total_weight = sum(_RISK_WEIGHTS[a.risk_level] for a in assessments)
    avg_score = total_weight / len(assessments)

    # Single-clause escalation rule
    has_critical = any(a.risk_level == RiskLevel.CRITICAL for a in assessments)
    has_high = any(a.risk_level == RiskLevel.HIGH for a in assessments)

    if has_critical:
        overall = max(RiskLevel.HIGH, _score_to_level(avg_score))
    elif has_high and avg_score > 2.0:
        overall = RiskLevel.HIGH
    else:
        overall = _score_to_level(avg_score)

    logger.info(
        "risk_matrix_calculated",
        assessment_count=len(assessments),
        avg_score=round(avg_score, 2),
        overall_risk=overall.value,
    )
    return overall


def _score_to_level(score: float) -> RiskLevel:
    """Map a numeric average score to a risk level."""
    if score <= 1.5:
        return RiskLevel.LOW
    elif score <= 2.2:
        return RiskLevel.MEDIUM
    elif score <= 3.0:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def lookup_precedent(clause_type: str) -> str | None:
    """Find the most relevant legal precedent for a clause type.

    Searches the mock precedent database for entries whose clause_type
    matches (substring) the provided type.

    Args:
        clause_type: The type of clause (e.g. ``"unlimited_liability"``).

    Returns:
        A formatted precedent string, or ``None`` if no match is found.
    """
    normalized = clause_type.lower().replace(" ", "_").replace("-", "_")

    best_match: Precedent | None = None
    for precedent in PRECEDENT_DATABASE:
        if normalized in precedent.clause_type or precedent.clause_type in normalized:
            best_match = precedent
            break

    if best_match is None:
        return None

    return (
        f"[{best_match.id}] {best_match.case_name} - "
        f"{best_match.outcome} "
        f"Recommendation: {best_match.recommendation}"
    )


def estimate_liability(clause_text: str) -> float:
    """Estimate the potential liability exposure from a clause.

    Uses simple heuristics to extract dollar amounts and multipliers
    from the clause text.

    Args:
        clause_text: The raw text of the clause.

    Returns:
        Estimated liability in USD. Returns 0.0 if no amounts are found.
    """
    # Look for explicit dollar amounts
    dollar_pattern = re.compile(r"\$[\d,]+(?:\.\d{2})?")
    amounts = dollar_pattern.findall(clause_text)

    total = 0.0
    for amount_str in amounts:
        cleaned = amount_str.replace("$", "").replace(",", "")
        try:
            total += float(cleaned)
        except ValueError:
            continue

    # Check for "unlimited" liability
    if re.search(r"unlimited|no limit|without limit", clause_text, re.IGNORECASE):
        # Flag as extremely high exposure
        total = max(total, 10_000_000.0)
        logger.warning("unlimited_liability_detected", estimated=total)

    # Check for multiplier language
    multiplier_match = re.search(r"(\d+)\s*(?:times|x)\s*(?:the|total|annual)", clause_text, re.IGNORECASE)
    if multiplier_match:
        multiplier = int(multiplier_match.group(1))
        if total > 0:
            total *= multiplier

    return total
