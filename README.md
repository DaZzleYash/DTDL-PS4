# Finance Decision Engine

**PS4 — Configurable Decision Automation Platform**  
Deutsche Telekom Digital Labs · The Talent Hack (Build Sprint)

A modular decision automation platform built with Python 3.12 and FastAPI. Structured JSON requests are evaluated against **configurable rules** stored in a database, and the service returns an explainable decision with a full audit trace.

Finance (loan/credit) is the reference demo domain under `app/finance/`. The core engine is domain-agnostic.

---

## What Is Active

All five modules are integrated on `main`:

| Layer | Module | API / Entry | Status |
|---|---|---|---|
| Platform | `app/core/` | config, DB, logging, errors | Active |
| Engine | `app/engine/` | condition JSON interpreter | Active |
| Rules | `app/rules/` | `GET/POST/PUT/PATCH/DELETE /api/rules` | Active |
| Decisions | `app/decisions/` | `POST /api/decisions/evaluate`, `/evaluate/bulk` | Active |
| Finance demo | `app/finance/` | `python -m app.finance.seed_rules` | Active |
| Health | `app/main.py` | `GET /health` | Active |
| Docs | FastAPI | `GET /docs`, `GET /redoc` | Active |

### Seeded finance rules (5)

| Rule | Outcome | Priority |
|---|---|---|
| Minimum Credit Score | APPROVE | 10 |
| High Debt-to-Income Flag | MANUAL_REVIEW | 20 |
| VIP Existing Customer Fast Track | APPROVE | 25 |
| Prior Default Block | REJECT | 30 |
| Underage Applicant Block | REJECT | 40 |

See `app/finance/rule_catalog.md` for plain-English descriptions.

---

## Prerequisites

- **Python 3.12+** (required — 3.9 will fail on dependencies)
- `pip`
- Git

Docker is optional (documented below for later; local SQLite is the default path).

---

## Local Setup (Windows)

Run these from the repo root (`D:\DTDL-PS4`):

### 1. Clone and create virtual environment

```powershell
git clone https://github.com/DaZzleYash/DTDL-PS4.git
cd DTDL-PS4
git pull origin main

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure environment

```powershell
copy .env.example .env
mkdir data -Force
```

Default `.env` uses SQLite — no Postgres needed locally:

```
DATABASE_URL=sqlite:///./data/decisions.db
LOG_LEVEL=INFO
APP_ENV=local
```

### 3. Apply database migrations

Creates the `rules` table:

```powershell
alembic upgrade head
```

### 4. Seed finance demo rules

```powershell
python -m app.finance.seed_rules
```

Expected output:

```
Seeded 5 rule(s): Minimum Credit Score, High Debt-to-Income Flag, ...
```

Re-running is safe — existing rules are skipped (idempotent).

### 5. Start the API server

```powershell
uvicorn app.main:app --reload
```

| URL | Purpose |
|---|---|
| http://localhost:8000/docs | Swagger UI — try all endpoints |
| http://localhost:8000/redoc | ReDoc API reference |
| http://localhost:8000/health | Health check |

---

## Local Setup (macOS / Linux)

```bash
git clone https://github.com/DaZzleYash/DTDL-PS4.git
cd DTDL-PS4
git pull origin main

python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
mkdir -p data
alembic upgrade head
python -m app.finance.seed_rules
uvicorn app.main:app --reload
```

---

## Try the Demo (curl / PowerShell)

### List seeded rules

```powershell
curl http://localhost:8000/api/rules/
```

### Evaluate a good applicant (expect APPROVE)

```powershell
curl -X POST http://localhost:8000/api/decisions/evaluate `
  -H "Content-Type: application/json" `
  -d "{\"context\": {\"applicant\": {\"creditScore\": 720, \"annualIncome\": 85000, \"employmentStatus\": \"EMPLOYED\", \"dateOfBirth\": \"1994-01-15\", \"existingCustomer\": false}, \"loan\": {\"amount\": 25000, \"purpose\": \"AUTO\", \"termMonths\": 60}, \"risk_flags\": {\"hasDefaulted\": false, \"debtToIncomeRatio\": 0.30}}}"
```

### Evaluate high DTI (expect MANUAL_REVIEW)

