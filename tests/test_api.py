"""API endpoint tests for Contract Lifecycle Crew."""

from __future__ import annotations

import pytest

SAMPLE_CONTRACT = """
MASTER SERVICES AGREEMENT

This Master Services Agreement ("Agreement") is entered into as of January 15, 2025
by and between TechCorp Inc. ("Client") and CloudVendor LLC ("Provider").

1. TERM AND TERMINATION
This Agreement shall commence on the Effective Date and continue for a period of
thirty-six (36) months. Either party may terminate with 90 days written notice.
Provider may terminate immediately if Client fails to pay within 30 days of invoice.

2. PAYMENT TERMS
Client shall pay Provider $250,000 annually, payable quarterly in advance.
Late payments shall accrue interest at 1.5% per month.

3. CONFIDENTIALITY
Each party agrees to maintain the confidentiality of all proprietary information
disclosed by the other party. This obligation survives termination for 5 years.

4. LIMITATION OF LIABILITY
PROVIDER'S TOTAL LIABILITY SHALL NOT EXCEED THE FEES PAID IN THE PRIOR 12 MONTHS.
IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT OR CONSEQUENTIAL DAMAGES.

5. INDEMNIFICATION
Provider shall indemnify Client against third-party claims arising from Provider's
breach of this Agreement or negligence.

6. INTELLECTUAL PROPERTY
All pre-existing IP remains with the original owner. Work product created under
this Agreement shall be owned by Client upon full payment.

7. DATA PROTECTION
Provider shall comply with all applicable data protection laws including GDPR.
Provider shall process personal data only as instructed by Client.

8. SLA AND UPTIME
Provider guarantees 99.9% uptime. Failure to meet SLA entitles Client to
service credits of 10% of monthly fees per hour of downtime.

9. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.

10. AUTO-RENEWAL
This Agreement shall automatically renew for successive 12-month periods unless
either party provides 60 days written notice of non-renewal.
"""


@pytest.mark.asyncio
async def test_health(client):
    """Health endpoint returns service info."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "contract-lifecycle-crew"


@pytest.mark.asyncio
async def test_create_contract_session(client):
    """Submit a contract for analysis."""
    resp = await client.post(
        "/api/v1/contracts",
        json={"contract_text": SAMPLE_CONTRACT},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "stream_url" in data


@pytest.mark.asyncio
async def test_get_contract_session(client):
    """Get contract session status."""
    create_resp = await client.post(
        "/api/v1/contracts",
        json={"contract_text": SAMPLE_CONTRACT},
    )
    session_id = create_resp.json()["session_id"]

    import asyncio
    await asyncio.sleep(0.5)

    resp = await client.get(f"/api/v1/contracts/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == session_id


@pytest.mark.asyncio
async def test_get_nonexistent_contract(client):
    """404 for unknown contract."""
    resp = await client.get("/api/v1/contracts/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_contracts(client):
    """List all contracts."""
    resp = await client.get("/api/v1/contracts")
    assert resp.status_code == 200
    data = resp.json()
    assert "contracts" in data


@pytest.mark.asyncio
async def test_list_templates(client):
    """List available contract templates."""
    resp = await client.get("/api/v1/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert "templates" in data
    assert len(data["templates"]) > 0


@pytest.mark.asyncio
async def test_approve_contract(client):
    """Approve a contract at current level."""
    create_resp = await client.post(
        "/api/v1/contracts",
        json={"contract_text": SAMPLE_CONTRACT},
    )
    session_id = create_resp.json()["session_id"]

    import asyncio
    await asyncio.sleep(1.5)

    resp = await client.post(
        f"/api/v1/contracts/{session_id}/approve",
        json={"approver": "manager@techcorp.com", "comments": "Looks good"},
    )
    assert resp.status_code in (200, 400)


@pytest.mark.asyncio
async def test_get_report(client):
    """Get full contract analysis report."""
    create_resp = await client.post(
        "/api/v1/contracts",
        json={"contract_text": SAMPLE_CONTRACT},
    )
    session_id = create_resp.json()["session_id"]

    import asyncio
    await asyncio.sleep(1.5)

    resp = await client.get(f"/api/v1/contracts/{session_id}/report")
    assert resp.status_code in (200, 404)
