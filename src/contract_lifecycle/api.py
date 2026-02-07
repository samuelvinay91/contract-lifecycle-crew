"""FastAPI application for the Contract Lifecycle Crew.

Exposes REST endpoints for:
- Contract submission and lifecycle management
- SSE streaming of contract processing events
- Approval workflow (approve, reject, renegotiate)
- Contract execution
- Report generation
- Template browsing
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from common import ErrorResponse, HealthResponse

from contract_lifecycle.config import Settings
from contract_lifecycle.flow.lifecycle_flow import ContractLifecycleFlow
from contract_lifecycle.mock_data.contracts import MOCK_CONTRACTS
from contract_lifecycle.mock_data.templates import CONTRACT_TEMPLATES
from contract_lifecycle.models import (
    ApprovalDecision,
    ApprovalLevel,
    ContractSession,
    ContractType,
    LifecycleStage,
    RiskLevel,
)
from contract_lifecycle.streaming import (
    EVENT_APPROVED,
    EVENT_REJECTED,
    ContractEventStream,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ContractSubmitRequest(BaseModel):
    """Request body for contract submission."""

    contract_text: str = Field(
        ..., min_length=50, description="Full text of the contract to analyze."
    )
    contract_type: str | None = Field(
        None, description="Optional contract type hint (auto-detected if omitted)."
    )


class ApproveRequest(BaseModel):
    """Request body for contract approval at a specific level."""

    approver: str = Field(
        default="", description="Name of the approver."
    )
    comments: str = Field(
        default="", description="Optional approval comments."
    )


class RejectRequest(BaseModel):
    """Request body for contract rejection."""

    approver: str = Field(
        default="", description="Name of the approver."
    )
    comments: str = Field(
        ..., min_length=1, description="Reason for rejection."
    )


class RenegotiateRequest(BaseModel):
    """Request body for counter-terms submission."""

    counter_terms: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of clause IDs to proposed counter-terms.",
    )
    comments: str = Field(
        default="", description="Additional negotiation notes."
    )


# ---------------------------------------------------------------------------
# Session manager (in-memory)
# ---------------------------------------------------------------------------


class SessionManager:
    """In-memory contract session store."""

    def __init__(self) -> None:
        self._sessions: dict[str, ContractSession] = {}

    def create_session(self, contract_text: str) -> ContractSession:
        """Create a new contract session."""
        session_id = str(uuid.uuid4())
        session = ContractSession(
            id=session_id,
            state=LifecycleStage.INTAKE,
            contract_text=contract_text,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> ContractSession | None:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    def update_session(
        self, session_id: str, **kwargs: Any
    ) -> ContractSession | None:
        """Update session fields."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        session.updated_at = datetime.now(tz=timezone.utc)
        return session

    def list_sessions(self) -> list[ContractSession]:
        """Return all sessions."""
        return list(self._sessions.values())


# ---------------------------------------------------------------------------
# Application state container
# ---------------------------------------------------------------------------


