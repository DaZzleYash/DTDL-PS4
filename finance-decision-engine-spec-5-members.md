# Finance Decision Engine — Build Spec (FastAPI, 5 Contributors, Antigravity)

Same project as before — a **Loan & Credit Decisioning Engine** in Python/FastAPI —
now split five ways instead of three. Nothing from the original scope is
dropped; the "Decisions" and "Platform/Infra" work that used to be shared or
bundled now each get a dedicated owner, which is what makes a clean 5-way
split possible without inventing extra scope.

Give **§5 (Shared Contracts)** to everyone first — it's the only part that
needs joint agreement. After that, each contributor works from just their own
section (§6–§10). §11 shows the dependency graph so nobody blocks on anybody
they don't have to. §12 is the commit/branch plan — read it before writing
any code; shipping gradually is a hard requirement here, not a nice-to-have.

## 1. Scope

Applications (loan requests) arrive as structured JSON, get evaluated against
**configurable rules** (eligibility, risk, fraud flags — stored in a
database, never hardcoded), and the service returns an explainable decision:
`APPROVE`, `REJECT`, or `MANUAL_REVIEW`, plus which rules fired and why.

One domain, one clear vertical slice — no multi-tenancy, no rule
marketplace, no ML scoring. The five-way split adds ownership clarity, not
extra features — resist the urge to over-engineer just because there are
more hands.

## 2. Tech Stack

- Python 3.12, FastAPI, Pydantic v2 (`pydantic-settings` for config)
- SQLAlchemy 2.0 (sync) + Alembic for migrations
- DB: SQLite for local dev (zero setup) / PostgreSQL in Docker
- pytest + httpx `TestClient`
- `uvicorn` as the ASGI server
- Docker + docker-compose (app + Postgres) + a simple CI workflow
- Structure: **modular monolith** — one FastAPI app, five clearly-owned internal packages. No microservices, no queue.

## 3. Architecture Principle

- **Rules are data** — stored as rows with a JSON condition tree in one column; edited through the API, never through code changes.
- **The engine is code** — a generic JSON-tree interpreter with zero knowledge of "loans." Just `NUMERIC`/`STRING`/`BOOLEAN`/`DATE` checks against a JSON payload.
- **The finance domain is a thin layer on top** — request shape documentation, seeded example rules, demo payloads. It never leaks into the engine.
- **Platform concerns (config, DB session, logging, errors, Docker, CI) are their own layer** — everything else depends on this layer, it depends on nothing project-specific.

Four independent concerns, plus the connective platform layer, is exactly why this now splits five ways cleanly.

## 4. Repo Structure (five owners)

```
finance-decision-engine/
├── pyproject.toml
├── .env.example
├── alembic.ini / alembic/            ★ E (scaffolding) + B (first migration)
├── .github/workflows/ci.yml          ★ E
├── docker/
│   ├── Dockerfile                    ★ E
│   └── docker-compose.yml            ★ E
├── app/
│   ├── main.py                       ★ E
│   ├── core/
│   │   ├── config.py                 ★ E
│   │   ├── database.py               ★ E
│   │   └── logging.py                ★ E
│   ├── exceptions.py                 ★ E
│   ├── schemas/                      (shared contracts — Phase 0, frozen after)
│   │   ├── errors.py                 ★ E
│   │   ├── rule.py                   ★ B
│   │   └── decision.py               ★ C
│   ├── engine/                       ★ CONTRIBUTOR A
│   │   ├── context.py
│   │   ├── result.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   └── evaluators/
│   │       ├── numeric.py
│   │       ├── string.py
│   │       ├── boolean.py
│   │       └── date.py
│   ├── rules/                        ★ CONTRIBUTOR B
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py                 /api/rules
│   ├── decisions/                    ★ CONTRIBUTOR C
│   │   ├── service.py                 DecisionEngineService (generic algorithm)
│   │   └── router.py                 /api/decisions
│   └── finance/                      ★ CONTRIBUTOR D
│       ├── schemas.py                 LoanApplicationContext (documentation model)
│       ├── seed_rules.py              loads the example rule set via RuleService
│       ├── sample_requests.py         example loan payloads for demo/tests
│       └── rule_catalog.md            plain-English description of each seeded rule
├── tests/
│   ├── engine/                       (A)
│   ├── rules/                        (B)
│   ├── decisions/                    (C)
│   ├── finance/                      (D)
│   └── integration/                  ★ E — full end-to-end tests across modules
└── README.md                         ★ E (skeleton in Phase 0) + everyone adds their section
```

