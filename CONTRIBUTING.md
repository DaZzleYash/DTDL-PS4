# Contributing Guide

## Getting Started

1. Clone the repo and follow [README.md](README.md) setup instructions.
2. Read the full build spec (shared with the team).
3. Find your module folder — each has a `README.md` listing your deliverables.
4. Create your Phase 1 branch from `main` after Phase 0 is merged.

## Module Boundaries

**Do not edit another contributor's folder.** Read freely, but keep changes scoped to your module (plus shared contracts in `app/schemas/` during Phase 0 only).

If you need to change a shared schema after Phase 0, notify all four other contributors before merging.

## Commit Conventions

Use conventional commits with module scope:

```
feat(engine): add numeric condition evaluator
feat(rules): SQLAlchemy Rule model + Alembic migration
test(decisions): highest-priority match wins
chore: wire routers in main.py
```

Keep commits small — one logical unit per commit. If a commit touches more than one module folder, stop and check whether a shared contract update is needed.

## Pull Request Workflow

1. Branch from `main`: `feat/<module-name>`
2. Write tests in your module's `tests/` folder
3. Ensure `pytest` and `ruff check app tests` pass locally
4. Open a PR — get at least one review from another contributor
5. Merge to `main` as soon as your tests pass (no strict ordering in Phase 1)

## Shared Contracts (Phase 0 — Frozen After Merge)

| File | Owner | Purpose |
|---|---|---|
| `app/schemas/rule.py` | B | Rule CRUD shapes |
| `app/schemas/decision.py` | C | Evaluation request/response |
| `app/schemas/errors.py` | E | Standard error body |
| `app/exceptions.py` | E | Domain exceptions |
| `app/core/config.py` | E | Settings |
| `app/core/database.py` | E | DB session dependency |

## Dependency Stubs

Until other modules land, use mocks/stubs in tests:

- **B** can stub `registry.validate` as `lambda c: None` until A's registry is ready
- **C** can mock `RuleRepository` and `ConditionEvaluatorRegistry` in tests
- **D** can write schemas and sample data immediately; seed script execution waits for B+C

## Questions?

Tag the module owner in your PR or team chat.
