"""Pydantic models for the Contract Lifecycle Crew.

Defines all domain objects used across agents, crews, flows, and API
endpoints: contract types, risk levels, lifecycle stages, clauses, risk
assessments, negotiation positions, approval decisions, and session state.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ContractType(str, Enum):
    """Supported contract categories."""

    NDA = "nda"
    SAAS_AGREEMENT = "saas_agreement"
    VENDOR_MSA = "vendor_msa"
    EMPLOYMENT = "employment"
    CONSULTING = "consulting"
    LICENSING = "licensing"


class RiskLevel(str, Enum):
    """Risk severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LifecycleStage(str, Enum):
    """Stages in the contract lifecycle flow."""

    INTAKE = "intake"
    ANALYZING = "analyzing"
    RISK_ASSESSING = "risk_assessing"
    NEGOTIATING = "negotiating"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RENEGOTIATING = "renegotiating"
    EXECUTED = "executed"
    FAILED = "failed"


class ApprovalLevel(str, Enum):
    """Approval authority levels (ascending seniority)."""

    AUTO = "auto"
    MANAGER = "manager"
    VP = "vp"
    LEGAL = "legal"
    CFO = "cfo"


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class Clause(BaseModel):
    """A single clause extracted from a contract."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    text: str
    section: str = ""
    is_standard: bool = True
    risk_flags: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Risk evaluation of a specific clause."""

    clause_id: str
    risk_level: RiskLevel
    description: str
    recommendation: str
    precedent_reference: str | None = None


class NegotiationPosition(BaseModel):
    """Negotiation strategy for a flagged clause."""

    clause_id: str
    current_terms: str
    proposed_terms: str
    rationale: str
    leverage_points: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    """Decision made at a single approval level."""

    level: ApprovalLevel
    approver: str
    decision: str = "pending"  # pending | approved | rejected
    comments: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ContractAnalysis(BaseModel):
    """Full analysis output produced by the legal analyst."""

    contract_type: ContractType
    parties: list[str] = Field(default_factory=list)
    effective_date: str = ""
    expiration_date: str = ""
    total_value: float = 0.0
    clauses: list[Clause] = Field(default_factory=list)
    summary: str = ""


class ContractVersion(BaseModel):
    """Snapshot of a contract revision."""

    version: int
    changes: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ContractSession(BaseModel):
    """Top-level session tracking the full lifecycle of a contract."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: LifecycleStage = LifecycleStage.INTAKE
    contract_text: str = ""
    contract_type: ContractType | None = None
    analysis: ContractAnalysis | None = None
    risk_assessments: list[RiskAssessment] = Field(default_factory=list)
    negotiations: list[NegotiationPosition] = Field(default_factory=list)
    approval_chain: list[ApprovalDecision] = Field(default_factory=list)
    versions: list[ContractVersion] = Field(default_factory=list)
    overall_risk: RiskLevel | None = None
    report: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    error: str | None = None


class ContractEvent(BaseModel):
    """SSE event emitted during contract lifecycle processing."""

    event_type: str
    session_id: str
    data: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
