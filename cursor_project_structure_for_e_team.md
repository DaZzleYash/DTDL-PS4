# DTDL-PS4 — Team E Cursor Prompt Playbook

**Project:** Finance Decision Engine (PS4 — Configurable Decision Automation Platform)  
**Your role:** Contributor **E** — Platform, Infra & Integration  
**Repo:** `https://github.com/DaZzleYash/DTDL-PS4`  
**Spec reference:** `finance-decision-engine-spec-5-members.md`  
**Exported / cleaned:** July 24, 2026

---

## How to use this document

- Prompts are sorted in **project timeline order** (Phase 0 → Phase 2 → polish).
- Copy the **Prompt** block into Cursor as-is; adjust paths only if your machine differs.
- **Outcome** tells you what “done” looks like before moving on.
- Prompts marked **(E)** are your work. Others are **team checkpoints** — use when reviewing or unblocking teammates.
- Removed: system notifications, “briefly inform user” noise, duplicate status checks, and full Cursor reply dumps.

---

## Timeline overview

| Phase | When | E's focus | Depends on |
|---|---|---|---|
| **0** | Day 1 — first session | Scaffold, shared contracts, CI/Docker skeleton | Nothing |
| **0b** | Day 1 — after scaffold | Push to GitHub, team handoff | Phase 0 merged |
| **1** | Parallel (A–D build) | Support, review schemas, platform hardening | Phase 0 on `main` |
| **2** | After A/B/C/D merge | Wire routers, E2E tests, README, local demo | All modules merged |
| **3** | Pre-submission | AI Engineering Log, Docker fix, demo prep | Phase 2 complete |
| **Bonus** | If time | Confidence, history, AI rule gen (see ADDITIONS) | PS4 core done |

---

# PHASE 0 — Project scaffold (E drives)

### Prompt 1 — Kickstart repo structure **(E)**

```
Read finance-decision-engine-spec-5-members.md and PS4 problem statement
(The Talent Hack — Problem Statement 4: Configurable Decision Automation Platform).

We are Team E (Platform / Infra / Integration). Build the Phase 0 scaffold so
contributors A–D can branch and work in parallel:

- pyproject.toml, requirements.txt, .env.example, .gitignore
- app/core/ (config, database, logging)
- app/schemas/ (errors, rule, decision — shared contracts)
- app/exceptions.py + exception handlers in main.py
- app/main.py with GET /health
- Module stubs: app/engine/, app/rules/, app/decisions/, app/finance/ each with README
- alembic scaffolding, docker/, .github/workflows/ci.yml
- tests/integration/ (health + exception tests)
- README.md + CONTRIBUTING.md

Do not implement A/B/C/D logic yet — stubs only.
Reference: finance-decision-engine-spec-5-members.md §4, §5, §10, §12 Phase 0.
```

**Outcome:** Empty repo becomes a collaborative monolith skeleton. B and C review shared schemas before Phase 1 branches start.

**Commit message:**
```
chore: Phase 0 project scaffold for Finance Decision Engine (PS4)
```

---

### Prompt 2 — Push to GitHub **(E)**

```
Push the Phase 0 scaffold to origin main.
Repo: https://github.com/DaZzleYash/DTDL-PS4.git
```

**Outcome:** Team can clone and branch. If push fails on `.github/workflows/ci.yml`, GitHub PAT needs **`workflow`** scope, or temporarily remove CI file from commit and add it back after token fix.

**Fix for workflow scope error:**
```
1. GitHub → Settings → Developer settings → Personal access tokens
2. Enable "workflow" scope
3. cmdkey /delete:git:https://github.com   (clear cached token)
4. git push -u origin main
```

---

### Prompt 3 — Generalize domain folder? **(E — optional discussion)**

```
We use app/finance/ for the demo domain, but the platform should work for any
domain (insurance, HR, etc.). Should we rename to app/domains/finance/?
Compare with finance-decision-engine-spec-5-members.md §3 architecture principle:
"finance domain is a thin layer on top."
Recommend and apply only if the team agrees — do not break merged work.
```

**Outcome:** Team stayed on `app/finance/` on main (spec path). Domain-agnostic core remains `engine/`, `rules/`, `decisions/`.

---

# PHASE 1 — Parallel module work (E supports, others build)

While A–D work on feature branches, E can run **platform hardening** in parallel (spec §12):

### Prompt 4 — Platform hardening **(E, optional during Phase 1)**

```
On branch feat/platform-hardening from main:

1. Polish docker/Dockerfile + docker-compose.yml
2. Ensure CI runs pytest + ruff on push/PR
3. Verify /health and structured logging in app/core/logging.py
4. Do not touch app/engine/, app/rules/, app/decisions/, app/finance/ internals
```

**Outcome:** Docker/CI skeleton ready; no module conflicts.

