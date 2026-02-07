"""Mock legal precedent database for risk assessment.

Maps clause types to outcomes and recommendations drawn from
(fictitious) case law to support the risk assessor agent.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Precedent:
    """A single legal precedent entry."""

    id: str
    clause_type: str
    case_name: str
    jurisdiction: str
    year: int
    outcome: str
    recommendation: str
    risk_impact: str  # "increases_risk" | "decreases_risk" | "neutral"


PRECEDENT_DATABASE: list[Precedent] = [
    Precedent(
        id="PREC-001",
        clause_type="unlimited_liability",
        case_name="TechCorp v. CloudServices Inc., 2023 Del. Ch. 1847",
        jurisdiction="Delaware",
        year=2023,
        outcome=(
            "Court enforced unlimited liability clause. Defendant ordered to pay "
            "$4.2M in consequential damages that exceeded contract value by 10x."
        ),
        recommendation=(
            "Always cap total liability at 12 months of fees paid. Exclude "
            "consequential and indirect damages."
        ),
        risk_impact="increases_risk",
    ),
    Precedent(
        id="PREC-002",
        clause_type="auto_renewal",
        case_name="SMB Alliance v. SaaSProvider Corp., 2022 Cal. App. 2d 445",
        jurisdiction="California",
        year=2022,
        outcome=(
            "Auto-renewal clause with 30-day notice period upheld despite "
            "customer's claim of insufficient notice. Customer locked into "
            "additional 12-month term at increased pricing."
        ),
        recommendation=(
            "Require at least 60-day notice period for non-renewal. Cap price "
            "increases on renewal at 5% or CPI."
        ),
        risk_impact="increases_risk",
    ),
    Precedent(
        id="PREC-003",
        clause_type="non_compete",
        case_name="InnovateTech v. Former Employee, 2024 Wash. App. 119",
        jurisdiction="Washington",
        year=2024,
        outcome=(
            "Non-compete clause of 36 months deemed unreasonable and struck down. "
            "Court limited enforceability to 12 months within specific market segment."
        ),
        recommendation=(
            "Limit non-compete duration to 12 months maximum. Narrow geographic "
            "and market-segment scope to be enforceable."
        ),
        risk_impact="increases_risk",
    ),
    Precedent(
        id="PREC-004",
        clause_type="ip_ownership",
        case_name="DevStudio LLC v. ClientCo, 2023 N.Y. Sup. Ct. 3201",
        jurisdiction="New York",
        year=2023,
        outcome=(
            "Ambiguous IP clause resulted in dispute over custom software ownership. "
            "Court ruled in favor of developer due to lack of explicit work-for-hire "
            "language, costing client $800K in re-development."
        ),
        recommendation=(
            "Clearly specify work-for-hire provisions. Distinguish between "
            "pre-existing IP and newly created work product."
        ),
        risk_impact="increases_risk",
    ),
    Precedent(
        id="PREC-005",
        clause_type="termination",
        case_name="VendorFirst v. Enterprise Client, 2024 Del. Super. 782",
        jurisdiction="Delaware",
        year=2024,
        outcome=(
            "Unilateral termination by vendor without cause upheld under contract "
            "terms. Client lost critical service with only 30 days to migrate, "
            "resulting in $1.5M in transition costs."
        ),
        recommendation=(
            "Ensure both parties have equal termination rights. Require minimum "
            "90-day notice for termination without cause."
        ),
        risk_impact="increases_risk",
    ),
    Precedent(
        id="PREC-006",
        clause_type="sla_penalties",
        case_name="HostingPro v. WebRetail Inc., 2023 Cal. Super. Ct. 1099",
        jurisdiction="California",
        year=2023,
        outcome=(
            "SLA with service credits as sole remedy upheld. Customer unable to "
            "recover actual damages from extended outage despite $2M in lost revenue."
        ),
        recommendation=(
            "Include right to terminate without penalty if SLA is repeatedly missed. "
            "Define actual damage recovery for outages exceeding certain thresholds."
        ),
        risk_impact="neutral",
    ),
    Precedent(
        id="PREC-007",
        clause_type="data_protection",
        case_name="EU DPA v. US Cloud Provider, 2024 CJEU C-311/24",
        jurisdiction="European Union",
        year=2024,
        outcome=(
            "Cloud provider fined EUR 2.1M for inadequate data processing agreement. "
            "Lack of explicit sub-processor notification and breach notification "
            "clauses cited as key failures."
        ),
        recommendation=(
            "Include GDPR-compliant data processing addendum. Require 72-hour "
            "breach notification and explicit sub-processor approval process."
        ),
        risk_impact="increases_risk",
    ),
    Precedent(
        id="PREC-008",
        clause_type="indemnification",
        case_name="ServiceCo v. TechBuyer LLC, 2022 Tex. App. 4th 2847",
        jurisdiction="Texas",
        year=2022,
        outcome=(
            "One-sided indemnification clause enforced. Customer required to "
            "indemnify provider for claims arising from provider's own negligence. "
            "Customer paid $600K in legal fees."
        ),
        recommendation=(
            "Ensure mutual indemnification obligations. Each party should "
            "indemnify for its own negligence and breach."
        ),
        risk_impact="increases_risk",
    ),
    Precedent(
        id="PREC-009",
        clause_type="confidentiality_scope",
        case_name="DataLeaks Inc. v. PartnerCorp, 2024 Mass. Super. 441",
        jurisdiction="Massachusetts",
        year=2024,
        outcome=(
            "Overly broad definition of confidential information deemed "
            "unenforceable. Court held that 'all information in any form' was "
            "too vague to provide adequate notice."
        ),
        recommendation=(
            "Define confidential information with reasonable specificity. "
            "Include clear exclusions for publicly available information."
        ),
        risk_impact="neutral",
    ),
    Precedent(
        id="PREC-010",
        clause_type="limitation_of_liability",
        case_name="MedTech Solutions v. Hospital Network, 2024 Ill. App. 2d 156",
        jurisdiction="Illinois",
        year=2024,
        outcome=(
            "Liability cap of 12 months' fees upheld as reasonable. Consequential "
            "damages waiver enforced despite significant patient-data exposure."
        ),
        recommendation=(
            "Standard 12-month fee cap is commercially reasonable and enforceable. "
            "Consider carve-outs for data breaches and IP infringement."
        ),
        risk_impact="decreases_risk",
    ),
]


def lookup_precedent(clause_type: str) -> Precedent | None:
    """Find the most relevant precedent for a given clause type.

    Returns the first matching precedent or ``None`` if no match is found.
    """
    # Normalize the search term
    normalized = clause_type.lower().replace(" ", "_").replace("-", "_")
    for precedent in PRECEDENT_DATABASE:
        if normalized in precedent.clause_type or precedent.clause_type in normalized:
            return precedent
    return None


def get_all_precedents() -> list[Precedent]:
    """Return the full precedent database."""
    return list(PRECEDENT_DATABASE)
