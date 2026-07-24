"""
Rule Management & Persistence — owned by Contributor B.

Depends on: Module A (registry.validate), Module E (get_db, exceptions).

Deliverables:
  - app/rules/models.py         SQLAlchemy Rule model
  - app/rules/repository.py     RuleRepository
  - app/rules/service.py        RuleService (CRUD + validation)
  - app/rules/router.py         /api/rules endpoints
  - alembic/versions/           first migration (rules table)

Branch: feat/rules-module
Tests:  tests/rules/
"""