---

### Team checkpoint — Review incoming work **(E)**

```
Pull latest main. Compare merged modules against PS4 Problem Statement 4 and
finance-decision-engine-spec-5-members.md §14 acceptance checklist.

Report:
- What is aligned (rules, decisions, explainability, tests, API docs)
- What is missing (finance demo, integration, AI log, Docker verified)
- Which contributor should act next
```

**Outcome:** Alignment report before Phase 2. Typical order: A → B → C → D → E integration.

---

### Team checkpoint — Module status **(any contributor)**

```
Check each module against its README deliverables in app/engine/, app/rules/,
app/decisions/, app/finance/. Report what is complete vs stub.
Run pytest per module folder.
```

**Outcome:** Clear picture of who is done. E waits for D before full E2E demo.

---

# PHASE 2 — Integration (E drives)

### Prompt 5 — Final integration pass **(E — main deliverable)**

```
We are Team E. All modules A/B/C/D are merged on main. Do Phase 2 integration
per finance-decision-engine-spec-5-members.md §10 and §12:

1. git pull origin main
2. Verify app/main.py wires rules + decisions routers and exception handlers
3. Add tests/integration/conftest.py (in-memory DB + seed finance rules)
4. Add tests/integration/test_end_to_end.py:
   - seed rules → POST /api/decisions/evaluate → assert final_decision + trace
   - all 5 sample scenarios from app/finance/sample_requests.py
   - NO_DECISION, bulk evaluate, 400 invalid rule, 404 missing rule
5. Update README.md with comprehensive local run guide (Windows + macOS)
6. Run full pytest suite

Reference spec §13 for setup commands. Docker can wait.
```

**Outcome:** Full stack verified. README documents local setup. Integration tests pass without a running server.

**Commit message:**
```
chore(integration): add end-to-end tests and local run guide
```

---

### Prompt 6 — What is active after integration? **(E)**

```
After integration, list everything that is active:
- All API endpoints and their purpose
- Seeded finance rules (names + outcomes)
- How modules connect (engine → rules → decisions → finance demo)
- Step-by-step local run guide for Windows (Python 3.12, SQLite, no Docker)
```

**Outcome:** Team demo script and onboarding doc.

---

# PHASE 2b — Local setup & troubleshooting

### Prompt 7 — Fix pip / greenlet install error **(E)**

```
pip install -r requirements.txt fails building greenlet from source.
Error: C7555 designated initializers requires /std:c++latest

Diagnose Python version and fix so the project runs locally per spec (Python 3.12+).
```

**Outcome:** Root cause is Python 3.9 — install 3.12, recreate `.venv`, reinstall deps.

**Fix commands:**
```powershell
cd D:\DTDL-PS4
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Prompt 8 — Run project locally **(E / anyone)**

```
Set up and run the project locally on Windows:
1. venv + pip install
2. copy .env.example .env, mkdir data
3. alembic upgrade head
4. python -m app.finance.seed_rules
5. uvicorn app.main:app --reload

Confirm /health, /docs, /api/rules/, /api/decisions/evaluate work.
```

**Outcome:** Server at http://127.0.0.1:8000. Five rules seeded.

---

### Prompt 9 — Server running — what's next? **(E)**

```
uvicorn is running and seed_rules completed. What should we verify next before
demo/submission? Include Swagger steps, test commands, and open hackathon
deliverables (AI Engineering Log, etc.).
```

**Outcome:** Verify API → run pytest → commit integration → write AI log → prep judge demo.

---

### Prompt 10 — Health page looks empty **(E)**

```
GET /health shows blank page in Cursor embedded browser (Pretty-print bar only).
Is the API broken?
```

**Outcome:** API is fine — returns JSON. Use http://127.0.0.1:8000/docs or Chrome/Edge, not Cursor Simple Browser for JSON endpoints.

**Verify:**
```powershell
curl http://127.0.0.1:8000/health
# {"status":"healthy","environment":"local","timestamp":"..."}
```

---

# PHASE 3 — Submission prep (E)

### Prompt 11 — ADDITIONS PDF review **(E)**

```
Read ADDITIONS.pdf (decision history, confidence score, AI rule generator,
conflict detector, rule versioning, demo UI).

Compare each item to PS4 must-haves vs nice-to-have vs mid-challenge change
request examples in the problem statement.

