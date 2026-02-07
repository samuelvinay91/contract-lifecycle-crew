"""Approval Workflow Manager agent.

Routes contracts through the appropriate approval chain based on risk
level, contract value, and contract type. Implements escalation logic
from auto-approval through CFO-level review.
"""

from __future__ import annotations

import structlog

from contract_lifecycle.models import (
    ApprovalDecision,
    ApprovalLevel,
    ContractType,
    RiskLevel,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# CrewAI-style agent metadata
# ---------------------------------------------------------------------------

ROLE = "Approval Workflow Manager"
GOAL = (
    "Route contracts through the appropriate approval chain based on risk "
    "level, contract value, and contract type. Ensure proper authorization "
    "at each level before execution."
)
BACKSTORY = (
    "You are the VP of Procurement Operations with 15 years of experience "
    "designing and managing approval workflows for Fortune 500 companies. "
    "You have implemented approval systems that process over 10,000 contracts "
    "per year while maintaining 100% audit compliance. You are known for "
    "balancing speed of execution with appropriate risk controls."
)

# ---------------------------------------------------------------------------
# Approval chain rules
# ---------------------------------------------------------------------------

# Value thresholds (in USD)
_VALUE_THRESHOLDS = {
    "manager": 50_000,
    "vp": 250_000,
    "legal": 500_000,
    "cfo": 1_000_000,
}

# Default approver names by level
_DEFAULT_APPROVERS: dict[ApprovalLevel, str] = {
    ApprovalLevel.AUTO: "System (Auto-Approval)",
    ApprovalLevel.MANAGER: "Department Manager",
    ApprovalLevel.VP: "VP of Operations",
    ApprovalLevel.LEGAL: "General Counsel",
    ApprovalLevel.CFO: "Chief Financial Officer",
}


class ApprovalRouterAgent:
    """Approval Workflow Manager agent.

    Determines the required approval chain based on overall risk level,
    contract monetary value, and contract type.
    """

    def __init__(self) -> None:
        self.role = ROLE
        self.goal = GOAL
        self.backstory = BACKSTORY
        self.tools: list[str] = []
        self.verbose = True

    async def determine_approval_chain(
        self,
        overall_risk: RiskLevel,
        contract_value: float,
        contract_type: ContractType,
    ) -> list[ApprovalLevel]:
        """Determine the required approval chain for a contract.

        The approval chain is built based on three factors:
        1. **Risk level**: Higher risk requires more senior approvals.
        2. **Contract value**: Higher value requires additional oversight.
        3. **Contract type**: Certain types (e.g., employment) always
           require legal review.

        Routing logic:
        - LOW risk + value < $50K -> AUTO
        - MEDIUM risk or value $50K-$250K -> MANAGER
        - HIGH risk or value $250K-$1M -> MANAGER + VP + LEGAL
        - CRITICAL risk or value > $1M -> MANAGER + VP + LEGAL + CFO

        Args:
            overall_risk: The aggregate risk level from risk assessment.
            contract_value: The total monetary value of the contract.
            contract_type: The type of contract.

        Returns:
            An ordered list of :class:`ApprovalLevel` values representing
            the required approval chain.
        """
        logger.info(
            "approval_routing_starting",
            risk=overall_risk.value,
            value=contract_value,
            contract_type=contract_type.value,
        )

        chain: list[ApprovalLevel] = []

        # Risk-based routing
        if overall_risk == RiskLevel.LOW:
            chain = [ApprovalLevel.AUTO]
        elif overall_risk == RiskLevel.MEDIUM:
            chain = [ApprovalLevel.MANAGER]
        elif overall_risk == RiskLevel.HIGH:
            chain = [ApprovalLevel.MANAGER, ApprovalLevel.VP, ApprovalLevel.LEGAL]
        elif overall_risk == RiskLevel.CRITICAL:
            chain = [
                ApprovalLevel.MANAGER,
                ApprovalLevel.VP,
                ApprovalLevel.LEGAL,
                ApprovalLevel.CFO,
            ]

        # Value-based escalation (add levels not already in chain)
        if contract_value >= _VALUE_THRESHOLDS["cfo"]:
            for level in [ApprovalLevel.MANAGER, ApprovalLevel.VP,
                          ApprovalLevel.LEGAL, ApprovalLevel.CFO]:
                if level not in chain:
                    chain.append(level)
        elif contract_value >= _VALUE_THRESHOLDS["legal"]:
            for level in [ApprovalLevel.MANAGER, ApprovalLevel.VP, ApprovalLevel.LEGAL]:
                if level not in chain:
                    chain.append(level)
        elif contract_value >= _VALUE_THRESHOLDS["vp"]:
            for level in [ApprovalLevel.MANAGER, ApprovalLevel.VP]:
                if level not in chain:
                    chain.append(level)
        elif contract_value >= _VALUE_THRESHOLDS["manager"]:
            if ApprovalLevel.MANAGER not in chain:
                chain.append(ApprovalLevel.MANAGER)

        # Contract type overrides
        if contract_type == ContractType.EMPLOYMENT:
            if ApprovalLevel.LEGAL not in chain:
                chain.append(ApprovalLevel.LEGAL)
        elif contract_type == ContractType.LICENSING:
            if ApprovalLevel.LEGAL not in chain:
                chain.append(ApprovalLevel.LEGAL)

        # Remove AUTO if any human approval is needed
        if len(chain) > 1 and ApprovalLevel.AUTO in chain:
            chain.remove(ApprovalLevel.AUTO)

        # Sort by seniority
        seniority_order = [
            ApprovalLevel.AUTO,
            ApprovalLevel.MANAGER,
            ApprovalLevel.VP,
            ApprovalLevel.LEGAL,
            ApprovalLevel.CFO,
        ]
        chain.sort(key=lambda level: seniority_order.index(level))

        logger.info(
            "approval_chain_determined",
            chain=[level.value for level in chain],
            chain_length=len(chain),
        )
        return chain

    def create_approval_decisions(
        self, chain: list[ApprovalLevel]
    ) -> list[ApprovalDecision]:
        """Create initial (pending) approval decision objects for the chain.

        Args:
            chain: The ordered list of required approval levels.

        Returns:
            A list of :class:`ApprovalDecision` objects with ``pending`` status.
        """
        decisions: list[ApprovalDecision] = []
        for level in chain:
            decisions.append(
                ApprovalDecision(
                    level=level,
                    approver=_DEFAULT_APPROVERS.get(level, "Unknown"),
                    decision="pending",
                    comments="",
                )
            )
        return decisions
