"""Senior Legal Analyst agent.

Analyzes contracts thoroughly, extracts all clauses, identifies key
terms, and summarizes obligations and rights. Uses regex-based
heuristics for clause extraction so no API keys are required.
"""

from __future__ import annotations

import re
from datetime import datetime

import structlog

from contract_lifecycle.models import (
    Clause,
    ContractAnalysis,
    ContractType,
)
from contract_lifecycle.tools.clause_tools import extract_clauses

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# CrewAI-style agent metadata
# ---------------------------------------------------------------------------

ROLE = "Senior Legal Analyst"
GOAL = (
    "Analyze contracts thoroughly, extract all clauses, identify key terms, "
    "and summarize obligations and rights for each party."
)
BACKSTORY = (
    "You are a senior legal analyst with 15 years of corporate law experience "
    "specializing in technology agreements, vendor contracts, and SaaS licensing. "
    "You have reviewed over 5,000 contracts and are known for your meticulous "
    "attention to detail and ability to identify subtle risks that others miss. "
    "You hold a J.D. from Harvard Law School and are a member of the bar in "
    "New York, California, and Delaware."
)

# ---------------------------------------------------------------------------
# Contract type detection patterns
# ---------------------------------------------------------------------------

_TYPE_PATTERNS: dict[ContractType, list[re.Pattern[str]]] = {
    ContractType.NDA: [
        re.compile(r"non-disclosure\s+agreement|nda|confidentiality\s+agreement", re.IGNORECASE),
    ],
    ContractType.SAAS_AGREEMENT: [
        re.compile(r"saas\s+agreement|software.as.a.service|subscription\s+agreement", re.IGNORECASE),
    ],
    ContractType.VENDOR_MSA: [
        re.compile(r"master\s+service\s+agreement|msa|vendor\s+agreement", re.IGNORECASE),
    ],
    ContractType.EMPLOYMENT: [
        re.compile(r"employment\s+agreement|offer\s+letter|employment\s+contract", re.IGNORECASE),
    ],
    ContractType.CONSULTING: [
        re.compile(r"consulting\s+agreement|consultant\s+contract|independent\s+contractor", re.IGNORECASE),
    ],
    ContractType.LICENSING: [
        re.compile(r"licen[sc]ing\s+agreement|license\s+agreement|licen[sc]e\s+grant", re.IGNORECASE),
    ],
}

# ---------------------------------------------------------------------------
# Party extraction patterns
# ---------------------------------------------------------------------------

_PARTY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r'by\s+and\s+between\s+(.+?)\s*\(".*?"\)\s+and\s+(.+?)\s*\(".*?"\)',
        re.IGNORECASE,
    ),
    re.compile(
        r'between\s+(.+?)\s*\(".*?"\)\s+and\s+(.+?)\s*\(".*?"\)',
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Date extraction patterns
# ---------------------------------------------------------------------------

_DATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:effective\s+(?:date|as\s+of)|entered\s+into\s+as\s+of|commenc(?:e|ing)\s+on)\s+"
        r"(\w+\s+\d{1,2},?\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:as\s+of)\s+(\w+\s+\d{1,2},?\s+\d{4})",
        re.IGNORECASE,
    ),
]

_EXPIRATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:initial\s+term\s+of|continue\s+for)\s+"
        r"(?:an?\s+)?(\w+)\s*\(?\d*\)?\s*(?:months?|years?)",
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Value extraction patterns
# ---------------------------------------------------------------------------

_VALUE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?:total\s+(?:contract\s+)?value|total\s+compensation)[:\s]*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"\$([\d,]+(?:\.\d+)?)\s*(?:annually|per\s+year|per\s+annum)", re.IGNORECASE),
    re.compile(r"(?:annual|yearly)\s+.*?\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE),
]


