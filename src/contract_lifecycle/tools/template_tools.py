"""Contract template retrieval and merging utilities.

Provides functions for loading standard clause templates by contract
type, merging template variables, and retrieving lists of standard
clauses for negotiation recommendations.
"""

from __future__ import annotations

import re

import structlog

from contract_lifecycle.mock_data.templates import CONTRACT_TEMPLATES

logger = structlog.get_logger(__name__)


def get_contract_template(contract_type: str) -> dict[str, str]:
    """Retrieve the clause template set for a given contract type.

    Args:
        contract_type: One of the supported contract type identifiers
            (e.g. ``"saas_agreement"``, ``"nda"``, ``"vendor_msa"``).

    Returns:
        A dictionary mapping clause names to their standard template text.
        Returns an empty dict for unknown contract types.
    """
    normalized = contract_type.lower().replace(" ", "_").replace("-", "_")
    templates = CONTRACT_TEMPLATES.get(normalized, {})

    if not templates:
        logger.warning("template_not_found", contract_type=contract_type)
    else:
        logger.debug(
            "template_loaded",
            contract_type=contract_type,
            clause_count=len(templates),
        )

    return dict(templates)


def merge_template(template: str, variables: dict[str, str]) -> str:
    """Merge variable placeholders into a template string.

    Replaces ``{{variable_name}}`` patterns with corresponding values
    from the *variables* dictionary.

    Args:
        template: The template string with ``{{placeholder}}`` markers.
        variables: A mapping of placeholder names to their values.

    Returns:
        The merged string with all recognized placeholders replaced.
    """
    result = template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))

    # Warn about unreplaced placeholders
    remaining = re.findall(r"\{\{(\w+)\}\}", result)
    if remaining:
        logger.warning("unresolved_placeholders", placeholders=remaining)

    return result


def get_standard_clauses(contract_type: str) -> list[str]:
    """Return a list of standard clause names for a contract type.

    Useful for checking whether a contract is missing any expected
    clauses.

    Args:
        contract_type: The contract type identifier.

    Returns:
        A list of clause name strings (e.g. ``["limitation_of_liability",
        "termination", ...]``).
    """
    templates = get_contract_template(contract_type)
    return list(templates.keys())


def get_safe_clause_text(contract_type: str, clause_name: str) -> str | None:
    """Retrieve the safe/standard version of a specific clause.

    Used by the negotiation strategist to propose alternative language.

    Args:
        contract_type: The contract type identifier.
        clause_name: The clause category (e.g. ``"limitation_of_liability"``).

    Returns:
        The safe clause text, or ``None`` if not found.
    """
    normalized_clause = clause_name.lower().replace(" ", "_").replace("-", "_")
    templates = get_contract_template(contract_type)
    return templates.get(normalized_clause)
