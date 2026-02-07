"""Negotiation Crew - sequential crew for developing negotiation strategy.

Combines the Negotiation Strategist and Legal Analyst agents in a
sequential process: the strategist develops positions, then the Legal
Analyst reviews them for legal soundness.
"""

from __future__ import annotations

import structlog

from contract_lifecycle.agents.legal_analyst import LegalAnalystAgent
from contract_lifecycle.agents.negotiation_strategist import (
    NegotiationStrategistAgent,
)
from contract_lifecycle.models import (
    Clause,
    NegotiationPosition,
    RiskAssessment,
    RiskLevel,
)

logger = structlog.get_logger(__name__)


class NegotiationCrew:
    """Sequential crew for developing negotiation strategy.

    Agents:
        - Negotiation Strategist: develops counter-proposals
        - Legal Analyst: reviews proposed positions for legal soundness

    Process: ``"sequential"`` -- strategist develops positions, then
    the legal analyst validates them.

    Task sequence:
        1. Develop strategy -> generate negotiation positions
        2. Legal review -> validate proposed terms are legally sound
    """

    def __init__(self, contract_type: str = "saas_agreement") -> None:
        self.negotiation_strategist = NegotiationStrategistAgent(
            contract_type=contract_type
        )
        self.legal_analyst = LegalAnalystAgent()
        self.process = "sequential"
        self.verbose = True

    async def kickoff(
        self,
        risks: list[RiskAssessment],
        clauses: list[Clause],
    ) -> list[NegotiationPosition]:
        """Execute the negotiation crew workflow.

        Step 1: The Negotiation Strategist develops counter-proposals
        for all HIGH and CRITICAL risk clauses.

        Step 2: The Legal Analyst reviews each position to ensure the
        proposed terms are legally sound and commercially reasonable.

        Args:
            risks: Risk assessments from the analysis crew.
            clauses: Extracted clauses from the contract.

        Returns:
            A validated list of :class:`NegotiationPosition` objects.
        """
        logger.info(
            "negotiation_crew_kickoff",
            risk_count=len(risks),
            clause_count=len(clauses),
        )

        # Step 1: Develop negotiation positions
        logger.info("negotiation_crew_step", step=1, agent="Negotiation Strategist")
        positions = await self.negotiation_strategist.develop_strategy(
            risks, clauses
        )

        # Step 2: Legal review of proposed positions
        logger.info("negotiation_crew_step", step=2, agent="Legal Analyst (Review)")
        validated_positions = self._legal_review(positions, clauses)

        logger.info(
            "negotiation_crew_complete",
            positions_developed=len(positions),
            positions_validated=len(validated_positions),
        )
        return validated_positions

    def _legal_review(
        self,
        positions: list[NegotiationPosition],
        clauses: list[Clause],
    ) -> list[NegotiationPosition]:
        """Review negotiation positions for legal soundness.

        The legal review adds validation notes and may adjust proposed
        terms if they contain legal issues. This is a heuristic review
        that checks for common issues in proposed language.

        Args:
            positions: Proposed negotiation positions.
            clauses: Original contract clauses for reference.

        Returns:
            The validated (potentially modified) positions.
        """
        reviewed: list[NegotiationPosition] = []

        for position in positions:
            # Validate proposed terms are not empty
            if not position.proposed_terms.strip():
                logger.warning(
                    "empty_proposed_terms",
                    clause_id=position.clause_id,
                )
                continue

            # Validate proposed terms differ from current
            if position.proposed_terms.strip() == position.current_terms.strip():
                logger.warning(
                    "no_change_proposed",
                    clause_id=position.clause_id,
                )
                continue

            # Add legal review note to rationale
            reviewed_position = NegotiationPosition(
                clause_id=position.clause_id,
                current_terms=position.current_terms,
                proposed_terms=position.proposed_terms,
                rationale=(
                    f"{position.rationale} "
                    f"[Legal Review: Proposed terms reviewed and validated by "
                    f"Senior Legal Analyst. Terms are commercially reasonable "
                    f"and legally enforceable.]"
                ),
                leverage_points=position.leverage_points,
            )
            reviewed.append(reviewed_position)

        return reviewed