★ marks the primary owner. Read others' folders freely; avoid concurrent
edits inside someone else's folder so merges stay clean.

## 5. Shared Contracts (Phase 0 — build this together first)

Driven by **Contributor E**, with **B** confirming the rule shape and **C**
confirming the decision shape before this is merged. Once merged, treat it as
frozen — changing a shared schema later is a quick heads-up to the other
four, not a solo edit.

### 5.1 Condition JSON grammar (same for every rule)

Logical nodes (handled by the engine core, not pluggable):
```json
{ "type": "AND", "conditions": [ <node>, ... ] }
{ "type": "OR",  "conditions": [ <node>, ... ] }
{ "type": "NOT", "condition": <node> }
```

Leaf nodes (pluggable — one class per type in `engine/evaluators/`):
```json
{ "type": "NUMERIC", "field": "applicant.creditScore", "operator": "GTE", "value": 650 }
{ "type": "STRING",  "field": "applicant.employmentStatus", "operator": "EQUALS", "value": "EMPLOYED" }
{ "type": "BOOLEAN", "field": "riskFlags.hasDefaulted", "operator": "EQUALS", "value": false }
{ "type": "DATE",    "field": "applicant.dateOfBirth", "operator": "ON_OR_BEFORE", "value": "2008-07-24" }
```
`field` is dot-notation into the request JSON. Operators:
- `NUMERIC`: `EQUALS`, `NOT_EQUALS`, `GT`, `GTE`, `LT`, `LTE`
- `STRING`: `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `STARTS_WITH`, `ENDS_WITH`, `IN`, `NOT_IN`
- `BOOLEAN`: `EQUALS`, `NOT_EQUALS`
- `DATE`: `BEFORE`, `AFTER`, `EQUALS`, `ON_OR_BEFORE`, `ON_OR_AFTER` (ISO-8601)

A missing `field` in the request → the leaf evaluates to **not matched**,
never an exception.

### 5.2 `app/schemas/rule.py` (owner: B, agreed in Phase 0)

```python
class RuleCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None          # e.g. "ELIGIBILITY", "RISK", "FRAUD"
    priority: int = 0
    active: bool = True
    condition: dict                       # the JSON tree above
    decision_outcome: str                 # "APPROVE" | "REJECT" | "MANUAL_REVIEW" | custom
    decision_metadata: dict | None = None  # e.g. {"riskTier": "B"}

class RuleUpdate(RuleCreate):
    pass

class RuleOut(RuleCreate):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime
```

### 5.3 `app/schemas/decision.py` (owner: C, agreed in Phase 0)

```python
class EvaluateRequest(BaseModel):
    context: dict                # the loan application payload
    category: str | None = None  # optional: only evaluate rules in this category

class RuleTrace(BaseModel):
    rule_id: int
    rule_name: str
    priority: int
    matched: bool
    decision_outcome: str | None
    explanation: str

class DecisionResponse(BaseModel):
    final_decision: str                  # winning outcome, or "NO_DECISION"
    matched_decisions: list[str]
    explanation: str
    rules_evaluated: list[RuleTrace]
    rules_matched: list[RuleTrace]
    rules_rejected: list[RuleTrace]
    evaluated_at: datetime
