"""Negotiation Strategist agent.

Develops optimal negotiation positions for high-risk clauses using
game theory principles and standard enterprise contract templates.
"""

from __future__ import annotations

import structlog

from contract_lifecycle.models import (
    Clause,
    NegotiationPosition,
    RiskAssessment,
    RiskLevel,
)
from contract_lifecycle.tools.template_tools import get_safe_clause_text

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# CrewAI-style agent metadata
# ---------------------------------------------------------------------------

ROLE = "Negotiation Strategist"
GOAL = (
    "Develop optimal negotiation positions for high-risk clauses. "
    "Maximize favorable terms while maintaining deal viability."
)
BACKSTORY = (
    "You are an expert negotiator with a background in game theory and "
    "contract optimization. With 12 years of experience negotiating "
    "enterprise technology agreements worth over $2B in total contract "
    "value, you have developed strategies that consistently achieve "
    "30-40% improvement in contract terms. You hold a Ph.D. in Decision "
    "Sciences from Stanford and have published research on optimal "
    "negotiation strategies in multi-party agreements."
)

# ---------------------------------------------------------------------------
# Leverage point templates by risk flag
# ---------------------------------------------------------------------------

_LEVERAGE_POINTS: dict[str, list[str]] = {
    "unlimited_liability": [
        "Industry standard is capped liability at 12 months of fees",
        "Unlimited liability creates uninsurable risk and may require board approval",
        "Competing vendors offer capped liability as standard terms",
        "Reference PREC-001: TechCorp v. CloudServices showing enforcement risk",
    ],
    "auto_renewal": [
        "30-day notice is insufficient for budget planning cycles",
        "Auto-renewal without price caps creates uncontrolled cost exposure",
        "Customer should have adequate time to evaluate alternatives",
        "Market rates may decrease, customer should not be locked into stale pricing",
    ],
    "unilateral_termination": [
        "Unilateral termination creates unacceptable business continuity risk",
        "Migration costs can exceed the contract value itself",
        "Mutual termination rights are industry standard",
        "Reference PREC-005: VendorFirst case showing $1.5M transition costs",
    ],
    "broad_non_compete": [
        "Worldwide non-compete is likely unenforceable in multiple jurisdictions",
        "Courts regularly strike down overly broad non-competes entirely",
        "Narrow scope protects legitimate interests while being enforceable",
        "Reference PREC-003: InnovateTech case limiting scope to specific segments",
    ],
    "long_non_compete": [
        "Non-compete exceeding 12 months is considered unreasonable by most courts",
        "California does not enforce non-competes at all",
        "FTC has proposed rules limiting non-compete enforceability",
        "12-month maximum is the widely accepted commercial standard",
    ],
    "one_sided_indemnification": [
        "Mutual indemnification is the commercial standard",
        "One-sided indemnification shifts all risk to one party unfairly",
        "Each party should be responsible for claims arising from its own conduct",
        "Reference PREC-008: ServiceCo case showing enforcement of one-sided terms",
    ],
    "broad_confidentiality": [
        "Overly broad definitions have been held unenforceable",
        "Standard exclusions protect both parties from unreasonable obligations",
        "Reference PREC-009: DataLeaks case where broad definition failed",
        "Clear definitions reduce compliance burden for both parties",
    ],
    "ip_favors_provider": [
        "Customer-funded customizations should be customer-owned work product",
        "Pre-existing IP vs. new work product distinction is industry standard",
        "Reference PREC-004: DevStudio case showing cost of ambiguous IP terms",
        "Clear IP ownership reduces future disputes and litigation risk",
    ],
    "high_interest_rate": [
        "1.5% monthly (18% annual) may exceed usury limits in some states",
        "Prime rate + 2% is the typical commercial standard",
        "High interest rates create adversarial payment dynamics",
        "Market-rate interest is sufficient to incentivize timely payment",
    ],
}


class NegotiationStrategistAgent:
    """Negotiation Strategist agent for developing counter-proposals.

    Generates optimal negotiation positions for high-risk and
    critical-risk clauses using standard enterprise templates and
    leverage point analysis.
    """

    def __init__(self, contract_type: str = "saas_agreement") -> None:
        self.role = ROLE
        self.goal = GOAL
        self.backstory = BACKSTORY
        self.tools = ["get_contract_template", "get_safe_clause_text"]
        self.verbose = True
        self._contract_type = contract_type

    async def develop_strategy(
        self,
        risks: list[RiskAssessment],
        clauses: list[Clause],
    ) -> list[NegotiationPosition]:
        """Develop negotiation positions for high-risk clauses.

        Only generates positions for clauses rated HIGH or CRITICAL.
        Uses safe clause templates as proposed alternative language.

        Args:
            risks: Risk assessments for all clauses.
            clauses: All extracted clauses (for looking up current text).

        Returns:
            A list of :class:`NegotiationPosition` objects.
        """
        logger.info(
            "negotiation_strategy_starting",
            total_risks=len(risks),
            high_critical=sum(
                1 for r in risks
                if r.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            ),
        )

        # Build a clause lookup by ID
        clause_map: dict[str, Clause] = {c.id: c for c in clauses}
        positions: list[NegotiationPosition] = []

        for risk in risks:
            if risk.risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                continue

            clause = clause_map.get(risk.clause_id)
            if clause is None:
                continue

            position = self._build_position(clause, risk)
            if position:
                positions.append(position)

        logger.info(
            "negotiation_strategy_complete",
            positions_developed=len(positions),
        )
        return positions

    def _build_position(
        self,
        clause: Clause,
        risk: RiskAssessment,
    ) -> NegotiationPosition | None:
        """Build a single negotiation position for a risky clause."""
        # Try to find safe replacement text from templates
        section_key = clause.section.lower().replace(" ", "_")
        proposed_terms = get_safe_clause_text(self._contract_type, section_key)

        if proposed_terms is None:
            # Try mapping common section names to template keys
            section_mappings: dict[str, str] = {
                "liability": "limitation_of_liability",
                "term": "auto_renewal",
                "termination": "termination",
                "ip": "ip_ownership",
                "confidentiality": "confidentiality",
                "indemnification": "indemnification",
                "sla": "sla",
                "non_compete": "non_compete",
                "data_protection": "data_protection",
            }
            mapped_key = section_mappings.get(section_key, "")
            if mapped_key:
                proposed_terms = get_safe_clause_text(self._contract_type, mapped_key)

        if proposed_terms is None:
            proposed_terms = risk.recommendation

        # Gather leverage points from all matching flags
        leverage: list[str] = []
        for flag in clause.risk_flags:
            flag_leverage = _LEVERAGE_POINTS.get(flag, [])
            leverage.extend(flag_leverage)

        if not leverage:
            leverage = [
                "Current terms deviate from industry standard",
                "Proposed alternative reduces risk for both parties",
                risk.recommendation,
            ]

        return NegotiationPosition(
            clause_id=clause.id,
            current_terms=clause.text[:500],  # Truncate for readability
            proposed_terms=proposed_terms,
            rationale=(
                f"Risk Level: {risk.risk_level.value.upper()}. "
                f"{risk.description[:300]}"
            ),
            leverage_points=leverage[:5],  # Cap at 5 points
        )
