# AI Engineering Log

**Project:** Finance Decision Engine (DTDL-PS4)  
**Problem Statement:** PS4 — Configurable Decision Automation Platform  
**Team role documented here:** Contributor **E** (Platform, Infra & Integration)  
**Repository:** https://github.com/DaZzleYash/DTDL-PS4  
**Date:** July 24, 2026

This log satisfies the PS4 **AI Usage Requirement**. It records how AI development tools were used during design, implementation, validation, and integration — not AI features inside the product itself.

For a chronological list of Cursor prompts used by Team E, see also [`cursor_project_structure_for_e_team.md`](cursor_project_structure_for_e_team.md).

---

## 1. AI tools used

| Tool | Purpose |
|---|---|
| **Cursor** (Agent mode) | Primary tool — scaffolding, integration, README, Docker fixes, test authoring, PS4 alignment reviews, prompt playbook |
| **Cursor** (Chat) | Architecture questions, ADDITIONS.pdf triage, troubleshooting (Python version, health endpoint, git push) |

Other teammates may have used GitHub Copilot, ChatGPT, or Claude on modules A–D; this log focuses on work driven through Cursor for **Contributor E**.

---

## 2. Key prompts provided

Prompts are grouped by project phase. Wording is summarized; full copy-paste prompts live in `cursor_project_structure_for_e_team.md`.

### Phase 0 — Scaffold (Day 1)

**Prompt (summary):**
> Read `finance-decision-engine-spec-5-members.md` and PS4 problem statement. We are Team E. Build Phase 0 scaffold: `pyproject.toml`, `app/core/`, shared schemas, exception handlers, `main.py` with `/health`, module stubs for A–D, Alembic/Docker/CI skeleton, integration tests, README + CONTRIBUTING. Do not implement A/B/C/D logic yet.

**Intent:** Give the team a merge base so A, B, C, D can work in parallel on separate folders.

---

### Phase 1 — Review & alignment

**Prompt (summary):**
> Pull latest `main`. Compare merged modules against PS4 Problem Statement 4 and build spec §14. Report what is aligned, what is missing, and who should act next.

**Intent:** Gate before Phase 2 integration; confirmed engine, rules, and decisions modules matched PS4 functional requirements.

---

### Phase 2 — Integration (Contributor E)

**Prompt (summary):**
> All modules A/B/C/D are merged. Verify router wiring in `main.py`, add `tests/integration/test_end_to_end.py` (seed finance rules → POST `/api/decisions/evaluate` → assert decision + trace), update README with local run guide, run full pytest.

**Intent:** Complete spec §10 / §12 Phase 2 integration pass.

---

### Phase 3 — Submission prep

| Prompt topic | Purpose |
|---|---|
| ADDITIONS.pdf review | Prioritize optional features (confidence, history, AI rule gen) vs PS4 must-haves |
| PS4 must-have clarification | Confirm only AI Engineering Log is strictly required from ADDITIONS list |
| Docker verification | Fix Postgres driver, auto-migrations, smoke-test stack |
| Local setup errors | Diagnose `greenlet` / Python 3.9 install failure |
| Health page empty in browser | Confirm API vs Cursor embedded browser display issue |

---

## 3. AI-generated code that was accepted

The following was **generated or heavily drafted by Cursor**, then reviewed and kept in the repository.

### Platform layer (`app/core/`, `app/main.py`)

| File | What AI produced |
|---|---|
| `app/core/config.py` | `pydantic-settings` `Settings` class (`DATABASE_URL`, `LOG_LEVEL`, `APP_ENV`) |
| `app/core/database.py` | SQLAlchemy engine, `SessionLocal`, `get_db()` dependency |
| `app/core/logging.py` | Structured logging setup |
| `app/exceptions.py` | `RuleNotFoundError`, `InvalidRuleError` |
| `app/schemas/errors.py` | Standard JSON error body schema |
| `app/main.py` | FastAPI app, lifespan, exception handlers (404/400/500), `GET /health`, router includes |

### Shared contracts (Phase 0 — reviewed by B & C)

| File | What AI produced |
|---|---|
| `app/schemas/rule.py` | `RuleCreate`, `RuleUpdate`, `RuleOut`, `RuleActiveUpdate` |
| `app/schemas/decision.py` | `EvaluateRequest`, `RuleTrace`, `DecisionResponse` |