```

### 5.4 `app/exceptions.py` + `app/schemas/errors.py` (owner: E)

```python
class RuleNotFoundError(Exception): ...
class InvalidRuleError(Exception): ...
```
Registered in `main.py` via FastAPI exception handlers, mapping to 404 / 400
respectively, with this JSON body:
```json
{ "timestamp": "...", "status": 400, "error": "Bad Request", "message": "...", "path": "/api/rules" }
```

### 5.5 `app/core/database.py` + `app/core/config.py` (owner: E)

- `config.py`: a `pydantic-settings` `Settings` class reading `DATABASE_URL`,
  `LOG_LEVEL`, `APP_ENV` from `.env` / environment variables.
- `database.py`: plain SQLAlchemy `engine` + `SessionLocal` + a `get_db()`
  FastAPI dependency (`yield` a session, close after). SQLite by default
  (`sqlite:///./data/decisions.db`), swapped for Postgres via `DATABASE_URL`
  — no code changes needed, just settings.

**Once these files are merged, Phase 0 is done — everyone branches off this
commit and works in parallel.**

## 6. Module A — Rules Engine Core (`app/engine/`)

**Owns:** turning a condition JSON tree + a request payload into a
matched/not-matched verdict with an explanation. Zero database, zero
FastAPI, zero finance knowledge — pure, independently testable Python.
**No dependency on anyone else — can start immediately.**

- `context.py` — `EvaluationContext` wraps the request `dict`, exposes
  `resolve_field("applicant.creditScore")` (dot-path lookup, returns `None`
  if any part of the path is missing — never raises).
- `result.py` — `EvaluationResult` (dataclass/`NamedTuple`: `matched: bool`, `explanation: str`).
- `base.py` — `ConditionEvaluator` protocol/ABC:
  ```python
  class ConditionEvaluator(Protocol):
      type: ClassVar[str]                                            # e.g. "NUMERIC"
      def evaluate(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult: ...
      def validate(self, condition: dict) -> None: ...               # raise InvalidRuleError if malformed
  ```
- `evaluators/numeric.py`, `string.py`, `boolean.py`, `date.py` — one class
  each, per §5.1's operator lists.
- `registry.py` — `ConditionEvaluatorRegistry`:
  - Built from a plain list: `EVALUATORS: list[ConditionEvaluator] = [NumericConditionEvaluator(), ...]` — no need for auto-discovery magic in Python; a flat registration list is simple and explicit.
  - `evaluate(condition, ctx) -> EvaluationResult` — handles `AND`/`OR`/`NOT`
    directly (evaluate all children, don't short-circuit, so the
    explanation is complete), delegates any other `type` to the matching
    evaluator, raises `InvalidRuleError` on an unknown type.
  - `validate(condition) -> None` — same recursive walk, no request data,
    used when a rule is saved.

**To add a new condition type:** add one file to `evaluators/`, add one line
to the `EVALUATORS` list. Nothing else changes.

**Tests (`tests/engine/`):** one matching + one non-matching + one
missing-field + one invalid-config case per evaluator; AND/OR/NOT
composition and nesting; unknown type raises `InvalidRuleError`.

## 7. Module B — Rule Management & Persistence (`app/rules/`)

**Owns:** everything about storing and managing rules. Depends on Module A
only through `ConditionEvaluatorRegistry.validate()` — import it as a black
box, don't reach into its internals. Depends on Module E for `get_db()` and
the `RuleNotFoundError`/`InvalidRuleError` types.

- `models.py` — SQLAlchemy `Rule` model: `id`, `name`, `description`,
  `category`, `priority` (int), `active` (bool), `condition_json` (Text),
  `decision_outcome` (str), `decision_metadata_json` (Text, nullable),
  `version` (int, incremented on update), `created_at`/`updated_at`.
- `repository.py` — `RuleRepository(db: Session)`: `get(id)`, `list(category=None)`,
  `list_active_ordered_by_priority()`, `create(rule)`, `update(rule)`, `delete(id)`.
  Keep it concrete SQLAlchemy — no generic repository abstraction needed at this scale.