class AppState:
    """Shared application state accessible from route handlers."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session_manager = SessionManager()
        self.event_stream = ContractEventStream()
        self.flow_tasks: dict[str, asyncio.Task[Any]] = {}


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or Settings()

    app = FastAPI(
        title="Contract Lifecycle Crew",
        description=(
            "End-to-end contract lifecycle management powered by CrewAI-style "
            "multi-agent orchestration. Handles contract analysis, clause "
            "extraction, risk assessment, negotiation strategy, and approval "
            "routing."
        ),
        version=settings.service_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared state
    state = AppState(settings)
    app.state.app_state = state
    app.state.settings = settings

    # -------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            service=settings.service_name,
            version=settings.service_version,
        )

    # -------------------------------------------------------------------
    # Contract submission
    # -------------------------------------------------------------------

    @app.post("/api/v1/contracts", tags=["contracts"])
    async def submit_contract(req: ContractSubmitRequest) -> dict[str, Any]:
        """Submit a contract for lifecycle processing.

        Creates a new session and kicks off the lifecycle flow
        asynchronously. Use the ``/stream`` endpoint to follow progress.
        """
        session = state.session_manager.create_session(req.contract_text)

        async def _run_flow() -> None:
            """Execute the lifecycle flow asynchronously."""
            flow = ContractLifecycleFlow()
            result = await flow.run(
                contract_text=req.contract_text,
                session_id=session.id,
                event_stream=state.event_stream,
                settings=settings,
            )

            # Persist results to session
            state.session_manager.update_session(
                session.id,
                state=result.stage,
                contract_type=(
                    result.analysis.contract_type if result.analysis else None
                ),
                analysis=result.analysis,
                risk_assessments=result.risks,
                negotiations=result.negotiations,
                approval_chain=result.approval_chain,
                versions=result.versions,
                overall_risk=result.overall_risk,
                error=result.error,
            )

        task = asyncio.create_task(_run_flow())
        state.flow_tasks[session.id] = task

        return {
            "session_id": session.id,
            "status": session.state.value,
            "message": "Contract submitted for lifecycle processing.",
            "stream_url": f"/api/v1/contracts/{session.id}/stream",
        }

    # -------------------------------------------------------------------
    # Contract retrieval
    # -------------------------------------------------------------------

    @app.get("/api/v1/contracts", tags=["contracts"])
    async def list_contracts() -> dict[str, Any]:
        """List all contract sessions."""
        sessions = state.session_manager.list_sessions()
        return {
            "contracts": [
                {
                    "id": s.id,
                    "state": s.state.value,
                    "contract_type": s.contract_type.value if s.contract_type else None,
                    "overall_risk": s.overall_risk.value if s.overall_risk else None,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in sessions
            ],
            "total": len(sessions),
        }

    @app.get("/api/v1/contracts/{contract_id}", tags=["contracts"])
    async def get_contract(contract_id: str) -> dict[str, Any]:
        """Get the current state of a contract session."""
        session = state.session_manager.get_session(contract_id)
        if session is None:
            raise HTTPException(
                status_code=404, detail=f"Contract session {contract_id} not found"
            )
        return session.model_dump()

    # -------------------------------------------------------------------
    # SSE streaming
    # -------------------------------------------------------------------

    @app.get("/api/v1/contracts/{contract_id}/stream", tags=["contracts"])
    async def stream_contract(contract_id: str) -> EventSourceResponse:
        """SSE stream of contract lifecycle events."""
        session = state.session_manager.get_session(contract_id)
        if session is None:
            raise HTTPException(
                status_code=404, detail=f"Contract session {contract_id} not found"
            )

        async def event_generator():  # type: ignore[no-untyped-def]
            async for event in state.event_stream.subscribe(contract_id):
                yield {
                    "event": event.event_type,
                    "data": json.dumps(event.model_dump(), default=str),
                }

        return EventSourceResponse(event_generator())

    # -------------------------------------------------------------------
    # Approval workflow
    # -------------------------------------------------------------------

    @app.post("/api/v1/contracts/{contract_id}/approve", tags=["approval"])
    async def approve_contract(
        contract_id: str, req: ApproveRequest
    ) -> dict[str, Any]:
        """Approve the contract at the current approval level.

        Advances the approval chain to the next level. When all levels
        have approved, the contract moves to APPROVED status.
        """
        session = state.session_manager.get_session(contract_id)
        if session is None:
            raise HTTPException(
                status_code=404, detail=f"Contract session {contract_id} not found"
            )

        if session.state != LifecycleStage.AWAITING_APPROVAL:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Contract is in state '{session.state.value}', "
                    f"not awaiting approval."
                ),
            )

        # Find the next pending approval
        pending_found = False
        all_approved = True
        for decision in session.approval_chain:
            if decision.decision == "pending":
                decision.decision = "approved"
                decision.approver = req.approver or decision.approver
                decision.comments = req.comments
                decision.timestamp = datetime.now(tz=timezone.utc)
                pending_found = True
                break

        if not pending_found:
            raise HTTPException(
                status_code=400, detail="No pending approvals found."
            )

        # Check if all approvals are complete
        all_approved = all(
            d.decision == "approved" for d in session.approval_chain
        )

        if all_approved:
            session.state = LifecycleStage.APPROVED
            await state.event_stream.emit(
                session_id=contract_id,
                event_type=EVENT_APPROVED,
                data={
                    "approval_chain": [
                        d.model_dump() for d in session.approval_chain
                    ]
                },
                message="All approvals received. Contract approved.",
            )
        else:
            # Find next pending level
            next_pending = next(
                (d for d in session.approval_chain if d.decision == "pending"),
                None,
            )
            next_level = next_pending.level.value if next_pending else "none"
            await state.event_stream.emit(
                session_id=contract_id,
                event_type="approval_progress",
                data={"next_level": next_level},
                message=f"Approval recorded. Next: {next_level}.",
            )

        session.updated_at = datetime.now(tz=timezone.utc)

        return {
            "session_id": contract_id,
            "status": session.state.value,
            "all_approved": all_approved,
            "approval_chain": [
                {
                    "level": d.level.value,
                    "decision": d.decision,
                    "approver": d.approver,
                }
                for d in session.approval_chain
            ],
        }

    @app.post("/api/v1/contracts/{contract_id}/reject", tags=["approval"])
    async def reject_contract(
        contract_id: str, req: RejectRequest
    ) -> dict[str, Any]:
        """Reject the contract with comments."""
        session = state.session_manager.get_session(contract_id)
        if session is None:
            raise HTTPException(
                status_code=404, detail=f"Contract session {contract_id} not found"
            )

        if session.state != LifecycleStage.AWAITING_APPROVAL:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Contract is in state '{session.state.value}', "
                    f"not awaiting approval."
                ),
            )

        session.state = LifecycleStage.REJECTED

        # Mark the next pending approval as rejected
        for decision in session.approval_chain:
            if decision.decision == "pending":
                decision.decision = "rejected"
                decision.approver = req.approver or decision.approver
                decision.comments = req.comments
                decision.timestamp = datetime.now(tz=timezone.utc)
                break

        session.updated_at = datetime.now(tz=timezone.utc)

        await state.event_stream.emit(
            session_id=contract_id,
            event_type=EVENT_REJECTED,
            data={
                "approver": req.approver,
                "comments": req.comments,
            },
            message=f"Contract rejected: {req.comments}",
        )

        return {
            "session_id": contract_id,
            "status": session.state.value,
            "message": f"Contract rejected by {req.approver or 'reviewer'}.",
            "comments": req.comments,
        }

    @app.post("/api/v1/contracts/{contract_id}/renegotiate", tags=["approval"])
    async def renegotiate_contract(
        contract_id: str, req: RenegotiateRequest
    ) -> dict[str, Any]:
        """Submit counter-terms for renegotiation."""
        session = state.session_manager.get_session(contract_id)
        if session is None:
            raise HTTPException(
                status_code=404, detail=f"Contract session {contract_id} not found"
            )

        if session.state not in (
            LifecycleStage.AWAITING_APPROVAL,
            LifecycleStage.REJECTED,
            LifecycleStage.NEGOTIATING,
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Contract is in state '{session.state.value}', "
                    f"cannot renegotiate."
                ),
            )

        session.state = LifecycleStage.RENEGOTIATING
        session.updated_at = datetime.now(tz=timezone.utc)

        # Record the renegotiation as a new version
        from contract_lifecycle.models import ContractVersion

        session.versions.append(
            ContractVersion(
                version=len(session.versions) + 1,
                changes=[
                    f"Counter-terms submitted for clause {cid}: {terms[:100]}"
                    for cid, terms in req.counter_terms.items()
                ] + ([f"Notes: {req.comments}"] if req.comments else []),
            )
        )

        # Reset approval chain to pending
        for decision in session.approval_chain:
            decision.decision = "pending"
            decision.comments = ""

        # Move back to awaiting approval
        session.state = LifecycleStage.AWAITING_APPROVAL

        await state.event_stream.emit(
            session_id=contract_id,
            event_type="renegotiating",
            data={
                "counter_terms": req.counter_terms,
                "version": len(session.versions),
            },
            message=(
                f"Counter-terms submitted. Version {len(session.versions)} "
                f"created. Approval chain reset."
            ),
        )

        return {
            "session_id": contract_id,
            "status": session.state.value,
            "version": len(session.versions),
            "message": "Counter-terms submitted. Approval chain reset for re-review.",
        }

    # -------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------

    @app.post("/api/v1/contracts/{contract_id}/execute", tags=["contracts"])
    async def execute_contract(contract_id: str) -> dict[str, Any]:
        """Mark the contract as executed after all approvals."""
        session = state.session_manager.get_session(contract_id)
        if session is None:
            raise HTTPException(
                status_code=404, detail=f"Contract session {contract_id} not found"
            )

        if session.state != LifecycleStage.APPROVED:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Contract must be in 'approved' state to execute. "
                    f"Current state: '{session.state.value}'."
                ),
            )

        session.state = LifecycleStage.EXECUTED
        session.updated_at = datetime.now(tz=timezone.utc)

        from contract_lifecycle.models import ContractVersion

        session.versions.append(
            ContractVersion(
                version=len(session.versions) + 1,
                changes=["Contract executed"],
            )
        )

        return {
            "session_id": contract_id,
            "status": session.state.value,
            "message": "Contract has been executed successfully.",
            "executed_at": session.updated_at.isoformat(),
        }

    # -------------------------------------------------------------------
    # Report
    # -------------------------------------------------------------------

    @app.get("/api/v1/contracts/{contract_id}/report", tags=["contracts"])
    async def get_contract_report(contract_id: str) -> dict[str, Any]:
        """Get a comprehensive contract lifecycle report."""
        session = state.session_manager.get_session(contract_id)
        if session is None:
            raise HTTPException(
                status_code=404, detail=f"Contract session {contract_id} not found"
            )

        report = {
            "session_id": session.id,
            "status": session.state.value,
            "contract_type": (
                session.contract_type.value if session.contract_type else None
            ),
            "overall_risk": (
                session.overall_risk.value if session.overall_risk else None
            ),
            "analysis": (
                session.analysis.model_dump() if session.analysis else None
            ),
            "risk_assessments": [r.model_dump() for r in session.risk_assessments],
            "risk_summary": {
                "total": len(session.risk_assessments),
                "low": sum(
                    1 for r in session.risk_assessments
                    if r.risk_level == RiskLevel.LOW
                ),
                "medium": sum(
                    1 for r in session.risk_assessments
                    if r.risk_level == RiskLevel.MEDIUM
                ),
                "high": sum(
                    1 for r in session.risk_assessments
                    if r.risk_level == RiskLevel.HIGH
                ),
                "critical": sum(
                    1 for r in session.risk_assessments
                    if r.risk_level == RiskLevel.CRITICAL
                ),
            },
            "negotiations": [n.model_dump() for n in session.negotiations],
            "approval_chain": [a.model_dump() for a in session.approval_chain],
            "versions": [v.model_dump() for v in session.versions],
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "error": session.error,
        }

        return report

    # -------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------

    @app.get("/api/v1/templates", tags=["templates"])
    async def list_templates() -> dict[str, Any]:
        """List available contract templates and their clause categories."""
        templates_info = {}
        for contract_type, clauses in CONTRACT_TEMPLATES.items():
            templates_info[contract_type] = {
                "clause_count": len(clauses),
                "clauses": list(clauses.keys()),
            }

        return {
            "templates": templates_info,
            "total": len(templates_info),
            "mock_contracts": list(MOCK_CONTRACTS.keys()),
        }

    # -------------------------------------------------------------------
    # Error handlers
    # -------------------------------------------------------------------

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all error handler."""
        logger.error(
            "unhandled_exception", error=str(exc), path=request.url.path
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc),
                status_code=500,
            ).model_dump(),
        )

    return app
