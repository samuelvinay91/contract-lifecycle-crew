"""Contract Lifecycle Flow - event-driven orchestration.

Implements CrewAI's Flow pattern with ``@start``, ``@listen``, and
``@router`` decorators (simulated as method dispatch) to coordinate
the full contract lifecycle: intake -> analysis -> risk routing ->
negotiation/approval -> execution.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import structlog

from contract_lifecycle.config import Settings
from contract_lifecycle.crews.analysis_crew import AnalysisCrew
from contract_lifecycle.crews.approval_crew import ApprovalCrew
from contract_lifecycle.crews.negotiation_crew import NegotiationCrew
from contract_lifecycle.flow.conditions import (
    approval_threshold,
    risk_level_check,
)
from contract_lifecycle.flow.state import ContractFlowState
from contract_lifecycle.models import (
    ApprovalDecision,
    ApprovalLevel,
    ContractVersion,
    LifecycleStage,
    RiskLevel,
)
from contract_lifecycle.streaming import (
    EVENT_ANALYSIS_COMPLETE,
    EVENT_ANALYZING,
    EVENT_APPROVED,
    EVENT_AWAITING_APPROVAL,
    EVENT_CLAUSES_EXTRACTED,
    EVENT_COMPLETED,
    EVENT_ERROR,
    EVENT_EXECUTED,
    EVENT_EXTRACTING_CLAUSES,
    EVENT_INTAKE,
    EVENT_NEGOTIATING,
    EVENT_NEGOTIATION_STRATEGY_READY,
    EVENT_REJECTED,
    EVENT_RISK_ASSESSING,
    EVENT_RISK_ASSESSMENT_DONE,
    EVENT_ROUTING_APPROVAL,
    ContractEventStream,
)
from contract_lifecycle.tools.risk_tools import calculate_risk_matrix

logger = structlog.get_logger(__name__)


class ContractLifecycleFlow:
    """Event-driven orchestration for the contract lifecycle.

    Simulates CrewAI's Flow pattern with method-based step dispatch.
    Each step transitions the state, emits SSE events, and delegates
    work to the appropriate Crew.

    Flow graph::

        intake -> analyze -> assess_risk -> [router]
                                               |
                    +-----------+--------------+----------+
                    |           |                         |
              auto_approve  standard_review        full_negotiation
                    |           |                         |
                    v           v                         v
                 execute   single_approval          negotiate
                              |                         |
                              v                    multi_level_approval
                           execute                      |
                                                        v
                                                     execute
    """

    def __init__(self) -> None:
        self._analysis_crew = AnalysisCrew()
        self._negotiation_crew: NegotiationCrew | None = None
        self._approval_crew = ApprovalCrew()

    async def run(
        self,
        contract_text: str,
        session_id: str,
        event_stream: ContractEventStream,
        settings: Settings,
    ) -> ContractFlowState:
        """Run the complete contract lifecycle flow.

        This is the main entry point. It drives the state machine
        through all stages, emitting events along the way.

        Args:
            contract_text: The raw contract text to process.
            session_id: The unique session identifier.
            event_stream: The SSE event stream for real-time updates.
            settings: Application settings.

        Returns:
            The final :class:`ContractFlowState` after all stages.
        """
        state = ContractFlowState(
            session_id=session_id,
            contract_text=contract_text,
        )

        try:
            # @start: intake
            state = await self._intake(state, event_stream)

            # @listen(intake): analyze
            state = await self._analyze(state, event_stream)

            # @listen(analyze): assess_risk
            state = await self._assess_risk(state, event_stream)

            # @router(assess_risk): risk_routing
            route = risk_level_check(state.overall_risk or RiskLevel.LOW)

            if route == "auto_approve":
                # @listen(risk_routing, "auto_approve")
                can_auto = approval_threshold(
                    state.overall_risk or RiskLevel.LOW,
                    settings.auto_approve_threshold,
                )
                if can_auto:
                    state = await self._auto_approve(state, event_stream)
                else:
                    state = await self._standard_review(state, event_stream, settings)

            elif route == "standard_review":
                # @listen(risk_routing, "standard_review")
                state = await self._standard_review(state, event_stream, settings)

            else:
                # @listen(risk_routing, "full_negotiation")
                state = await self._negotiate(state, event_stream, settings)
                state = await self._multi_level_approval(state, event_stream, settings)

            # @listen(approved): execute
            if state.stage in (LifecycleStage.APPROVED, LifecycleStage.AWAITING_APPROVAL):
                state = await self._execute(state, event_stream)

            # Emit completion
            await event_stream.emit(
                session_id=session_id,
                event_type=EVENT_COMPLETED,
                data=state.to_dict(),
                message="Contract lifecycle processing complete.",
            )

        except Exception as exc:
            logger.error("flow_error", error=str(exc), session_id=session_id)
            state.error = str(exc)
            state.stage = LifecycleStage.FAILED
            await event_stream.emit(
                session_id=session_id,
                event_type=EVENT_ERROR,
                data={"error": str(exc)},
                message=f"Flow error: {exc}",
            )

        return state

    # ------------------------------------------------------------------
    # Flow steps
    # ------------------------------------------------------------------

    async def _intake(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
    ) -> ContractFlowState:
        """@start - Validate and store the contract for processing."""
        logger.info("flow_step", step="intake", session_id=state.session_id)

        state.stage = LifecycleStage.INTAKE
        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_INTAKE,
            data={"text_length": len(state.contract_text)},
            message="Contract received. Starting lifecycle processing.",
        )

        # Basic validation
        if not state.contract_text or len(state.contract_text.strip()) < 50:
            raise ValueError(
                "Contract text is too short. Minimum 50 characters required."
            )

        # Create initial version
        state.versions.append(
            ContractVersion(
                version=1,
                changes=["Initial contract submission"],
            )
        )

        # Small delay to simulate processing
        await asyncio.sleep(0.1)
        return state

    async def _analyze(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
    ) -> ContractFlowState:
        """@listen(intake) - Run the AnalysisCrew on the contract."""
        logger.info("flow_step", step="analyze", session_id=state.session_id)

        state.stage = LifecycleStage.ANALYZING
        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_ANALYZING,
            message="Analysis crew started. Legal analyst is reviewing the contract.",
        )

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_EXTRACTING_CLAUSES,
            message="Extracting clauses and key terms from contract text.",
        )

        # Run the analysis crew
        result = await self._analysis_crew.kickoff(state.contract_text)

        state.analysis = result["analysis"]
        state.risks = result["all_risks"]

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_CLAUSES_EXTRACTED,
            data={
                "clause_count": len(state.analysis.clauses),
                "contract_type": state.analysis.contract_type.value,
                "parties": state.analysis.parties,
            },
            message=(
                f"Extracted {len(state.analysis.clauses)} clauses. "
                f"Contract type: {state.analysis.contract_type.value}."
            ),
        )

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_ANALYSIS_COMPLETE,
            data={
                "summary": state.analysis.summary,
                "total_value": state.analysis.total_value,
                "risk_assessments": len(result["risk_assessments"]),
                "compliance_issues": len(result["compliance_issues"]),
            },
            message="Contract analysis complete.",
        )

        return state

    async def _assess_risk(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
    ) -> ContractFlowState:
        """@listen(analyze) - Calculate overall risk from assessments."""
        logger.info("flow_step", step="assess_risk", session_id=state.session_id)

        state.stage = LifecycleStage.RISK_ASSESSING
        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_RISK_ASSESSING,
            data={"assessment_count": len(state.risks)},
            message="Calculating overall risk from clause assessments.",
        )

        # Calculate aggregate risk
        state.overall_risk = calculate_risk_matrix(state.risks)

        risk_breakdown = {
            "low": sum(1 for r in state.risks if r.risk_level == RiskLevel.LOW),
            "medium": sum(1 for r in state.risks if r.risk_level == RiskLevel.MEDIUM),
            "high": sum(1 for r in state.risks if r.risk_level == RiskLevel.HIGH),
            "critical": sum(1 for r in state.risks if r.risk_level == RiskLevel.CRITICAL),
        }

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_RISK_ASSESSMENT_DONE,
            data={
                "overall_risk": state.overall_risk.value,
                "breakdown": risk_breakdown,
            },
            message=(
                f"Overall risk: {state.overall_risk.value.upper()}. "
                f"Breakdown: {risk_breakdown}."
            ),
        )

        await asyncio.sleep(0.1)
        return state

    async def _auto_approve(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
    ) -> ContractFlowState:
        """@listen(risk_routing, 'auto_approve') - Auto-approve low-risk contracts."""
        logger.info("flow_step", step="auto_approve", session_id=state.session_id)

        state.stage = LifecycleStage.APPROVED
        state.approval_chain = [
            ApprovalDecision(
                level=ApprovalLevel.AUTO,
                approver="System (Auto-Approval)",
                decision="approved",
                comments=(
                    f"Contract auto-approved. Overall risk: "
                    f"{state.overall_risk.value if state.overall_risk else 'low'}. "
                    f"Risk level meets auto-approval threshold."
                ),
            )
        ]

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_APPROVED,
            data={
                "approval_level": "auto",
                "approver": "System (Auto-Approval)",
            },
            message="Contract auto-approved. Low risk level meets threshold.",
        )

        return state

    async def _standard_review(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
        settings: Settings,
    ) -> ContractFlowState:
        """@listen(risk_routing, 'standard_review') - Simplified manager approval."""
        logger.info("flow_step", step="standard_review", session_id=state.session_id)

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_ROUTING_APPROVAL,
            data={"route": "standard_review"},
            message="Routing to standard review (manager approval).",
        )

        # Run approval crew to determine chain
        contract_value = state.analysis.total_value if state.analysis else 0.0
        contract_type = (
            state.analysis.contract_type if state.analysis
            else __import__("contract_lifecycle.models", fromlist=["ContractType"]).ContractType.CONSULTING
        )

        approval_result = await self._approval_crew.kickoff(
            risk_level=state.overall_risk or RiskLevel.MEDIUM,
            contract_value=contract_value,
            contract_type=contract_type,
        )

        state.approval_chain = approval_result["approval_decisions"]
        state.stage = LifecycleStage.AWAITING_APPROVAL

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_AWAITING_APPROVAL,
            data={
                "approval_chain": [
                    {"level": d.level.value, "approver": d.approver}
                    for d in state.approval_chain
                ],
                "validation_notes": approval_result["validation_notes"],
            },
            message=(
                f"Awaiting approval from {len(state.approval_chain)} "
                f"level(s): {', '.join(d.level.value for d in state.approval_chain)}."
            ),
        )

        return state

    async def _negotiate(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
        settings: Settings,
    ) -> ContractFlowState:
        """@listen(risk_routing, 'full_negotiation') - Run NegotiationCrew."""
        logger.info("flow_step", step="negotiate", session_id=state.session_id)

        state.stage = LifecycleStage.NEGOTIATING
        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_NEGOTIATING,
            data={
                "high_risk_clauses": sum(
                    1 for r in state.risks
                    if r.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
                ),
            },
            message="Negotiation crew started. Developing counter-proposals for high-risk clauses.",
        )

        # Initialize negotiation crew with contract type
        contract_type_str = (
            state.analysis.contract_type.value if state.analysis
            else "saas_agreement"
        )
        self._negotiation_crew = NegotiationCrew(contract_type=contract_type_str)

        clauses = state.analysis.clauses if state.analysis else []
        positions = await self._negotiation_crew.kickoff(
            risks=state.risks,
            clauses=clauses,
        )
        state.negotiations = positions

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_NEGOTIATION_STRATEGY_READY,
            data={
                "positions_count": len(positions),
                "positions": [
                    {
                        "clause_id": p.clause_id,
                        "rationale": p.rationale[:200],
                        "leverage_points": len(p.leverage_points),
                    }
                    for p in positions
                ],
            },
            message=f"Negotiation strategy ready. {len(positions)} counter-proposals developed.",
        )

        # Record version
        state.versions.append(
            ContractVersion(
                version=len(state.versions) + 1,
                changes=[
                    f"Negotiation position developed for clause {p.clause_id}"
                    for p in positions
                ],
            )
        )

        return state

    async def _multi_level_approval(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
        settings: Settings,
    ) -> ContractFlowState:
        """@listen(negotiate) - Run ApprovalCrew and set up multi-level approval."""
        logger.info(
            "flow_step", step="multi_level_approval", session_id=state.session_id
        )

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_ROUTING_APPROVAL,
            data={"route": "multi_level"},
            message="Routing through multi-level approval chain.",
        )

        # Run approval crew
        contract_value = state.analysis.total_value if state.analysis else 0.0
        contract_type = (
            state.analysis.contract_type if state.analysis
            else __import__("contract_lifecycle.models", fromlist=["ContractType"]).ContractType.CONSULTING
        )

        approval_result = await self._approval_crew.kickoff(
            risk_level=state.overall_risk or RiskLevel.HIGH,
            contract_value=contract_value,
            contract_type=contract_type,
        )

        state.approval_chain = approval_result["approval_decisions"]
        state.current_approval_index = 0
        state.stage = LifecycleStage.AWAITING_APPROVAL

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_AWAITING_APPROVAL,
            data={
                "approval_chain": [
                    {"level": d.level.value, "approver": d.approver}
                    for d in state.approval_chain
                ],
                "negotiation_positions": len(state.negotiations),
                "validation_notes": approval_result["validation_notes"],
            },
            message=(
                f"Contract requires {len(state.approval_chain)}-level approval: "
                f"{', '.join(d.level.value for d in state.approval_chain)}. "
                f"Awaiting human decisions."
            ),
        )

        return state

    async def _execute(
        self,
        state: ContractFlowState,
        event_stream: ContractEventStream,
    ) -> ContractFlowState:
        """@listen(approved) - Mark contract as executed."""
        logger.info("flow_step", step="execute", session_id=state.session_id)

        state.stage = LifecycleStage.EXECUTED

        # Record final version
        state.versions.append(
            ContractVersion(
                version=len(state.versions) + 1,
                changes=["Contract executed after all approvals received"],
            )
        )

        await event_stream.emit(
            session_id=state.session_id,
            event_type=EVENT_EXECUTED,
            data={
                "versions": len(state.versions),
                "approval_levels": [d.level.value for d in state.approval_chain],
            },
            message="Contract has been executed successfully.",
        )

        return state