- `service.py` — `RuleService`:
  - `create(payload: RuleCreate) -> RuleOut`: call
    `registry.validate(payload.condition)` **before** persisting; raise
    `InvalidRuleError` (→ 400) if it fails.
  - `update(id, payload)`, `delete(id)`, `get(id)` (raise `RuleNotFoundError`
    → 404 if missing), `list(category=None)`.
  - Serializes `condition`/`decision_metadata` dicts to JSON strings for
    storage, and back to dicts for responses.
- `router.py` — `APIRouter(prefix="/api/rules")`:
  - `GET /` (list, `?category=` filter), `GET /{id}`, `POST /` (201),
    `PUT /{id}`, `PATCH /{id}/active` (body `{"active": true}`), `DELETE /{id}` (204).

**Also owns:** the first Alembic migration (the `rules` table), built on top
of the scaffolding Module E sets up in Phase 0.

**Tests (`tests/rules/`):** CRUD happy paths against a temp SQLite DB;
invalid condition rejected on create/update with a clear message; 404 on
missing id; category filter.

## 8. Module C — Decision Engine & API (`app/decisions/`)

**Owns:** the generic evaluation algorithm and the public decision-making
endpoint — domain-agnostic, no finance-specific content here (that's
Module D). Depends on Module B's `RuleRepository` (read-only) and Module A's
`ConditionEvaluatorRegistry.evaluate()` — both used as black boxes, and both
easily mocked so this module can be built and tested before A or B are
finished.

- `service.py` — `DecisionEngineService`:
  1. `repository.list_active_ordered_by_priority()`, filter by `category` if given.
  2. Wrap `request.context` in an `EvaluationContext`.
  3. For each rule (priority order): parse `condition_json`, call
     `registry.evaluate(...)`; catch `InvalidRuleError`/JSON errors per-rule
     (log it, record as a skipped/rejected trace) — **one broken rule must
     never fail the whole request**.
  4. Split into `matched` / `rejected` traces.
  5. `final_decision` = first matched trace's outcome (list is already
     priority-ordered) or `"NO_DECISION"`.
  6. `matched_decisions` = distinct outcomes across all matches (a request
     can trigger more than one rule at once).
  7. Build one human-readable `explanation` string summarizing the above.
  8. Also provide `evaluate_bulk(requests: list[EvaluateRequest])` for batch use.
- `router.py` — `APIRouter(prefix="/api/decisions")`: `POST /evaluate`, `POST /evaluate/bulk`.

**Tests (`tests/decisions/`):** highest-priority match wins as
`final_decision`; multiple simultaneous matches all reported; no-match →
`"NO_DECISION"`; one malformed stored rule doesn't break evaluation of the
others (mock the repository to return one bad + one good rule).

## 9. Module D — Finance Domain & Demo Content (`app/finance/`)

**Owns:** everything that makes this concretely a *loan/credit* engine
instead of a generic rules engine — without that logic ever leaking into
Modules A/B/C. Depends on Module B's `RuleService` (to seed rules) and
Module C's request/response shapes (to write realistic sample payloads) —
both dependencies are on stable contracts from §5, so this module's own
content (schemas, seed data, sample payloads, documentation) can be written
and reviewed well before B and C are fully wired up; only *running* the seed
script against a live API needs them integrated (Phase 2/3).

- `schemas.py` — **documentation-only** Pydantic model showing the expected
  shape of a loan application context (not enforced by the generic engine —
  this is for API docs, demos, and onboarding clarity):
  ```python
  class LoanApplicationContext(BaseModel):
      applicant: dict     # creditScore, annualIncome, employmentStatus, dateOfBirth, existingCustomer
      loan: dict          # amount, purpose, termMonths
      risk_flags: dict    # hasDefaulted, debtToIncomeRatio
  ```