class LegalAnalystAgent:
    """Senior Legal Analyst agent for contract analysis.

    Mirrors CrewAI's Agent interface while using pure heuristic logic
    so the agent works without any API keys.
    """

    def __init__(self) -> None:
        self.role = ROLE
        self.goal = GOAL
        self.backstory = BACKSTORY
        self.tools = ["extract_clauses", "check_standard_terms"]
        self.verbose = True

    async def analyze_contract(self, contract_text: str) -> ContractAnalysis:
        """Perform full contract analysis.

        Extracts contract type, parties, dates, value, and all clauses
        from the raw contract text using regex-based heuristics.

        Args:
            contract_text: The full text of the contract.

        Returns:
            A :class:`ContractAnalysis` with all extracted information.
        """
        logger.info("legal_analyst_starting", text_length=len(contract_text))

        contract_type = self._detect_contract_type(contract_text)
        parties = self._extract_parties(contract_text)
        effective_date = self._extract_effective_date(contract_text)
        expiration_date = self._extract_expiration_date(contract_text)
        total_value = self._extract_value(contract_text)
        clauses = extract_clauses(contract_text)
        summary = self._generate_summary(
            contract_type, parties, clauses, total_value
        )

        analysis = ContractAnalysis(
            contract_type=contract_type,
            parties=parties,
            effective_date=effective_date,
            expiration_date=expiration_date,
            total_value=total_value,
            clauses=clauses,
            summary=summary,
        )

        logger.info(
            "legal_analyst_complete",
            contract_type=contract_type.value,
            parties=parties,
            clauses_found=len(clauses),
            total_value=total_value,
        )
        return analysis

    def _detect_contract_type(self, text: str) -> ContractType:
        """Detect the contract type from title and content patterns."""
        for ctype, patterns in _TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text):
                    return ctype
        return ContractType.CONSULTING  # Default fallback

    def _extract_parties(self, text: str) -> list[str]:
        """Extract party names from the contract text."""
        for pattern in _PARTY_PATTERNS:
            match = pattern.search(text)
            if match:
                parties = [match.group(1).strip(), match.group(2).strip()]
                return parties
        return []

    def _extract_effective_date(self, text: str) -> str:
        """Extract the effective/commencement date."""
        for pattern in _DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_expiration_date(self, text: str) -> str:
        """Extract or compute the expiration date from term clauses."""
        for pattern in _EXPIRATION_PATTERNS:
            match = pattern.search(text)
            if match:
                term_word = match.group(1).lower()
                # Map common English numbers to digits
                word_to_num = {
                    "one": 1, "two": 2, "three": 3, "four": 4,
                    "six": 6, "twelve": 12, "twenty-four": 24,
                    "twenty": 20, "thirty-six": 36,
                }
                months = word_to_num.get(term_word)
                if months is None:
                    try:
                        months = int(term_word)
                    except ValueError:
                        months = 12
                return f"{months} months from effective date"
        return ""

    def _extract_value(self, text: str) -> float:
        """Extract the total contract value."""
        for pattern in _VALUE_PATTERNS:
            match = pattern.search(text)
            if match:
                value_str = match.group(1).replace(",", "")
                try:
                    return float(value_str)
                except ValueError:
                    continue
        return 0.0

    def _generate_summary(
        self,
        contract_type: ContractType,
        parties: list[str],
        clauses: list[Clause],
        total_value: float,
    ) -> str:
        """Generate a human-readable analysis summary."""
        party_str = " and ".join(parties) if parties else "Unknown parties"
        risky_count = sum(1 for c in clauses if not c.is_standard)
        standard_count = sum(1 for c in clauses if c.is_standard)

        all_flags: list[str] = []
        for c in clauses:
            all_flags.extend(c.risk_flags)
        unique_flags = list(set(all_flags))

        summary_parts = [
            f"This is a {contract_type.value.replace('_', ' ').title()} between {party_str}.",
            f"Total contract value: ${total_value:,.2f}." if total_value > 0 else "",
            f"The contract contains {len(clauses)} identified clauses: "
            f"{standard_count} standard and {risky_count} requiring review.",
        ]

        if unique_flags:
            flags_str = ", ".join(f.replace("_", " ") for f in unique_flags)
            summary_parts.append(f"Risk flags identified: {flags_str}.")

        if risky_count > 0:
            summary_parts.append(
                "Recommendation: Engage risk assessment and negotiation teams "
                "before proceeding with execution."
            )
        else:
            summary_parts.append(
                "Overall assessment: Contract terms appear standard and low-risk."
            )

        return " ".join(part for part in summary_parts if part)
