"""CrewAI-style Task definitions for contract lifecycle workflows.

Each task mirrors CrewAI's ``Task`` API with a description, expected
output, and an assigned agent. Tasks are used by Crews to orchestrate
the multi-agent workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """A unit of work assigned to an agent within a Crew.

    Mirrors the ``crewai.Task`` interface for API compatibility.
    """

    description: str
    expected_output: str
    agent_role: str
    context: list[str] = field(default_factory=list)
    result: Any = None


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------


def analyze_contract_task() -> Task:
    """Create the contract analysis task for the Legal Analyst."""
    return Task(
        description=(
            "Analyze the submitted contract text thoroughly. Extract all "
            "clauses, identify the contract type, parties involved, key "
            "dates, total value, and generate a comprehensive summary of "
            "obligations and rights for each party."
        ),
        expected_output=(
            "A ContractAnalysis object containing: contract_type, parties, "
            "effective_date, expiration_date, total_value, list of Clause "
            "objects with risk flags, and a narrative summary."
        ),
        agent_role="Senior Legal Analyst",
    )


def assess_risk_task() -> Task:
    """Create the risk assessment task for the Risk Assessor."""
    return Task(
        description=(
            "Evaluate each extracted clause for legal, financial, and "
            "operational risk. Flag unlimited liability, auto-renewal traps, "
            "excessive non-competes, unilateral termination rights, unclear "
            "IP ownership, and missing SLA penalties. Quantify exposure "
            "where possible."
        ),
        expected_output=(
            "A list of RiskAssessment objects, one per clause, each with "
            "risk_level, description, recommendation, and precedent "
            "references where applicable."
        ),
        agent_role="Risk Assessment Specialist",
        context=["analyze_contract"],
    )


def check_compliance_task() -> Task:
    """Create the compliance check task for the Compliance Officer."""
    return Task(
        description=(
            "Review the contract analysis and extracted clauses against "
            "regulatory requirements including GDPR data processing "
            "obligations, SOX financial controls, and industry-specific "
            "regulations. Identify all compliance gaps."
        ),
        expected_output=(
            "A list of RiskAssessment objects representing compliance gaps, "
            "each with risk_level, description of the regulatory requirement, "
            "and specific recommendations for remediation."
        ),
        agent_role="Compliance Officer",
        context=["analyze_contract"],
    )


def develop_negotiation_task() -> Task:
    """Create the negotiation strategy task for the Negotiation Strategist."""
    return Task(
        description=(
            "Develop optimal negotiation positions for all HIGH and CRITICAL "
            "risk clauses. For each position, provide the current problematic "
            "terms, proposed replacement language from standard enterprise "
            "templates, a rationale for the change, and leverage points to "
            "support the negotiation."
        ),
        expected_output=(
            "A list of NegotiationPosition objects, each containing "
            "clause_id, current_terms, proposed_terms, rationale, and "
            "leverage_points."
        ),
        agent_role="Negotiation Strategist",
        context=["assess_risk", "check_compliance"],
    )


def route_approval_task() -> Task:
    """Create the approval routing task for the Approval Router."""
    return Task(
        description=(
            "Determine the appropriate approval chain for the contract "
            "based on the overall risk level, total contract value, and "
            "contract type. Apply escalation rules and create pending "
            "approval decisions for each required level."
        ),
        expected_output=(
            "An ordered list of ApprovalLevel values representing the "
            "required approval chain, plus corresponding ApprovalDecision "
            "objects in pending status."
        ),
        agent_role="Approval Workflow Manager",
        context=["assess_risk"],
    )
