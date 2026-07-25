# Module D — Finance Domain & Demo Content

Owned by **Contributor D**.

Depends on: Module B (`RuleService`), Module C (request/response shapes from §5).

## Deliverables

| File | Purpose |
|---|---|
| `app/finance/schemas.py` | `LoanApplicationContext` documentation model |
| `app/finance/seed_rules.py` | CLI to insert 7 example rules (`python -m app.finance.seed_rules`) |
| `app/finance/sample_requests.py` | Demo loan payloads + expected decisions |
| `app/finance/rule_catalog.md` | Plain-English description of each seeded rule |
| `docs/API_AND_RULE_EXAMPLES.md` | Category-wise rules, request/response examples, JSON reference |
| `docs/examples/` | Copy-paste JSON/JSONC payloads for curl and Postman |

## Branch / commits

Branch: `feat/finance-domain`

1. `feat(finance): LoanApplicationContext documentation schema`
2. `feat(finance): seed_rules script with 5 example rules`
3. `feat(finance): sample_requests + rule_catalog.md`
4. `test(finance): sample payloads produce expected decisions`

## Run

```bash
# after alembic upgrade head (and preferably with the API up)
python -m app.finance.seed_rules

pytest tests/finance
```