### Infrastructure

| File | What AI produced |
|---|---|
| `pyproject.toml`, `requirements.txt`, `.env.example`, `.gitignore` | Project metadata and dependencies |
| `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` | Migration scaffolding |
| `docker/Dockerfile`, `docker/docker-compose.yml` | Multi-stage build, Postgres compose |
| `.github/workflows/ci.yml` | pytest + ruff on push/PR |

### Integration & docs (Phase 2)

| File | What AI produced |
|---|---|
| `tests/integration/conftest.py` | In-memory DB + seeded rules fixture |
| `tests/integration/test_end_to_end.py` | Full HTTP E2E tests (5 demo scenarios, bulk, NO_DECISION, 400, 404) |
| `tests/integration/test_health.py` | Health + OpenAPI checks |
| `tests/integration/test_exceptions.py` | Exception handler unit tests |
| `README.md` | Local run guide, architecture, API reference, checklists |
| `CONTRIBUTING.md` | Module boundaries, branch plan, commit conventions |
| `cursor_project_structure_for_e_team.md` | Sequential Cursor prompt playbook for Team E |
| `scripts/test_all_endpoints.py` | Live API smoke test script |

### Module stubs (handoff to A–D)

| Path | What AI produced |
|---|---|
| `app/engine/README.md` | Deliverables + branch name for Contributor A |
| `app/rules/README.md`, `app/rules/router.py` (stub) | Handoff for Contributor B |
| `app/decisions/README.md`, `app/decisions/router.py` (stub) | Handoff for Contributor C |
| `app/finance/README.md` | Handoff for Contributor D |

### Docker fix (accepted after manual verification)

| Change | What AI produced |
|---|---|
| `requirements.txt` | Added `psycopg2-binary>=2.9` for Postgres in Docker |
| `docker/Dockerfile` | Run `alembic upgrade head` before uvicorn on container start |

**Note:** Modules A–D (`app/engine/`, `app/rules/`, `app/decisions/`, `app/finance/`) were implemented by respective contributors; E’s AI work wired them together in `main.py` and validated via integration tests.

---

## 4. AI-generated code that was rejected or modified

| AI suggestion | Decision | Reason |
|---|---|---|
| Rename `app/finance/` → `app/domains/finance/` | **Rejected** (locally); not merged to team `main` | Team and spec use `app/finance/`; D module landed on that path. Core is already domain-agnostic via `engine/`, `rules/`, `decisions/`. |
| Implement full ADDITIONS backlog (confidence, decision history, AI rule generator, conflict detector, rule versioning, demo UI) | **Rejected** for initial submission | PS4 core already met; only AI log is required deliverable. ADDITIONS treated as optional / mid-challenge backlog. |
| Numeric threshold `strength` on `EvaluationResult` for confidence | **Rejected** | Prefer simpler priority-weight formula if confidence is added later; not implemented yet. |
| Wire `app/domains/` duplicate stubs | **Removed** | Conflicted with merged `app/finance/` on `main`. |
| Stub routers left commented in `main.py` | **Modified** | Replaced with real `include_router` calls after B and C merged. |
| Generic error messages in exception handlers | **Kept with modification** | 500 handler logs full trace server-side only; client gets generic message (spec §10). |
| README duplicate paragraphs during stash merge | **Modified** | Conflict marker blocks (`<<<<<<<`) accidentally committed; cleaned manually before final submission. |
| AI Engineering Log only as README section | **Modified** | PS4 asks for a dedicated log — this standalone `AI_ENGINEERING_LOG.md` file was created. |

---

## 5. How AI outputs were validated

AI-generated code was **never accepted on model opinion alone**. Validation always used deterministic checks:

### Automated tests

```powershell
pytest                          # full suite (engine, rules, decisions, finance, integration)
pytest tests/integration        # E2E HTTP stack
ruff check app tests            # lint
```

**Result at integration:** 70/70 tests passing after Docker fix and full module merge.

### Manual API verification

| Check | Method |
|---|---|
| Health | `curl http://127.0.0.1:8000/health` |
| Rules CRUD | Swagger UI `/docs` + `GET /api/rules/` |
| Decision evaluate | `POST /api/decisions/evaluate` with payloads from `app/finance/sample_requests.py` |
| All endpoints | `python scripts/test_all_endpoints.py` (with server running) |

