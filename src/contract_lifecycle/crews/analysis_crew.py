"""Analysis Crew - hierarchical crew for contract analysis and risk assessment.

Combines the Legal Analyst (manager), Risk Assessor, and Compliance
Officer agents in a hierarchical process where the Legal Analyst
coordinates analysis, risk assessment, and compliance checking.
"""

from __future__ import annotations

from typing import Any

import structlog

from contract_lifecycle.agents.compliance_officer import ComplianceOfficerAgent
from contract_lifecycle.agents.legal_analyst import LegalAnalystAgent
from contract_lifecycle.agents.risk_assessor import RiskAssessorAgent
from contract_lifecycle.models import (
    ContractAnalysis,
    RiskAssessment,
)

logger = structlog.get_logger(__name__)


class AnalysisCrew:
    """Hierarchical crew for contract analysis.

    Agents:
        - Legal Analyst (manager): analyzes contract and coordinates
        - Risk Assessor: evaluates clause-level risk
        - Compliance Officer: checks regulatory compliance

    Process: ``"hierarchical"`` -- the Legal Analyst acts as the
    manager agent, delegating to Risk Assessor and Compliance Officer.

    Task sequence:
        1. Analyze contract -> extract clauses and metadata
        2. Assess risk -> evaluate each clause for risk
        3. Check compliance -> verify regulatory requirements
    """

    def __init__(self) -> None:
        self.legal_analyst = LegalAnalystAgent()
        self.risk_assessor = RiskAssessorAgent()
        self.compliance_officer = ComplianceOfficerAgent()
        self.process = "hierarchical"
        self.manager_agent = self.legal_analyst
        self.verbose = True

    async def kickoff(self, contract_text: str) -> dict[str, Any]:
        """Execute the analysis crew workflow.

        Runs the three agents in sequence: analyze, assess risk, then
        check compliance. The Legal Analyst's output feeds into the
        Risk Assessor and Compliance Officer.

        Args:
            contract_text: The full text of the contract to analyze.

        Returns:
            A dictionary containing:
            - ``analysis``: The :class:`ContractAnalysis` result.
            - ``risk_assessments``: List of :class:`RiskAssessment` from
              the Risk Assessor.
            - ``compliance_issues``: List of :class:`RiskAssessment` from
              the Compliance Officer.
            - ``all_risks``: Combined list of all risk assessments.
        """
        logger.info("analysis_crew_kickoff", text_length=len(contract_text))

        # Step 1: Legal Analyst analyzes the contract
        logger.info("analysis_crew_step", step=1, agent="Legal Analyst")
        analysis: ContractAnalysis = await self.legal_analyst.analyze_contract(
            contract_text
        )

        # Step 2: Risk Assessor evaluates each clause
        logger.info("analysis_crew_step", step=2, agent="Risk Assessor")
        risk_assessments: list[RiskAssessment] = await self.risk_assessor.assess_risks(
            analysis.clauses, analysis.contract_type
        )

        # Step 3: Compliance Officer checks regulatory requirements
        logger.info("analysis_crew_step", step=3, agent="Compliance Officer")
        compliance_issues: list[RiskAssessment] = (
            await self.compliance_officer.check_compliance(
                analysis, analysis.clauses
            )
        )

        # Merge all risks for downstream processing
        all_risks = risk_assessments + compliance_issues

        result = {
            "analysis": analysis,
            "risk_assessments": risk_assessments,
            "compliance_issues": compliance_issues,
            "all_risks": all_risks,
        }

        logger.info(
            "analysis_crew_complete",
            clauses=len(analysis.clauses),
            risk_assessments=len(risk_assessments),
            compliance_issues=len(compliance_issues),
        )
        return result