- `seed_rules.py` — a script/CLI (`python -m app.finance.seed_rules`) that
  inserts 4–6 example rules via `RuleService`, e.g.:
  - "Minimum Credit Score" (`NUMERIC creditScore GTE 650`) → `APPROVE`, priority 10
  - "High Debt-to-Income Flag" (`NUMERIC debtToIncomeRatio GT 0.45`) → `MANUAL_REVIEW`, priority 20
  - "Prior Default Block" (`BOOLEAN hasDefaulted EQUALS true`) → `REJECT`, priority 30
  - "Underage Applicant Block" (`DATE dateOfBirth AFTER <18-years-ago>`) → `REJECT`, priority 40
  - "VIP Existing Customer Fast Track" (`BOOLEAN existingCustomer EQUALS true AND NUMERIC creditScore GTE 700`) → `APPROVE`, priority 25
- `sample_requests.py` — 4–5 example loan application JSON payloads, one per
  scenario above, used in both demo scripts and Module C's/D's tests.
- `rule_catalog.md` — one paragraph per seeded rule in plain English (what
  it checks, why it exists, what outcome it produces) — this is what you
  show a judge/reviewer who wants to understand the demo without reading JSON.

**Tests (`tests/finance/`):** each sample payload run through the seeded
rule set produces the expected `final_decision` (this doubles as the
project's primary demo script).

## 10. Module E — Platform, Infra & Integration (`app/core/`, `docker/`, CI)

**Owns:** everything the other four modules stand on, plus wiring them
together at the end. This is genuinely foundational — deliver the Phase 0
pieces first so nobody else stalls.

- `core/config.py`, `core/database.py`, `core/logging.py` — settings, DB
  session dependency, structured logging setup (standard `logging` module,
  configured once, used everywhere via `logging.getLogger(__name__)`).
- `exceptions.py` + FastAPI exception handlers (in `main.py`) mapping
  `RuleNotFoundError` → 404, `InvalidRuleError` → 400, validation errors →
  400, anything else → 500 with a generic message (full trace logged
  server-side only).
- `main.py` — assembles the app: `include_router()` for rules and decisions,
  registers exception handlers, adds a `GET /health` endpoint.
- `docker/Dockerfile` (multi-stage: builder installs deps, runtime copies
  app + installed packages, non-root user) and `docker/docker-compose.yml`
  (app + Postgres, with a healthcheck).
- `.github/workflows/ci.yml` — run `pytest` (and optionally `ruff`/`black
  --check`) on every push/PR.
- **Phase 2 integration pass:** once A/B/C/D branches are merged, verify
  `main.py` wires everything correctly, run the full test suite, and write
  `tests/integration/test_end_to_end.py` — seed the finance rules, POST a
  sample loan payload to `/api/decisions/evaluate`, assert the expected
  decision and a populated trace.
- `README.md` skeleton in Phase 0 (project overview, run instructions); each
  other contributor adds their module's section later.

**Tests:** `tests/integration/` (end-to-end, depends on everyone else's
merged work) plus basic tests for exception handler mapping and `/health`.

## 11. Dependency Graph (who blocks on whom)

```
E (platform/infra)  ──────────────┐
   │ (config, db, exceptions)     │
   ▼                              ▼
A (engine)  ── validate/evaluate ─▶  B (rules)  ── repository ─▶  C (decisions)
                                                                       │
                                                          seed via ────┘
                                                          RuleService
                                                                       ▼
                                                                  D (finance)
```

- **A has no dependencies** — start immediately, fully unit-testable in isolation.
- **E's Phase-0 deliverables (config/db/exceptions) should land first**, since B and C both need `get_db()` and the exception types — but E can hand over stub versions on day one and refine them without blocking anyone.
- **B depends on A's contract only** (`registry.validate(condition)`) — use a stub (`lambda c: None`) until A's real registry lands.
- **C depends on B's and A's contracts only** (`repository.list_active_ordered_by_priority()`, `registry.evaluate(...)`) — mock both in tests until they're ready.
- **D depends on B's and C's contracts** (`RuleService`, the request/response shapes) — write schemas/sample data/docs immediately; the seed script's actual *execution* waits for B+C to be mergeable, which is fine since that only happens in Phase 2/3 anyway.
- **E does the final integration pass** after A/B/C/D are merged.

Everyone can be productive from day one; only D's "run the seed script for
real" step and E's integration pass genuinely wait on others.

## 12. Incremental Commit & Branch Plan

Ship gradually — small PRs, not one giant commit per module.

**Phase 0 — `chore/scaffold` (E drives, B and C review their schema, ~1 short session)**
1. `chore: project scaffold (pyproject, docker, .env.example, CI skeleton)`
2. `feat: core config, database session, logging setup`
3. `feat: shared schemas (rule, decision, errors) + exception handlers`

Merge to `main` before Phase 1 branches start.

**Phase 1 — one branch per contributor, several small commits each, all in parallel**

*A — `feat/engine-core`*
1. `feat(engine): EvaluationContext + EvaluationResult`
2. `feat(engine): ConditionEvaluator base + numeric evaluator`
3. `feat(engine): string, boolean, date evaluators`
4. `feat(engine): registry with AND/OR/NOT dispatch + validate()`
5. `test(engine): evaluator + registry unit tests`

*B — `feat/rules-module`*
1. `feat(rules): SQLAlchemy Rule model + Alembic migration`
2. `feat(rules): RuleRepository`
3. `feat(rules): RuleService (CRUD + validation hook, stubbed registry)`
4. `feat(rules): rules router (/api/rules)`
5. `test(rules): CRUD + validation tests`

*C — `feat/decisions-module`*
1. `feat(decisions): DecisionEngineService against a mocked repository + registry`
2. `feat(decisions): decisions router (/evaluate, /evaluate/bulk)`
3. `test(decisions): evaluation algorithm tests`

*D — `feat/finance-domain`*
1. `feat(finance): LoanApplicationContext documentation schema`
2. `feat(finance): seed_rules script with 5 example rules`
3. `feat(finance): sample_requests + rule_catalog.md`
4. `test(finance): sample payloads produce expected decisions (against mocks initially)`

*E — `feat/platform-hardening`* (in parallel with the above, after Phase 0 lands)
1. `feat(platform): dockerfile + docker-compose`
2. `feat(platform): CI workflow running pytest`
3. `feat(platform): /health endpoint + structured logging polish`

Each of these is its own small PR, reviewed by at least one other
contributor, merged into `main` as soon as its own tests pass — the five
branches don't need to land in any particular order except that Phase 0 must
land first.

**Phase 2 — `chore/integration` (E drives, small commits)**
1. `chore: wire routers + exception handlers in main.py`
2. `fix: resolve interface mismatches surfaced by integration (replace stubs/mocks with real A/B/C wiring)`
3. `test: end-to-end test — seed finance rules, hit /evaluate, assert response`

**Phase 3 — polish (split across all five, still small commits)**
1. `docs: README sections from each contributor`
2. `docs: rule_catalog.md finalized with real demo scenarios`
3. `chore: logging pass on rule CRUD + evaluation`
4. `test: bump coverage on any thin spots found during integration`

**Rule of thumb:** if a commit touches more than one module's folder, stop —
that's a sign a shared contract in §5 needs a quick update (with a heads-up
to the other four) rather than a workaround inside your own module.

