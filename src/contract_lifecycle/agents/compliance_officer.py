"""Compliance Officer agent.

Ensures contracts meet regulatory requirements and internal policies,
including GDPR data processing clauses, SOX financial controls, and
industry-specific regulations.
"""

from __future__ import annotations

import re

import structlog

from contract_lifecycle.models import (
    Clause,
    ContractAnalysis,
    ContractType,
    RiskAssessment,
    RiskLevel,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# CrewAI-style agent metadata
# ---------------------------------------------------------------------------

ROLE = "Compliance Officer"
GOAL = (
    "Ensure contracts meet regulatory requirements and internal policies. "
    "Verify GDPR compliance, SOX controls, and industry-specific regulations."
)
BACKSTORY = (
    "You are the Chief Compliance Officer with expertise in regulatory "
    "frameworks across multiple jurisdictions. With 18 years of experience "
    "in financial services, healthcare, and technology sectors, you have "
    "built compliance programs that have passed every regulatory audit. "
    "You hold certifications in CIPP/US, CIPP/E, CCEP, and are a licensed "
    "attorney. You have a zero-tolerance approach to compliance gaps."
)

# ---------------------------------------------------------------------------
# Compliance check definitions
# ---------------------------------------------------------------------------

_GDPR_REQUIREMENTS = [
    ("data_processing_basis", re.compile(
        r"lawful\s+basis|legitimate\s+interest|consent|contract\s+necessity",
        re.IGNORECASE,
    )),
    ("breach_notification", re.compile(
        r"(?:72|seventy.two)\s*hours?|breach\s+notif|data\s+breach",
        re.IGNORECASE,
    )),
    ("data_subject_rights", re.compile(
        r"data\s+subject|right\s+to\s+(?:access|erasure|portability|rectification)",
        re.IGNORECASE,
    )),
    ("sub_processor", re.compile(
        r"sub.?processor|sub.?contractor.*?data|third.party.*?process",
        re.IGNORECASE,
    )),
    ("international_transfer", re.compile(
        r"(?:standard\s+contractual|adequacy\s+decision|binding\s+corporate|data\s+transfer)",
        re.IGNORECASE,
    )),
]

_SOX_REQUIREMENTS = [
    ("financial_controls", re.compile(
        r"internal\s+control|financial\s+reporting|audit\s+trail",
        re.IGNORECASE,
    )),
    ("record_retention", re.compile(
        r"record\s+retention|document\s+preservation|data\s+retention",
        re.IGNORECASE,
    )),
    ("segregation_of_duties", re.compile(
        r"segregation\s+of\s+duties|separation\s+of\s+duties",
        re.IGNORECASE,
    )),
]

_GENERAL_COMPLIANCE = [
    ("governing_law", re.compile(
        r"governing\s+law|applicable\s+law|jurisdiction",
        re.IGNORECASE,
    )),
    ("dispute_resolution", re.compile(
        r"dispute\s+resolution|arbitration|mediation",
        re.IGNORECASE,
    )),
    ("force_majeure", re.compile(
        r"force\s+majeure",
        re.IGNORECASE,
    )),
    ("assignment", re.compile(
        r"assignment|transfer\s+of\s+(?:rights|obligations)",
        re.IGNORECASE,
    )),
    ("entire_agreement", re.compile(
        r"entire\s+agreement|whole\s+agreement|integration\s+clause",
        re.IGNORECASE,
    )),
]


class ComplianceOfficerAgent:
    """Compliance Officer agent for regulatory and policy checks.

    Scans the contract analysis and clause text against regulatory
    requirements (GDPR, SOX, general compliance) using heuristic
    pattern matching.
    """

    def __init__(self) -> None:
        self.role = ROLE
        self.goal = GOAL
        self.backstory = BACKSTORY
        self.tools: list[str] = []
        self.verbose = True

    async def check_compliance(
        self,
        analysis: ContractAnalysis,
        clauses: list[Clause],
    ) -> list[RiskAssessment]:
        """Check contract compliance against regulatory requirements.

        Evaluates the full contract text (via clauses) for GDPR, SOX,
        and general compliance gaps.

        Args:
            analysis: The contract analysis with type and party info.
            clauses: All extracted clauses.

        Returns:
            A list of :class:`RiskAssessment` objects for compliance gaps.
        """
        logger.info(
            "compliance_check_starting",
            contract_type=analysis.contract_type.value,
            clause_count=len(clauses),
        )

        full_text = " ".join(c.text for c in clauses)
        compliance_issues: list[RiskAssessment] = []

        # GDPR checks (applicable to all contract types involving data)
        if self._involves_data_processing(full_text, analysis.contract_type):
            gdpr_issues = self._check_gdpr(full_text, clauses)
            compliance_issues.extend(gdpr_issues)

        # SOX checks (applicable to agreements involving financial controls)
        if self._involves_financial_controls(analysis):
            sox_issues = self._check_sox(full_text, clauses)
            compliance_issues.extend(sox_issues)

        # General compliance checks
        general_issues = self._check_general_compliance(full_text, clauses)
        compliance_issues.extend(general_issues)

        logger.info(
            "compliance_check_complete",
            issues_found=len(compliance_issues),
            critical=sum(1 for i in compliance_issues if i.risk_level == RiskLevel.CRITICAL),
            high=sum(1 for i in compliance_issues if i.risk_level == RiskLevel.HIGH),
        )
        return compliance_issues

    def _involves_data_processing(
        self, full_text: str, contract_type: ContractType
    ) -> bool:
        """Determine if the contract involves personal data processing."""
        data_keywords = re.compile(
            r"personal\s+data|customer\s+data|user\s+data|PII|"
            r"data\s+process|GDPR|CCPA|privacy",
            re.IGNORECASE,
        )
        always_check = {
            ContractType.SAAS_AGREEMENT,
            ContractType.VENDOR_MSA,
        }
        return contract_type in always_check or bool(data_keywords.search(full_text))

    def _involves_financial_controls(self, analysis: ContractAnalysis) -> bool:
        """Determine if SOX controls are relevant."""
        return analysis.total_value >= 100_000 or analysis.contract_type in {
            ContractType.VENDOR_MSA,
            ContractType.SAAS_AGREEMENT,
        }

    def _check_gdpr(
        self, full_text: str, clauses: list[Clause]
    ) -> list[RiskAssessment]:
        """Check for GDPR compliance gaps."""
        issues: list[RiskAssessment] = []

        for req_name, pattern in _GDPR_REQUIREMENTS:
            if not pattern.search(full_text):
                # Find the most relevant clause to attach the issue to
                clause_id = self._find_relevant_clause_id(
                    clauses, ["data_protection", "confidentiality", "obligations"]
                )
                readable = req_name.replace("_", " ").title()

                issues.append(
                    RiskAssessment(
                        clause_id=clause_id,
                        risk_level=RiskLevel.HIGH,
                        description=(
                            f"GDPR compliance gap: Missing '{readable}' provision. "
                            f"Contracts involving personal data processing must include "
                            f"explicit {readable.lower()} requirements under GDPR Art. 28."
                        ),
                        recommendation=(
                            f"Add a Data Processing Addendum (DPA) that includes "
                            f"{readable.lower()} provisions. Reference standard "
                            f"contractual clauses approved by the European Commission."
                        ),
                        precedent_reference=None,
                    )
                )

        return issues

    def _check_sox(
        self, full_text: str, clauses: list[Clause]
    ) -> list[RiskAssessment]:
        """Check for SOX compliance gaps in high-value contracts."""
        issues: list[RiskAssessment] = []

        for req_name, pattern in _SOX_REQUIREMENTS:
            if not pattern.search(full_text):
                clause_id = self._find_relevant_clause_id(
                    clauses, ["payment", "scope", "obligations"]
                )
                readable = req_name.replace("_", " ").title()

                issues.append(
                    RiskAssessment(
                        clause_id=clause_id,
                        risk_level=RiskLevel.MEDIUM,
                        description=(
                            f"SOX compliance gap: Missing '{readable}' provision. "
                            f"Contracts exceeding $100K should include {readable.lower()} "
                            f"requirements for regulatory compliance."
                        ),
                        recommendation=(
                            f"Add {readable.lower()} clause requiring the vendor to "
                            f"maintain adequate controls and provide audit access."
                        ),
                        precedent_reference=None,
                    )
                )

        return issues

    def _check_general_compliance(
        self, full_text: str, clauses: list[Clause]
    ) -> list[RiskAssessment]:
        """Check for general compliance and best-practice gaps."""
        issues: list[RiskAssessment] = []

        for req_name, pattern in _GENERAL_COMPLIANCE:
            if not pattern.search(full_text):
                clause_id = self._find_relevant_clause_id(clauses, [req_name])
                readable = req_name.replace("_", " ").title()

                issues.append(
                    RiskAssessment(
                        clause_id=clause_id,
                        risk_level=RiskLevel.LOW,
                        description=(
                            f"Missing standard clause: '{readable}'. While not always "
                            f"legally required, this clause is considered best practice "
                            f"and is present in most enterprise agreements."
                        ),
                        recommendation=(
                            f"Consider adding a '{readable}' clause to strengthen "
                            f"the agreement and reduce ambiguity."
                        ),
                        precedent_reference=None,
                    )
                )

        return issues

    def _find_relevant_clause_id(
        self, clauses: list[Clause], preferred_sections: list[str]
    ) -> str:
        """Find the most relevant clause ID for attaching a compliance issue."""
        for section in preferred_sections:
            for clause in clauses:
                if section.lower() in clause.section.lower():
                    return clause.id
        # Fall back to first clause or generate a placeholder
        return clauses[0].id if clauses else "COMPLIANCE"
