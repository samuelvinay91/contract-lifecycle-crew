"""Standard clause templates for each contract type.

Provides "safe" versions of commonly risky clauses that can be used as
negotiation recommendations by the negotiation strategist agent.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Standard safe clause templates by category
# ---------------------------------------------------------------------------

LIMITATION_OF_LIABILITY_SAFE = (
    "Each party's total aggregate liability under this Agreement shall not exceed "
    "the total fees paid or payable during the twelve (12) months preceding the "
    "event giving rise to the claim. In no event shall either party be liable for "
    "any indirect, incidental, special, consequential, or punitive damages."
)

AUTO_RENEWAL_SAFE = (
    "This Agreement shall renew for successive twelve-month periods unless either "
    "party provides written notice of non-renewal at least sixty (60) days prior "
    "to the end of the then-current term. Upon renewal, pricing adjustments shall "
    "not exceed 5% of the prior term's fees without mutual written agreement."
)

NON_COMPETE_SAFE = (
    "For twelve (12) months following termination, neither party shall directly "
    "compete with the other party in the specific product categories that were "
    "the subject of this Agreement, limited to the geographic regions where the "
    "other party actively conducts business."
)

TERMINATION_BALANCED = (
    "Either party may terminate this Agreement (a) for cause upon thirty (30) days "
    "written notice if the other party materially breaches any provision and fails "
    "to cure within the notice period, or (b) for convenience upon sixty (60) days "
    "written notice. Upon termination for convenience, the terminating party shall "
    "pay for all services rendered through the effective date of termination."
)

IP_OWNERSHIP_BALANCED = (
    "All pre-existing intellectual property remains the property of the originating "
    "party. Work product created specifically for and paid for by Customer under "
    "this Agreement shall be owned by Customer upon full payment. Provider retains "
    "ownership of its pre-existing tools, methodologies, and general know-how."
)

CONFIDENTIALITY_STANDARD = (
    "Each party agrees to maintain the confidentiality of the other party's "
    "proprietary information using at least the same degree of care it uses to "
    "protect its own confidential information, but no less than reasonable care. "
    "This obligation shall survive termination for a period of three (3) years, "
    "except for trade secrets which shall be protected indefinitely."
)

INDEMNIFICATION_MUTUAL = (
    "Each party shall indemnify, defend, and hold harmless the other party from "
    "any third-party claims, damages, losses, and reasonable expenses (including "
    "attorney fees) arising from the indemnifying party's (a) negligence or willful "
    "misconduct, (b) breach of this Agreement, or (c) violation of applicable law."
)

SLA_WITH_TEETH = (
    "Provider guarantees 99.9% uptime availability measured monthly. If availability "
    "falls below the guaranteed level: (a) below 99.9%: 10% service credit; "
    "(b) below 99.5%: 25% service credit; (c) below 99.0%: Customer may terminate "
    "without penalty. Service credits are applied to the next invoice and are "
    "Customer's sole remedy for downtime."
)

DATA_PROTECTION_GDPR = (
    "Provider shall process personal data only on documented instructions from "
    "Customer. Provider shall implement appropriate technical and organizational "
    "measures to ensure a level of security appropriate to the risk, including "
    "encryption of data in transit and at rest. Provider shall notify Customer "
    "within 72 hours of becoming aware of any personal data breach."
)

FORCE_MAJEURE_STANDARD = (
    "Neither party shall be liable for any delay or failure to perform its "
    "obligations under this Agreement due to causes beyond its reasonable control, "
    "including natural disasters, war, terrorism, pandemics, government actions, "
    "or infrastructure failures. The affected party shall promptly notify the other "
    "party and use commercially reasonable efforts to resume performance."
)

# ---------------------------------------------------------------------------
# Templates organized by contract type
# ---------------------------------------------------------------------------

SAAS_AGREEMENT_TEMPLATES: dict[str, str] = {
    "limitation_of_liability": LIMITATION_OF_LIABILITY_SAFE,
    "auto_renewal": AUTO_RENEWAL_SAFE,
    "termination": TERMINATION_BALANCED,
    "ip_ownership": IP_OWNERSHIP_BALANCED,
    "confidentiality": CONFIDENTIALITY_STANDARD,
    "indemnification": INDEMNIFICATION_MUTUAL,
    "sla": SLA_WITH_TEETH,
    "data_protection": DATA_PROTECTION_GDPR,
    "force_majeure": FORCE_MAJEURE_STANDARD,
}

NDA_TEMPLATES: dict[str, str] = {
    "confidentiality": CONFIDENTIALITY_STANDARD,
    "non_compete": NON_COMPETE_SAFE,
    "termination": TERMINATION_BALANCED,
}

VENDOR_MSA_TEMPLATES: dict[str, str] = {
    "limitation_of_liability": LIMITATION_OF_LIABILITY_SAFE,
    "termination": TERMINATION_BALANCED,
    "ip_ownership": IP_OWNERSHIP_BALANCED,
    "sla": SLA_WITH_TEETH,
    "indemnification": INDEMNIFICATION_MUTUAL,
    "data_protection": DATA_PROTECTION_GDPR,
    "force_majeure": FORCE_MAJEURE_STANDARD,
}

EMPLOYMENT_TEMPLATES: dict[str, str] = {
    "non_compete": NON_COMPETE_SAFE,
    "confidentiality": CONFIDENTIALITY_STANDARD,
    "ip_ownership": IP_OWNERSHIP_BALANCED,
    "termination": TERMINATION_BALANCED,
}

CONSULTING_TEMPLATES: dict[str, str] = {
    "limitation_of_liability": LIMITATION_OF_LIABILITY_SAFE,
    "termination": TERMINATION_BALANCED,
    "ip_ownership": IP_OWNERSHIP_BALANCED,
    "confidentiality": CONFIDENTIALITY_STANDARD,
    "indemnification": INDEMNIFICATION_MUTUAL,
}

LICENSING_TEMPLATES: dict[str, str] = {
    "limitation_of_liability": LIMITATION_OF_LIABILITY_SAFE,
    "termination": TERMINATION_BALANCED,
    "ip_ownership": IP_OWNERSHIP_BALANCED,
    "confidentiality": CONFIDENTIALITY_STANDARD,
    "indemnification": INDEMNIFICATION_MUTUAL,
}

CONTRACT_TEMPLATES: dict[str, dict[str, str]] = {
    "saas_agreement": SAAS_AGREEMENT_TEMPLATES,
    "nda": NDA_TEMPLATES,
    "vendor_msa": VENDOR_MSA_TEMPLATES,
    "employment": EMPLOYMENT_TEMPLATES,
    "consulting": CONSULTING_TEMPLATES,
    "licensing": LICENSING_TEMPLATES,
}
