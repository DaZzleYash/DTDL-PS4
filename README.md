# Finance Decision Engine

**PS4 — Configurable Decision Automation Platform**  
Deutsche Telekom Digital Labs · The Talent Hack (Build Sprint)

A Loan & Credit Decisioning Engine built with Python 3.12 and FastAPI. Applications arrive as structured JSON, get evaluated against **configurable rules** stored in a database, and the service returns an explainable decision: `APPROVE`, `REJECT`, or `MANUAL_REVIEW`.

## Team Ownership

| Contributor | Module | Folder |
|---|---|---|
| **A** | Rules Engine Core | `app/engine/` |
| **B** | Rule Management & Persistence | `app/rules/` |
| **C** | Decision Engine & API | `app/decisions/` |
| **D** | Finance Domain & Demo Content | `app/finance/` |
| **E** | Platform, Infra & Integration | `app/core/`, `docker/`, CI |

See each module's `README.md` for deliverables and branch name.

## Quick Start (Local — SQLite)

```bash
# 1. Clone and set up
git clone https://github.com/DaZzleYash/DTDL-PS4.git
cd DTDL-PS4
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
mkdir data

# 3. Run migrations (once Contributor B adds the rules table)
alembic upgrade head

# 4. Start the server
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Docker (Postgres)

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Running Tests

```bash
pytest                        # all tests
pytest tests/integration      # platform / health / exception tests
pytest tests/engine           # Contributor A
pytest tests/rules            # Contributor B
pytest tests/decisions        # Contributor C
pytest tests/finance          # Contributor D
```

## Project Structure

```
DTDL-PS4/
├── app/
│   ├── main.py                 # FastAPI app entry (E)
│   ├── core/                   # config, database, logging (E)
│   ├── schemas/                # shared contracts — Phase 0 (B, C, E)
│   ├── engine/                 # condition evaluator (A)
│   ├── rules/                  # rule CRUD + persistence (B)
│   ├── decisions/              # decision algorithm + API (C)
│   └── finance/                # loan domain + seed data (D)
├── tests/
├── alembic/                    # DB migrations
├── docker/
└── .github/workflows/ci.yml
```

## Phase 0 Status (Contributor E)

- [x] Project scaffold (`pyproject.toml`, `requirements.txt`, `.env.example`)
- [x] Core platform (`config`, `database`, `logging`)
- [x] Shared schemas (`rule`, `decision`, `errors`)
- [x] Exception handlers + `/health` endpoint
- [x] Docker + docker-compose skeleton
- [x] CI workflow (pytest + ruff)
- [x] Alembic scaffolding
- [ ] Wire routers in `main.py` (Phase 2 — after A/B/C/D merge)

## Branch Plan

1. **Phase 0** — `chore/scaffold` on `main` (this commit)
2. **Phase 1** — parallel feature branches:
   - `feat/engine-core` (A)
   - `feat/rules-module` (B)
   - `feat/decisions-module` (C)
   - `feat/finance-domain` (D)
   - `feat/platform-hardening` (E)
3. **Phase 2** — `chore/integration` (E wires everything together)

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/decisions.db` | DB connection string |
| `LOG_LEVEL` | `INFO` | Root logging level |
| `APP_ENV` | `local` | Environment tag in logs |

## AI Engineering Log

> Each contributor maintains their own section here during the hackathon.

### Contributor E
- **Tools used:** Cursor
- **Phase 0 scaffold:** project structure, platform layer, shared schemas, CI/Docker skeleton