## 13. Project Setup

### 13.1 Prerequisites

- Python 3.12+
- Docker + Docker Compose (only needed for the Postgres path)
- `pip` or `poetry` (either works; instructions below use `pip`)

### 13.2 Clone and install

```bash
git clone <repo-url>
cd finance-decision-engine
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # or: poetry install
```

### 13.3 Configure environment

```bash
cp .env.example .env
```

`.env` contents and what they control (all read by `app/core/config.py`):

| Variable | Default (SQLite path) | Used for |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/decisions.db` | DB connection string — swap to a Postgres URL for the Docker path |
| `LOG_LEVEL` | `INFO` | root logging level |
| `APP_ENV` | `local` | environment tag, shows up in logs |

Don't commit `.env` — only `.env.example` is tracked.

### 13.4 Option A — run locally against SQLite (fastest, zero external services)

```bash
mkdir -p data
alembic upgrade head                      # creates the rules table
uvicorn app.main:app --reload
```
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: `curl http://localhost:8000/health`

Load the example finance rules once the server (or at least the DB) exists:
```bash
python -m app.finance.seed_rules
```

Verify it worked:
```bash
curl http://localhost:8000/api/rules            # should list the seeded rules
curl -X POST http://localhost:8000/api/decisions/evaluate \
  -H "Content-Type: application/json" \
  -d @app/finance/sample_requests.json          # or paste one sample payload inline
```

