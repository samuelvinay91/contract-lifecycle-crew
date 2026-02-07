# Contract Lifecycle Crew

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg?logo=docker)](Dockerfile)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![CI](https://github.com/samuelvinay91/contract-lifecycle-crew/actions/workflows/ci.yml/badge.svg)](https://github.com/samuelvinay91/contract-lifecycle-crew/actions)

End-to-end contract lifecycle management powered by **CrewAI** patterns. Role-specialized AI agents handle contract analysis, clause extraction, risk assessment, negotiation strategy, and approval routing through hierarchical Crews and event-driven Flows.

---

## What This Demonstrates

| Concept | Implementation |
|---------|---------------|
| **CrewAI** | Agent(role, goal, backstory), Task, Crew, Flow patterns |
| **Role-Based Agents** | 5 specialized agents with distinct legal/business personas |
| **Hierarchical Process** | Senior Legal Analyst supervises Risk Assessor + Compliance Officer |
| **Sequential Process** | Negotiation and approval crews run tasks in order |
| **Flow Orchestration** | Full lifecycle: Intake → Analyze → Risk Route → Negotiate → Approve → Execute |
| **Conditional Routing** | Low risk → auto-approve, Medium → standard review, High → full negotiation |
| **Enterprise Domain** | Legal/procurement contract management with realistic mock data |

---

## Architecture

```
                      Contract Lifecycle Flow
                      =======================

  [Intake] ─── validate + store contract
      |
      ▼
  Analysis Crew (hierarchical)
  ┌──────────────────────────────────────────┐
  │  Manager: [Legal Analyst]                │
  │  Workers: [Risk Assessor] [Compliance]   │
  │  Tasks: extract clauses → assess risk    │
  └──────────────────────────────────────────┘
      |
      ▼
  [Risk Router] ── conditional branching
      |
  ┌───┼───────────┐
  ▼   ▼           ▼
 LOW  MEDIUM    HIGH/CRITICAL
  |     |           |
  ▼     ▼           ▼
[Auto  [Standard  Negotiation Crew (sequential)
Approve] Review]  ┌─────────────────────────┐
  |     |        │ [Negotiation Strategist] │
  |     |        │ [Legal Analyst review]   │
  |     |        └─────────────────────────┘
  |     |              |
  |     ▼              ▼
  |  [Manager      [Multi-Level Approval]
  |   Approval]    (VP → Legal → CFO)
  |     |              |
  └─────┴──────────────┘
           |
           ▼
      [Execute Contract]
```

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/samuelvinay91/contract-lifecycle-crew.git
cd contract-lifecycle-crew

docker build -t contract-lifecycle-crew .
docker run -p 8014:8000 --env-file .env contract-lifecycle-crew
```

The API will be available at **http://localhost:8014**. Docs at **http://localhost:8014/docs**.

### Option 2: Local Development

```bash
git clone https://github.com/samuelvinay91/contract-lifecycle-crew.git
cd contract-lifecycle-crew

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
python -m contract_lifecycle.main
```

### Option 3: uv (Fast)

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
python -m contract_lifecycle.main
```

> **No API keys required!** Regex-based clause extraction and rule-based risk assessment work out of the box.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/contracts` | Submit a contract for analysis |
| GET | `/api/v1/contracts/{id}` | Get contract session status |
| GET | `/api/v1/contracts/{id}/stream` | SSE stream of lifecycle progress |
| POST | `/api/v1/contracts/{id}/approve` | Approve at current level |
| POST | `/api/v1/contracts/{id}/reject` | Reject with comments |
| POST | `/api/v1/contracts/{id}/renegotiate` | Submit counter-terms |
| POST | `/api/v1/contracts/{id}/execute` | Mark contract as executed |
| GET | `/api/v1/contracts/{id}/report` | Download full analysis report |
| GET | `/api/v1/templates` | List contract templates |
| GET | `/api/v1/contracts` | List all contracts |
| GET | `/health` | Health check |

---

## Example Usage

```bash
# Submit a contract
curl -X POST http://localhost:8014/api/v1/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "contract_text": "MASTER SERVICES AGREEMENT\n\nThis Agreement is between TechCorp and CloudVendor...\n\n1. TERM\nThis Agreement shall continue for 36 months with auto-renewal..."
  }'

# Stream lifecycle progress
curl http://localhost:8014/api/v1/contracts/{session_id}/stream

# Approve contract
curl -X POST http://localhost:8014/api/v1/contracts/{session_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver": "vp@techcorp.com", "comments": "Approved"}'
```

---

## Agents (CrewAI Roles)

| Agent | Role | Backstory |
|-------|------|-----------|
| **Legal Analyst** | Senior Legal Analyst | 15 years corporate law, technology agreements specialist |
| **Risk Assessor** | Risk Assessment Specialist | Former Big Four consultant, enterprise risk management |
| **Compliance Officer** | Compliance Officer | Regulatory compliance expert (GDPR, SOX, industry-specific) |
| **Negotiation Strategist** | Negotiation Strategist | Game theory background, contract optimization expert |
| **Approval Router** | Approval Workflow Manager | Enterprise governance and workflow automation specialist |

---

## Risk-Based Routing

| Risk Level | Approval Path | Contract Examples |
|-----------|---------------|-------------------|
| **LOW** | Auto-approve | Standard NDAs, low-value renewals |
| **MEDIUM** | Manager approval | Standard SaaS agreements, consulting contracts |
| **HIGH** | Manager → VP → Legal | Large vendor MSAs, employment agreements with non-competes |
| **CRITICAL** | Manager → VP → Legal → CFO | Unlimited liability, broad indemnification, IP transfers |

---

## Mock Contracts

The project includes 4 realistic sample contracts for immediate testing:

1. **SaaS Agreement** - with risky auto-renewal and unlimited liability clauses
2. **NDA** - with aggressive non-compete and broad confidentiality definitions
3. **Vendor MSA** - with favorable SLA but weak termination rights
4. **Employment Agreement** - standard terms, low risk

---

## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=src/contract_lifecycle
pytest tests/ -v -m "not slow and not integration"
```

---

## Project Structure

```
contract-lifecycle-crew/
├── src/contract_lifecycle/
│   ├── agents/           # CrewAI-pattern role-based agents
│   ├── crews/            # Analysis, Negotiation, Approval crews
│   ├── flow/             # Lifecycle Flow orchestration
│   ├── tools/            # Clause extraction, risk calc, templates
│   ├── mock_data/        # Contracts, templates, precedents
│   ├── api.py            # FastAPI application
│   ├── config.py         # Settings
│   ├── models.py         # Pydantic domain models
│   ├── streaming.py      # SSE event stream
│   └── main.py           # Entry point
├── tests/
├── k8s/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