### Docker verification

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec app python -m app.finance.seed_rules
curl http://localhost:8000/health
```

### Spec alignment review

AI-assisted comparison against:

- PS4 Problem Statement 4 (functional + non-functional + deliverables)
- `finance-decision-engine-spec-5-members.md` §14 acceptance checklist

### What we did **not** use as acceptance criteria

- LLM “looks correct” judgments
- Cursor chat claims without running pytest or curl
- Embedded browser display for JSON endpoints (known to render blank)

---

## 6. Bugs or issues introduced by AI and how they were resolved

Only issues with an explicit **`fix(...)` commit** in git history are listed here. Each entry maps to a real commit on `main`.

```text
git log --grep="fix" --oneline
810fe45 fix(docker): add Postgres driver and auto-migrations on startup
957b251 fix(rules): resolve ruff lint issues in rules module
```

| Commit | Introduced in | Symptom | Resolution | AI link |
|---|---|---|---|---|
| [`810fe45`](https://github.com/DaZzleYash/DTDL-PS4/commit/810fe45) | Phase 0 Docker scaffold (`1a4c877`, Co-authored-by: Cursor) | App container crash on startup: `ModuleNotFoundError: No module named 'psycopg2'` when connecting to Postgres in compose | Added `psycopg2-binary>=2.9` to `requirements.txt` | Yes — missing driver in AI-generated scaffold |
| [`810fe45`](https://github.com/DaZzleYash/DTDL-PS4/commit/810fe45) | Phase 0 Docker scaffold (`1a4c877`, Co-authored-by: Cursor) | Fresh Docker start had no `rules` table — API failed until migrations were run manually | Changed Dockerfile `CMD` to run `alembic upgrade head` before `uvicorn` | Yes — no migration step in original AI Dockerfile |
| [`957b251`](https://github.com/DaZzleYash/DTDL-PS4/commit/957b251) | Rules module first pass (`ddea071`, Co-authored-by: Cursor) | `ruff check` failed: FastAPI `Depends()` B008 warnings, deprecated `timezone.utc` usage, unused import in `app/rules/service.py` | Added `# ruff: noqa: B008` on router; switched to `datetime.UTC`; removed unused import | Yes — lint/style issues in AI-generated rules code |

### How each fix was validated

| Commit | Validation |
|---|---|
| `810fe45` | Rebuilt compose stack; app container started; health check passed; API smoke tests green |
| `957b251` | `ruff check app tests` clean; rules module tests still passing |

### Not listed here (no fix commit in git)

The following were discussed during development but do **not** appear as `fix(...)` commits in history, so they are excluded from this section:

- GitHub PAT `workflow` scope push error (process/credentials — no code fix commit)
- Python 3.9 / `greenlet` install failure (local environment — no repo fix commit)
- README merge conflict markers (introduced in `31f3a17`, cleaned locally — pending commit)
- Cursor browser showing blank `/health` page (display issue — API worked; no code change)

---

## 7. Summary

| PS4 AI log requirement | Covered in section |
|---|---|
| AI tools used | §1 |
| Key prompts provided | §2 (+ full playbook file) |
| AI-generated code accepted | §3 |
| AI-generated code rejected/modified | §4 |
| How outputs were validated | §5 |
| Bugs/issues and resolutions | §6 |

**Process principle used throughout:** AI for **generation**; pytest, ruff, curl, Swagger, and spec checklists for **acceptance**. Same input state must produce the same pass/fail verdict.

---

## 8. Contributor E — session notes (for judges)

- **Phase 0:** Cursor scaffolded the collaborative monolith in one session; team branched A–D from `main`.
- **Phase 2:** Cursor added integration tests and README after all modules merged; validated full loan demo flow end-to-end.
- **Phase 3:** Cursor triaged ADDITIONS.pdf — implemented AI log and Docker fixes; deferred confidence/history/AI-rule-gen as non-required for initial PS4.
- **Prompt playbook:** Exported and cleaned to `cursor_project_structure_for_e_team.md` for reproducibility.

---

*This file should be updated if mid-challenge requirements add new features (e.g. audit history, confidence score, rule versioning).*
