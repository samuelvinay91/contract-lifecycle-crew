"""Risk Assessment Specialist agent.

Evaluates each clause for legal, financial, and operational risk using
heuristic rules. Flags unlimited liability, auto-renewal traps,
excessive non-competes, unilateral termination, unclear IP ownership,
and missing SLA penalties.
"""

from __future__ import annotations

import re

import structlog

from contract_lifecycle.models import (
    Clause,
    ContractType,
    RiskAssessment,
    RiskLevel,
)
from contract_lifecycle.tools.risk_tools import estimate_liability, lookup_precedent

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# CrewAI-style agent metadata
# ---------------------------------------------------------------------------

ROLE = "Risk Assessment Specialist"
GOAL = (
    "Evaluate each clause for legal, financial, and operational risk. "
    "Identify potential exposure, quantify liability, and provide "
    "actionable recommendations."
)
BACKSTORY = (
    "You are a former Big Four consulting partner specializing in enterprise "
    "risk management. With 20 years of experience across Fortune 500 companies, "
    "you have developed proprietary risk frameworks used by over 200 organizations. "
    "You are certified in CISA, CRISC, and hold an MBA from Wharton. Your risk "
    "assessments have prevented over $500M in potential losses."
)

# ---------------------------------------------------------------------------
# Risk assessment rules
# ---------------------------------------------------------------------------

_RISK_RULES: list[dict[str, object]] = [
    {
        "flag": "unlimited_liability",
        "risk_level": RiskLevel.CRITICAL,
        "description": (
            "Unlimited liability clause exposes the organization to uncapped "
            "financial risk. This includes direct, indirect, consequential, and "
            "incidental damages without any ceiling."
        ),
        "recommendation": (
            "Negotiate a liability cap tied to 12 months of fees paid. Exclude "
            "consequential and indirect damages. Add carve-outs only for gross "
            "negligence, willful misconduct, and IP infringement."
        ),
        "precedent_key": "unlimited_liability",
    },
    {
        "flag": "auto_renewal",
        "risk_level": RiskLevel.MEDIUM,
        "description": (
            "Auto-renewal clause may lock the organization into extended terms "
            "with insufficient notice period. Risk of being bound to unfavorable "
            "pricing or terms after initial period."
        ),
        "recommendation": (
            "Extend the non-renewal notice period to at least 60 days. Add a "
            "cap on price increases upon renewal (e.g., 5% or CPI). Include "
            "right to renegotiate terms at each renewal."
        ),
        "precedent_key": "auto_renewal",
    },
    {
        "flag": "unilateral_termination",
        "risk_level": RiskLevel.HIGH,
        "description": (
            "Vendor/provider has the right to terminate without cause, creating "
            "business continuity risk. Customer may face unexpected service "
            "disruption and migration costs."
        ),
        "recommendation": (
            "Negotiate mutual termination rights. Require minimum 90-day notice "
            "for termination without cause. Add transition assistance obligations "
            "and data export provisions."
        ),
        "precedent_key": "termination",
    },
    {
        "flag": "broad_non_compete",
        "risk_level": RiskLevel.HIGH,
        "description": (
            "Non-compete clause is overly broad in geographic scope (worldwide) "
            "or market coverage (any market segment). May be unenforceable in "
            "certain jurisdictions and restricts business opportunities."
        ),
        "recommendation": (
            "Narrow the scope to specific product categories and geographic "
            "regions where the other party actively operates. Many jurisdictions "
            "will not enforce overly broad non-competes."
        ),
        "precedent_key": "non_compete",
    },
    {
        "flag": "long_non_compete",
        "risk_level": RiskLevel.HIGH,
        "description": (
            "Non-compete duration exceeds 12 months, which courts in many "
            "jurisdictions consider unreasonable. Extended non-compete periods "
            "may be struck down entirely rather than modified."
        ),
        "recommendation": (
            "Reduce non-compete duration to 12 months maximum. Courts in "
            "California, for example, generally refuse to enforce non-competes "
            "entirely. Even in enforceable jurisdictions, 12 months is the "
            "typical maximum."
        ),
        "precedent_key": "non_compete",
    },
    {
        "flag": "one_sided_indemnification",
        "risk_level": RiskLevel.HIGH,
        "description": (
            "Indemnification obligations are one-sided, requiring only one party "
            "to indemnify the other. This creates an unbalanced risk allocation "
            "that may include indemnification for the other party's negligence."
        ),
        "recommendation": (
            "Negotiate mutual indemnification where each party indemnifies for "
            "its own negligence, breach, and legal violations. Add a requirement "
            "for the indemnified party to mitigate damages."
        ),
        "precedent_key": "indemnification",
    },
    {
        "flag": "broad_confidentiality",
        "risk_level": RiskLevel.MEDIUM,
        "description": (
            "Confidentiality definition is overly broad, covering 'ALL information "
            "in ANY form.' This may be unenforceable and creates compliance burden "
            "for tracking what constitutes confidential information."
        ),
        "recommendation": (
            "Define confidential information with reasonable specificity. Include "
            "standard exclusions for publicly available information, independently "
            "developed information, and information received from third parties."
        ),
        "precedent_key": "confidentiality_scope",
    },
    {
        "flag": "ip_favors_provider",
        "risk_level": RiskLevel.HIGH,
        "description": (
            "IP ownership clause assigns all intellectual property exclusively to "
            "the provider, including customizations and integrations developed "
            "for and paid by the customer."
        ),
        "recommendation": (
            "Negotiate work-for-hire provisions where customer-funded work product "
            "is owned by customer. Provider retains pre-existing IP and general "
            "know-how. Clearly define boundaries between pre-existing and new IP."
        ),
        "precedent_key": "ip_ownership",
    },
    {
        "flag": "high_interest_rate",
        "risk_level": RiskLevel.MEDIUM,
        "description": (
            "Late payment interest rate exceeds typical commercial rates and may "
            "exceed usury limits in some jurisdictions (e.g., 1.5% per month = "
            "18% annually)."
        ),
        "recommendation": (
            "Negotiate interest rate to prime rate + 2% or 1% per month maximum. "
            "Ensure compliance with applicable usury laws."
        ),
        "precedent_key": "limitation_of_liability",
    },
    {
        "flag": "missing_data_protection",
        "risk_level": RiskLevel.LOW,
        "description": (
            "Contract references data protection or GDPR compliance, which is "
            "standard for agreements involving personal data processing."
        ),
        "recommendation": (
            "Verify data protection provisions include: lawful basis for "
            "processing, data breach notification (72 hours), sub-processor "
            "controls, data subject rights, and international transfer safeguards."
        ),
        "precedent_key": "data_protection",
    },
]


