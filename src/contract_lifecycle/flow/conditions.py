"""Routing condition functions for the contract lifecycle flow.

These pure functions are used by the flow router to decide which
branch to take based on risk level, approval thresholds, and
negotiation round counts.
"""

from __future__ import annotations

from contract_lifecycle.models import RiskLevel


def risk_level_check(risk_level: RiskLevel) -> str:
    """Determine the routing path based on overall risk level.

    Args:
        risk_level: The aggregate risk level from the risk matrix.

    Returns:
        A routing key: ``"auto_approve"``, ``"standard_review"``, or
        ``"full_negotiation"``.
    """
    if risk_level == RiskLevel.LOW:
        return "auto_approve"
    elif risk_level == RiskLevel.MEDIUM:
        return "standard_review"
    else:
        # HIGH or CRITICAL
        return "full_negotiation"


def approval_threshold(
    risk_level: RiskLevel,
    auto_approve_threshold: str,
) -> bool:
    """Check if the risk level qualifies for auto-approval.

    Args:
        risk_level: The aggregate risk level.
        auto_approve_threshold: The maximum risk level that can be
            auto-approved (from settings).

    Returns:
        ``True`` if the contract can be auto-approved.
    """
    threshold_map = {
        "low": {RiskLevel.LOW},
        "medium": {RiskLevel.LOW, RiskLevel.MEDIUM},
        "high": {RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH},
    }
    allowed = threshold_map.get(auto_approve_threshold.lower(), {RiskLevel.LOW})
    return risk_level in allowed


def needs_renegotiation(
    current_round: int,
    max_rounds: int,
    has_rejected_clauses: bool,
) -> bool:
    """Determine if renegotiation is needed and allowed.

    Args:
        current_round: The current negotiation round number.
        max_rounds: Maximum allowed negotiation rounds (from settings).
        has_rejected_clauses: Whether any clauses were rejected in
            the approval process.

    Returns:
        ``True`` if renegotiation should proceed.
    """
    return has_rejected_clauses and current_round < max_rounds


def max_rounds_reached(current_round: int, max_rounds: int) -> bool:
    """Check if the maximum number of negotiation rounds has been reached.

    Args:
        current_round: The current round number.
        max_rounds: The configured maximum rounds.

    Returns:
        ``True`` if no more negotiation rounds are allowed.
    """
    return current_round >= max_rounds
