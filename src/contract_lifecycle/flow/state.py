"""Flow state dataclass for the contract lifecycle pipeline.

Holds the mutable state that flows through each stage of the
contract lifecycle, from intake through execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from contract_lifecycle.models import (
    ApprovalDecision,
    ContractAnalysis,
    ContractVersion,
    LifecycleStage,
    NegotiationPosition,
    RiskAssessment,
    RiskLevel,
)


@dataclass
class ContractFlowState:
    """Mutable state passed through the contract lifecycle flow.

    Each flow step reads from and writes to this state object, which
    tracks the contract through all lifecycle stages.
    """

    # Session identity
    session_id: str = ""

    # Contract data
    contract_text: str = ""
    stage: LifecycleStage = LifecycleStage.INTAKE

    # Analysis results
    analysis: ContractAnalysis | None = None
    risks: list[RiskAssessment] = field(default_factory=list)

    # Negotiation results
    negotiations: list[NegotiationPosition] = field(default_factory=list)

    # Approval workflow
    approval_chain: list[ApprovalDecision] = field(default_factory=list)
    current_approval_index: int = 0

    # Aggregate risk
    overall_risk: RiskLevel | None = None

    # Version history
    versions: list[ContractVersion] = field(default_factory=list)

    # Error tracking
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the flow state to a dictionary.

        Returns:
            A JSON-serializable dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "contract_text_length": len(self.contract_text),
            "stage": self.stage.value,
            "analysis": self.analysis.model_dump() if self.analysis else None,
            "risks": [r.model_dump() for r in self.risks],
            "negotiations": [n.model_dump() for n in self.negotiations],
            "approval_chain": [a.model_dump() for a in self.approval_chain],
            "current_approval_index": self.current_approval_index,
            "overall_risk": self.overall_risk.value if self.overall_risk else None,
            "versions": [v.model_dump() for v in self.versions],
            "error": self.error,
        }