Recommend what Team E should implement before demo and what to skip.
Do not over-engineer — core platform already works.
```

**Outcome:** Prioritized backlog. Only **AI_ENGINEERING_LOG.md** is a required PS4 deliverable from that list.

---

### Prompt 12 — Are suggested additions PS4 must-haves? **(E)**

```
From the ADDITIONS recommendations, which are strictly required by PS4 Problem
Statement 4 for initial submission vs optional mid-challenge items?
Be explicit: AI log, confidence score, evaluate() refactor, decision history,
AI rule generator.
```

**Outcome:**

| Item | PS4 must-have? |
|---|---|
| `AI_ENGINEERING_LOG.md` | **Yes** |
| Confidence score | Partial — priority already in traces; dedicated field is nice-to-have |
| `evaluate()` / `evaluate_request()` split | No — internal refactor |
| Decision history | No — mid-challenge example only |
| AI rule generator | No — PS4 requires AI in SDLC, not AI in product |

---

### Prompt 13 — Create AI Engineering Log **(E — required deliverable)**

```
Create AI_ENGINEERING_LOG.md at repo root per PS4 deliverable requirements:

- AI tools used (Cursor, etc.)
- Key prompts sent (reference this playbook)
- AI-generated code accepted vs rejected/modified
- How AI outputs were validated (pytest, manual API tests)
- Bugs introduced by AI and how resolved

Add entries for Phase 0 scaffold, integration pass, and any Docker work.
Do not write retroactively at the end — log as we go.
```

**Outcome:** Required PS4 submission artifact.

---

### Prompt 14 — Docker setup **(E)**

```
Is Docker ready for demo? Check docker/Dockerfile, docker-compose.yml against
spec §13.5. Build and verify app + Postgres end-to-end.

If broken, fix: psycopg2 driver, auto-migrations on startup, document seed command.
Run full pytest after fix.
```

**Outcome:** `docker compose -f docker/docker-compose.yml up --build` works. Add `psycopg2-binary>=2.9` if missing.

**After Docker up:**
```powershell
docker compose -f docker/docker-compose.yml exec app python -m app.finance.seed_rules
curl http://localhost:8000/health
```

---

### Prompt 15 — Self-verify full stack **(E)**

```
Run full verification:
- pytest (all modules + integration)
- API smoke: health, rules CRUD, all 5 finance scenarios via /api/decisions/evaluate
- Docker stack if configured

Report pass/fail table.
```

**Outcome:** 70/70 tests, all demo scenarios return expected `final_decision`.

---

# REFERENCE — Local run guide (consolidated)

## Prerequisites

- Python **3.12+** (not 3.9)
- Git

## One-time setup

```powershell
cd D:\DTDL-PS4
git pull origin main

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env
mkdir data -Force

alembic upgrade head
python -m app.finance.seed_rules
```

## Start server

```powershell
uvicorn app.main:app --reload
```

| URL | Purpose |
|---|---|
| http://127.0.0.1:8000/docs | Swagger — primary demo UI |
| http://127.0.0.1:8000/health | Health JSON |
| http://127.0.0.1:8000/api/rules/ | List seeded rules |
| http://127.0.0.1:8000/api/decisions/evaluate | Run decision |

## Run tests

```powershell
pytest                        # full suite
pytest tests/integration      # E2E only
pytest tests/engine           # A
pytest tests/rules            # B
pytest tests/decisions        # C
pytest tests/finance          # D
ruff check app tests
```

## Demo evaluate payload (expect APPROVE)

```json
{
  "context": {
    "applicant": {
      "creditScore": 720,
      "annualIncome": 85000,
      "employmentStatus": "EMPLOYED",
      "dateOfBirth": "1994-01-15",
      "existingCustomer": false
    },
    "loan": { "amount": 25000, "purpose": "AUTO", "termMonths": 60 },
    "risk_flags": { "hasDefaulted": false, "debtToIncomeRatio": 0.30 }
  }
}
```

More scenarios: `app/finance/sample_requests.py`  
Rule descriptions: `app/finance/rule_catalog.md`

---

# REFERENCE — Architecture (what E wires together)

```
Request JSON
    ↓
POST /api/decisions/evaluate     ← app/decisions/router.py (C)
    ↓
DecisionEngineService            ← app/decisions/service.py (C)
    ↓ reads rules
RuleRepository                   ← app/rules/ (B)
    ↓ evaluates conditions
ConditionEvaluatorRegistry       ← app/engine/ (A)
    ↓
DecisionResponse (final_decision + full trace)