class RiskAssessorAgent:
    """Risk Assessment Specialist agent.

    Evaluates each clause for legal, financial, and operational risk
    using heuristic rules and precedent lookups.
    """

    def __init__(self) -> None:
        self.role = ROLE
        self.goal = GOAL
        self.backstory = BACKSTORY
        self.tools = ["calculate_risk_matrix", "lookup_precedent", "estimate_liability"]
        self.verbose = True

    async def assess_risks(
        self,
        clauses: list[Clause],
        contract_type: ContractType,
    ) -> list[RiskAssessment]:
        """Assess risk for each clause based on its risk flags.

        Iterates over all clauses, matches risk flags to predefined
        rules, looks up legal precedents, and produces a risk assessment
        for each flagged clause.

        Args:
            clauses: Extracted clauses from the contract.
            contract_type: The type of contract being assessed.

        Returns:
            A list of :class:`RiskAssessment` objects for flagged clauses.
        """
        logger.info(
            "risk_assessment_starting",
            clause_count=len(clauses),
            contract_type=contract_type.value,
        )

        assessments: list[RiskAssessment] = []

        for clause in clauses:
            if not clause.risk_flags:
                # Standard clause, still provide a low-risk assessment
                assessments.append(
                    RiskAssessment(
                        clause_id=clause.id,
                        risk_level=RiskLevel.LOW,
                        description=(
                            f"Clause '{clause.title}' uses standard terms with "
                            f"no identified risk flags."
                        ),
                        recommendation="No changes required. Terms are commercially standard.",
                        precedent_reference=None,
                    )
                )
                continue

            # Find the highest-severity rule that matches
            for flag in clause.risk_flags:
                rule = self._find_rule(flag)
                if rule is None:
                    continue

                # Lookup precedent
                precedent_key = str(rule.get("precedent_key", ""))
                precedent_ref = lookup_precedent(precedent_key)

                # Estimate liability if relevant
                liability = estimate_liability(clause.text)
                description = str(rule["description"])
                if liability > 0:
                    description += f" Estimated liability exposure: ${liability:,.2f}."

                assessments.append(
                    RiskAssessment(
                        clause_id=clause.id,
                        risk_level=rule["risk_level"],  # type: ignore[arg-type]
                        description=description,
                        recommendation=str(rule["recommendation"]),
                        precedent_reference=precedent_ref,
                    )
                )

        logger.info(
            "risk_assessment_complete",
            assessments=len(assessments),
            high_risk=sum(1 for a in assessments if a.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)),
        )
        return assessments

    def _find_rule(self, flag: str) -> dict[str, object] | None:
        """Find the risk rule matching a given flag name."""
        for rule in _RISK_RULES:
            if rule["flag"] == flag:
                return rule
        return None