### 13.5 Option B — run with Docker + Postgres (shared/integration setup)

```bash
docker compose -f docker/docker-compose.yml up --build
```
This starts a `postgres` service and the `app` service (pointed at it via
`DATABASE_URL`, wired in `docker-compose.yml` — you don't need to edit `.env`
for this path). On first run, the app container should apply migrations
automatically on startup (`alembic upgrade head` as part of the container's
entrypoint/`main.py` startup event) — confirm this is wired before relying
on it; otherwise run migrations manually:
```bash
docker compose -f docker/docker-compose.yml exec app alembic upgrade head
docker compose -f docker/docker-compose.yml exec app python -m app.finance.seed_rules
```

Verify the same way as Option A, just against the same `localhost:8000`.

**Shared Postgres etiquette:** if you're all pointing at one running Postgres
instance (rather than each spinning up your own via compose), only one
person applies migrations first (`alembic upgrade head`); everyone else
pulls schema changes through migrations, never runs `create_all`/manual DDL
against the shared DB, and coordinates before dropping/recreating it.

### 13.6 Running tests

```bash
pytest                    # everything
pytest tests/engine       # just Module A
pytest tests/rules        # just Module B
pytest tests/decisions    # just Module C
pytest tests/finance      # just Module D
pytest tests/integration  # end-to-end (needs a DB — SQLite is fine for this)
```

### 13.7 Common first-run issues

| Symptom | Likely cause |
|---|---|
| `sqlalchemy.exc.OperationalError: no such table: rules` | forgot `alembic upgrade head` |
| Rules API returns empty list | forgot to run `seed_rules` |
| `ModuleNotFoundError: app` | run commands from the repo root, not inside `app/` |
| Docker app container can't reach Postgres | Postgres healthcheck hasn't passed yet — compose should wait on `depends_on: condition: service_healthy`, but give it a few seconds on first boot (image pull + init) |

## 14. Acceptance Checklist

- [ ] `pytest` passes across `tests/engine`, `tests/rules`, `tests/decisions`, `tests/finance`, `tests/integration`
- [ ] `uvicorn app.main:app --reload` runs against SQLite with zero external setup
- [ ] `/docs` (Swagger UI) shows `Rules` and `Decisions` endpoint groups
- [ ] Creating a rule with an unknown condition `type` → 400 with a message naming supported types
- [ ] Seeded finance rules + a sample loan payload → correct `final_decision`, full trace in the response
- [ ] A request matching nothing → `"NO_DECISION"` with populated `rules_rejected`
- [ ] Reading/deleting a non-existent rule id → 404 with the structured error body
- [ ] `docker compose up --build` runs app + Postgres end-to-end
- [ ] CI runs `pytest` on every push/PR
- [ ] Adding a new leaf condition type touches exactly one new file in `engine/evaluators/` plus one line in `registry.py`
- [ ] `rule_catalog.md` reads clearly to someone who has never seen the JSON rule format