Finance demo (D): app/finance/seed_rules.py → loads rules via RuleService (B)
Platform (E): app/core/, app/main.py, tests/integration/, docker/, CI
```

---

# REFERENCE — Active API surface (post-integration)

| Method | Path | Module |
|---|---|---|
| GET | `/health` | E |
| GET | `/docs` | FastAPI auto |
| GET/POST/PUT/PATCH/DELETE | `/api/rules/` … | B |
| POST | `/api/decisions/evaluate` | C |
| POST | `/api/decisions/evaluate/bulk` | C |

## Seeded finance rules

| Rule | Outcome | Priority |
|---|---|---|
| Minimum Credit Score | APPROVE | 10 |
| High Debt-to-Income Flag | MANUAL_REVIEW | 20 |
| VIP Existing Customer Fast Track | APPROVE | 25 |
| Prior Default Block | REJECT | 30 |
| Underage Applicant Block | REJECT | 40 |

---

# REFERENCE — PS4 acceptance checklist (§14)

- [x] pytest passes (engine, rules, decisions, finance, integration)
- [x] uvicorn runs on SQLite
- [x] `/docs` shows Rules + Decisions
- [x] Unknown condition type → 400
- [x] Seeded rules + sample payload → correct decision + trace
- [x] No match → `NO_DECISION`
- [x] Missing rule id → 404 structured error
- [ ] Docker compose verified end-to-end
- [x] CI workflow exists
- [ ] **AI Engineering Log** (required deliverable)
- [x] New rule type = one evaluator file + one registry line

---

# REFERENCE — Judge demo script (5 min)

1. `GET /health` — service up  
2. `GET /api/rules/` — 5 configurable rules, no code change  
3. `POST /api/decisions/evaluate` — good applicant → `APPROVE` + trace  
4. Same endpoint — prior default payload → `REJECT` + which rule fired  
5. `POST /api/rules/` — create a new rule live → re-evaluate  

---

# REFERENCE — Common issues

| Symptom | Fix |
|---|---|
| `greenlet` build fails on pip | Use Python 3.12+, recreate venv |
| `no such table: rules` | `alembic upgrade head` |
| Empty rules list | `python -m app.finance.seed_rules` |
| `/health` blank in Cursor browser | Use `/docs` or Chrome — API returns JSON fine |
| Push rejected on CI workflow | PAT needs `workflow` scope |
| Docker app crash | Add `psycopg2-binary>=2.9` to requirements.txt |
| `ModuleNotFoundError: app` | Run commands from repo root |

---

# APPENDIX — Other team prompts (out of E timeline, kept for reference)

Use these on the correct feature branch — not E's integration phase.

### Contributor A — Engine core

```
Implement app/engine/ per finance-decision-engine-spec-5-members.md §6:
EvaluationContext, EvaluationResult, ConditionEvaluator, registry with AND/OR/NOT,
evaluators (numeric, string, boolean, date), tests in tests/engine/.
Branch: feat/engine-core
```

### Contributor B — Rules module

```
Implement app/rules/ per spec §7: SQLAlchemy model, Alembic migration, repository,
service (validate via registry), router /api/rules, tests in tests/rules/.
Branch: feat/rules-module
```

### Contributor C — Decisions module

```
Implement app/decisions/ per spec §8. app/schemas/decision.py is already done (Phase 0).
Build service.py (DecisionEngineService) and router.py (/evaluate, /evaluate/bulk).
Tests in tests/decisions/. Branch: feat/decisions-module
```

### Contributor D — Finance demo

```
Implement app/finance/ per spec §9: schemas.py, seed_rules.py, sample_requests.py,
rule_catalog.md, tests/finance/. Branch: feat/finance-domain
```

### Contributor C — Commit feature branch

```
Commit decisions work on feat/decisions-module in logical commits per spec §12:
1. feat(decisions): DecisionEngineService
2. feat(decisions): router + main wiring
3. test(decisions): algorithm + API tests
Push and open PR to main.
```

---

# APPENDIX — Optional ADDITIONS backlog (if time after PS4 core)

Priority if hackathon time remains:

1. **AI_ENGINEERING_LOG.md** — do first (required)  
2. **Confidence score** — add `confidence: float` to `DecisionResponse` using `matched_priority_sum / total_active_priority_sum`  
3. **Decision history** — `app/history/`, migration, `GET /api/history` (mid-challenge pattern)  
4. **AI rule generator** — `POST /api/ai/generate-rule` + `registry.validate()` (strong AI demo)  
5. Skip unless asked: conflict detector, rule version history, static demo HTML  

---

# APPENDIX — Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/decisions.db` | DB connection |
| `LOG_LEVEL` | `INFO` | Logging |
| `APP_ENV` | `local` | Environment tag |

Docker compose overrides `DATABASE_URL` to Postgres automatically.

---

# APPENDIX — E folder ownership (do not cross-edit)

| Path | Owner |
|---|---|
| `app/core/` | E |
| `app/main.py` | E (wiring only in Phase 2) |
| `app/schemas/errors.py`, `app/exceptions.py` | E |
| `tests/integration/` | E |
| `docker/`, `.github/workflows/` | E |
| `app/engine/` | A |
| `app/rules/` | B |
| `app/decisions/` | C |
| `app/finance/` | D |

Rule: one commit should not touch more than one module folder unless updating a shared contract in `app/schemas/` (with team heads-up).

---

*End of playbook — ~650 lines, sequential prompts only, sorted by project phase.*