Use the payloads in `app/finance/sample_requests.py` — each scenario has a named constant and expected outcome.

### Create a custom rule

```powershell
curl -X POST http://localhost:8000/api/rules/ `
  -H "Content-Type: application/json" `
  -d "{\"name\": \"My Rule\", \"priority\": 5, \"active\": true, \"condition\": {\"type\": \"NUMERIC\", \"field\": \"applicant.creditScore\", \"operator\": \"GTE\", \"value\": 700}, \"decision_outcome\": \"APPROVE\"}"
```

### Bulk evaluate

```powershell
curl -X POST http://localhost:8000/api/decisions/evaluate/bulk `
  -H "Content-Type: application/json" `
  -d "[{\"context\": {\"applicant\": {\"creditScore\": 720}, \"loan\": {}, \"risk_flags\": {}}}]"
```

---

## Running Tests

```powershell
# Full suite
pytest

# By module
pytest tests/engine           # condition evaluators (A)
pytest tests/rules            # rule CRUD (B)
pytest tests/decisions        # decision algorithm (C)
pytest tests/finance          # seeded demo scenarios (D)
pytest tests/integration      # end-to-end HTTP stack (E)

# Lint
ruff check app tests
```

Integration tests seed finance rules in-memory and hit the real HTTP routes — no running server required.

---

## Project Structure

```
DTDL-PS4/
├── app/
│   ├── main.py                 # FastAPI entry — wires all routers (E)
│   ├── core/                   # config, database, logging (E)
│   ├── schemas/                # shared contracts (B, C, E)
│   ├── engine/                 # JSON condition interpreter (A)
│   ├── rules/                  # rule CRUD + persistence (B)
│   ├── decisions/              # evaluation algorithm + API (C)
│   └── finance/                # demo domain: seeds, samples, catalog (D)
├── tests/
│   ├── engine/
│   ├── rules/
│   ├── decisions/
│   ├── finance/
│   └── integration/            # end-to-end tests (E)
├── alembic/                    # DB migrations
├── docker/                     # Docker setup (for later)
└── .github/workflows/ci.yml
```

---

## Team Ownership

| Contributor | Module | Folder |
|---|---|---|
| **A** | Rules Engine Core | `app/engine/` |
| **B** | Rule Management & Persistence | `app/rules/` |
| **C** | Decision Engine & API | `app/decisions/` |
| **D** | Finance Domain & Demo Content | `app/finance/` |
| **E** | Platform, Infra & Integration | `app/core/`, `tests/integration/` |

---

## Integration Checklist (Phase 2 — E)

- [x] Routers wired in `main.py` (`/api/rules`, `/api/decisions`)
- [x] Exception handlers mapped (404, 400, 500)
- [x] Finance seed script runs against live DB
- [x] End-to-end integration tests (`tests/integration/test_end_to_end.py`)
- [x] All module test suites present
- [ ] Docker compose verified (deferred)
- [ ] AI Engineering Log finalized

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/decisions.db` | DB connection string |
| `LOG_LEVEL` | `INFO` | Root logging level |
| `APP_ENV` | `local` | Environment tag in logs |

---

## Common Issues

| Symptom | Fix |
|---|---|
| `no such table: rules` | Run `alembic upgrade head` |
| Empty rules list | Run `python -m app.finance.seed_rules` |
| `ModuleNotFoundError: app` | Run commands from repo root, not inside `app/` |
| Dependency install fails | Use Python **3.12+**, not 3.9 |
| Port 8000 in use | `uvicorn app.main:app --reload --port 8001` |

---

## Docker (later)

When ready to containerize:

```powershell
docker compose -f docker/docker-compose.yml up --build
```

Postgres URL is set automatically in compose. Run migrations and seed inside the container:

```powershell
docker compose -f docker/docker-compose.yml exec app alembic upgrade head
docker compose -f docker/docker-compose.yml exec app python -m app.finance.seed_rules
```

---

## AI Engineering Log

> Each contributor maintains their own section during the hackathon.

### Contributor E
- **Tools used:** Cursor
- **Phase 0:** project scaffold, platform layer, shared schemas, CI/Docker skeleton
- **Phase 2:** router wiring verification, end-to-end integration tests, local run documentation
