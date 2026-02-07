"""Crew and agent tests for Contract Lifecycle Crew."""

from __future__ import annotations

import pytest

SAMPLE_CONTRACT = """
NON-DISCLOSURE AGREEMENT

This NDA is entered into between AlphaCorp ("Discloser") and BetaInc ("Recipient").

1. CONFIDENTIAL INFORMATION
"Confidential Information" includes all information, whether written or oral,
disclosed by Discloser, including trade secrets, business plans, customer lists,
financial data, technical specifications, and any information marked confidential.

2. NON-DISCLOSURE OBLIGATIONS
Recipient shall not disclose any Confidential Information to third parties.
Recipient shall use Confidential Information solely for the Purpose.

3. TERM
This Agreement shall remain in effect for 3 years from the Effective Date.
Confidentiality obligations survive for 10 years after termination.

4. NON-COMPETE
Recipient agrees not to compete with Discloser in any market where Discloser
operates for a period of 5 years following termination of this Agreement.

5. REMEDIES
Discloser shall be entitled to injunctive relief and unlimited damages
for any breach of this Agreement.

6. GOVERNING LAW
This Agreement is governed by the laws of New York.
"""


@pytest.mark.asyncio
async def test_legal_analyst():
    """LegalAnalystAgent extracts clauses from contract text."""
    from contract_lifecycle.agents.legal_analyst import LegalAnalystAgent

    agent = LegalAnalystAgent()
    analysis = await agent.analyze_contract(SAMPLE_CONTRACT)

    assert analysis is not None
    assert len(analysis.clauses) > 0
    assert len(analysis.parties) >= 2
    assert analysis.summary


@pytest.mark.asyncio
async def test_risk_assessor():
    """RiskAssessorAgent identifies risks in clauses."""
    from contract_lifecycle.agents.legal_analyst import LegalAnalystAgent
    from contract_lifecycle.agents.risk_assessor import RiskAssessorAgent
    from contract_lifecycle.models import ContractType

    analyst = LegalAnalystAgent()
    analysis = await analyst.analyze_contract(SAMPLE_CONTRACT)

    assessor = RiskAssessorAgent()
    risks = await assessor.assess_risks(analysis.clauses, ContractType.NDA)

    assert isinstance(risks, list)
    # NDA with aggressive non-compete should flag some risks
    assert len(risks) > 0


@pytest.mark.asyncio
async def test_approval_router():
    """ApprovalRouterAgent determines correct approval chain."""
    from contract_lifecycle.agents.approval_router import ApprovalRouterAgent
    from contract_lifecycle.models import ApprovalLevel, ContractType, RiskLevel

    agent = ApprovalRouterAgent()

    # Low risk should get auto-approve
    low_chain = await agent.determine_approval_chain(
        RiskLevel.LOW, 10000.0, ContractType.NDA
    )
    assert ApprovalLevel.AUTO in low_chain

    # Critical risk should require multiple levels
    critical_chain = await agent.determine_approval_chain(
        RiskLevel.CRITICAL, 1000000.0, ContractType.VENDOR_MSA
    )
    assert len(critical_chain) >= 3


@pytest.mark.asyncio
async def test_negotiation_strategist():
    """NegotiationStrategistAgent develops counter-proposals."""
    from contract_lifecycle.agents.negotiation_strategist import (
        NegotiationStrategistAgent,
    )
    from contract_lifecycle.models import Clause, RiskAssessment, RiskLevel

    agent = NegotiationStrategistAgent()

    clauses = [
        Clause(
            id="c-1",
            title="Non-Compete",
            text="5 year non-compete in all markets",
            section="4",
            is_standard=False,
            risk_flags=["excessive_duration", "overbroad_scope"],
        ),
    ]
    risks = [
        RiskAssessment(
            clause_id="c-1",
            risk_level=RiskLevel.HIGH,
            description="Non-compete is overly broad",
            recommendation="Reduce to 1-2 years in specific market",
        ),
    ]

    positions = await agent.develop_strategy(risks, clauses)
    assert len(positions) >= 1
    assert positions[0].proposed_terms


@pytest.mark.asyncio
async def test_mock_contracts():
    """Mock data provides sample contracts."""
    from contract_lifecycle.mock_data.contracts import MOCK_CONTRACTS

    assert len(MOCK_CONTRACTS) >= 3


@pytest.mark.asyncio
async def test_mock_templates():
    """Mock data provides contract templates."""
    from contract_lifecycle.mock_data.templates import CONTRACT_TEMPLATES

    assert len(CONTRACT_TEMPLATES) >= 2


@pytest.mark.asyncio
async def test_clause_extraction_tool():
    """Clause extraction tool parses contract text."""
    from contract_lifecycle.tools.clause_tools import extract_clauses

    clauses = extract_clauses(SAMPLE_CONTRACT)
    assert len(clauses) >= 3
    titles = [c.title.lower() for c in clauses]
    assert any("confidential" in t for t in titles)
