"""Approval Crew - sequential crew for approval routing and validation.

Combines the Approval Router and Compliance Officer agents in a
sequential process: the router determines the approval chain, then
the Compliance Officer validates it meets regulatory requirements.
"""

from __future__ import annotations

from typing import Any

import structlog

from contract_lifecycle.agents.approval_router import ApprovalRouterAgent
from contract_lifecycle.agents.compliance_officer import ComplianceOfficerAgent
from contract_lifecycle.models import (
    ApprovalDecision,
    ApprovalLevel,
    ContractType,
    RiskLevel,
)

logger = structlog.get_logger(__name__)


class ApprovalCrew:
    """Sequential crew for approval chain determination.

    Agents:
        - Approval Router: determines the approval chain
        - Compliance Officer: validates the chain meets requirements

    Process: ``"sequential"`` -- router proposes chain, then compliance
    officer validates it.

    Task sequence:
        1. Determine approval chain -> based on risk, value, type
        2. Validate chain -> ensure regulatory requirements are met
    """

    def __init__(self) -> None:
        self.approval_router = ApprovalRouterAgent()
        self.compliance_officer = ComplianceOfficerAgent()
        self.process = "sequential"
        self.verbose = True

    async def kickoff(
        self,
        risk_level: RiskLevel,
        contract_value: float,
        contract_type: ContractType,
    ) -> dict[str, Any]:
        """Execute the approval crew workflow.

        Step 1: The Approval Router determines the required approval
        chain based on risk, value, and contract type.

        Step 2: The Compliance Officer validates that the chain meets
        minimum regulatory requirements for the contract type.

        Args:
            risk_level: The overall risk level of the contract.
            contract_value: The total monetary value of the contract.
            contract_type: The type of contract.

        Returns:
            A dictionary containing:
            - ``approval_chain``: Ordered list of :class:`ApprovalLevel`.
            - ``approval_decisions``: List of pending
              :class:`ApprovalDecision` objects.
            - ``validation_notes``: Notes from compliance validation.
        """
        logger.info(
            "approval_crew_kickoff",
            risk_level=risk_level.value,
            contract_value=contract_value,
            contract_type=contract_type.value,
        )

        # Step 1: Determine approval chain
        logger.info("approval_crew_step", step=1, agent="Approval Router")
        chain = await self.approval_router.determine_approval_chain(
            risk_level, contract_value, contract_type
        )

        # Step 2: Validate chain meets compliance requirements
        logger.info("approval_crew_step", step=2, agent="Compliance Officer (Validation)")
        validated_chain, notes = self._validate_chain(
            chain, risk_level, contract_value, contract_type
        )

        # Create approval decision objects
        decisions = self.approval_router.create_approval_decisions(validated_chain)

        result = {
            "approval_chain": validated_chain,
            "approval_decisions": decisions,
            "validation_notes": notes,
        }

        logger.info(
            "approval_crew_complete",
            chain_length=len(validated_chain),
            chain=[level.value for level in validated_chain],
        )
        return result

    def _validate_chain(
        self,
        chain: list[ApprovalLevel],
        risk_level: RiskLevel,
        contract_value: float,
        contract_type: ContractType,
    ) -> tuple[list[ApprovalLevel], list[str]]:
        """Validate the approval chain meets compliance requirements.

        The Compliance Officer applies additional rules to ensure the
        chain is sufficient for regulatory purposes.

        Args:
            chain: The proposed approval chain.
            risk_level: The overall risk level.
            contract_value: The contract monetary value.
            contract_type: The contract type.

        Returns:
            A tuple of (validated_chain, validation_notes).
        """
        notes: list[str] = []
        validated = list(chain)

        # Rule: Employment contracts always need legal review
        if contract_type == ContractType.EMPLOYMENT:
            if ApprovalLevel.LEGAL not in validated:
                validated.append(ApprovalLevel.LEGAL)
                notes.append(
                    "Added LEGAL approval: employment contracts require "
                    "legal review per company policy."
                )

        # Rule: High-value contracts need VP approval
        if contract_value >= 250_000:
            if ApprovalLevel.VP not in validated:
                validated.append(ApprovalLevel.VP)
                notes.append(
                    f"Added VP approval: contract value (${contract_value:,.2f}) "
                    f"exceeds $250K threshold."
                )

        # Rule: CRITICAL risk always needs CFO
        if risk_level == RiskLevel.CRITICAL:
            if ApprovalLevel.CFO not in validated:
                validated.append(ApprovalLevel.CFO)
                notes.append(
                    "Added CFO approval: CRITICAL risk level requires "
                    "executive-level authorization."
                )

        # Rule: Cannot auto-approve if compliance issues exist
        if risk_level != RiskLevel.LOW and ApprovalLevel.AUTO in validated:
            validated.remove(ApprovalLevel.AUTO)
            if ApprovalLevel.MANAGER not in validated:
                validated.append(ApprovalLevel.MANAGER)
            notes.append(
                "Replaced AUTO approval with MANAGER: non-LOW risk "
                "contracts cannot be auto-approved per compliance policy."
            )

        if not notes:
            notes.append("Approval chain validated. No modifications required.")

        # Sort by seniority
        seniority_order = [
            ApprovalLevel.AUTO,
            ApprovalLevel.MANAGER,
            ApprovalLevel.VP,
            ApprovalLevel.LEGAL,
            ApprovalLevel.CFO,
        ]
        validated.sort(key=lambda level: seniority_order.index(level))

        return validated, notes
