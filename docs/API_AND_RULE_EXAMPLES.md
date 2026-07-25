# API & Rule Examples — Finance Decision Engine

Reference for hackathon demos, jury review, and frontend integration. All examples match the **seeded demo rules** (`python -m app.finance.seed_rules`).

---

## 1. Rule categories (at least 3 in the demo set)

Rules are grouped by `category`. The decision engine can evaluate **all categories** or filter to one.

| Category | Purpose | Demo rules | Typical outcome |
|----------|---------|------------|-----------------|
| **ELIGIBILITY** | Can this applicant qualify? | Minimum Credit Score, VIP Fast Track, Underage Block | `APPROVE` or `REJECT` |
| **RISK** | Does the profile need human review? | High Debt-to-Income Flag | `MANUAL_REVIEW` |
| **FRAUD** | Hard stops for bad history | Prior Default Block | `REJECT` |

**Priority rule:** Lower `priority` number wins. If rule priority `10` and `20` both match, `final_decision` comes from priority `10`.

---

## 2. Rules by category (full JSON)

### Category: ELIGIBILITY

#### Rule A — Minimum Credit Score (priority 10)

```jsonc
{
  // POST /api/rules/ — create a new rule
  "name": "Minimum Credit Score",
  "description": "Approve applicants whose credit score is at least 650.",
  "category": "ELIGIBILITY",           // only ELIGIBILITY rules when category filter is used
  "priority": 10,                      // lowest number = checked first; wins if matched
  "active": true,
  "condition": {
    "type": "NUMERIC",                 // compares a number field
    "field": "applicant.creditScore",  // dot path into loan context
    "operator": "GTE",                 // greater than or equal
    "value": 650
  },
  "decision_outcome": "APPROVE",       // returned when condition matches
  "decision_metadata": { "riskTier": "A" }
}
```

#### Rule B — VIP Existing Customer Fast Track (priority 25)

```jsonc
{
  "name": "VIP Existing Customer Fast Track",
  "description": "Fast-track existing customers with credit score 700+.",
  "category": "ELIGIBILITY",
  "priority": 25,
  "active": true,
  "condition": {
    "type": "AND",                     // all nested conditions must match
    "conditions": [
      {
        "type": "BOOLEAN",
        "field": "applicant.existingCustomer",
        "operator": "EQUALS",
        "value": true
      },
      {
        "type": "NUMERIC",
        "field": "applicant.creditScore",
        "operator": "GTE",
        "value": 700
      }
    ]
  },
  "decision_outcome": "APPROVE",
  "decision_metadata": { "fastTrack": true }
}
```

#### Rule C — Underage Applicant Block (priority 40)

```jsonc
{
  "name": "Underage Applicant Block",
  "description": "Reject applicants under 18 years old.",
  "category": "ELIGIBILITY",
  "priority": 40,
  "active": true,
  "condition": {
    "type": "DATE",
    "field": "applicant.dateOfBirth",
    "operator": "AFTER",               // DOB after cutoff = under 18
    "value": "2008-07-25"              // computed at seed time; changes when re-seeded
  },
  "decision_outcome": "REJECT",
  "decision_metadata": { "reason": "underage" }
}
```

---

### Category: RISK

#### Rule D — High Debt-to-Income Flag (priority 20)

```jsonc
{
  "name": "High Debt-to-Income Flag",
  "description": "Flag applications where DTI exceeds 45% for manual review.",
  "category": "RISK",
  "priority": 20,
  "active": true,
  "condition": {
    "type": "NUMERIC",
    "field": "risk_flags.debtToIncomeRatio",  // 0.45 = 45%
    "operator": "GT",
    "value": 0.45
  },
  "decision_outcome": "MANUAL_REVIEW",
  "decision_metadata": { "reason": "high_dti" }
}
```

---

### Category: FRAUD

#### Rule E — Prior Default Block (priority 30)

```jsonc
{
  "name": "Prior Default Block",
  "description": "Reject applicants who have previously defaulted.",
  "category": "FRAUD",
  "priority": 30,
  "active": true,
  "condition": {
    "type": "BOOLEAN",
    "field": "risk_flags.hasDefaulted",
    "operator": "EQUALS",
    "value": true
  },
  "decision_outcome": "REJECT",
  "decision_metadata": { "reason": "prior_default" }
}
```

---

## 3. Loan application context (input shape)

Every evaluation needs a `context` object. This is the loan JSON the engine reads via dot paths (`applicant.creditScore`, etc.).

```jsonc
{
  // --- Applicant profile ---
  "applicant": {
    "creditScore": 720,              // FICO-style score; used by ELIGIBILITY rules
    "annualIncome": 85000,
    "employmentStatus": "EMPLOYED",  // EMPLOYED | SELF_EMPLOYED | UNEMPLOYED
    "dateOfBirth": "1996-07-25",     // ISO-8601 date string
    "existingCustomer": false        // true triggers VIP rule when score >= 700
  },

  // --- Loan being requested ---
  "loan": {
    "amount": 25000,
    "purpose": "AUTO",               // AUTO | HOME | PERSONAL | EDUCATION
    "termMonths": 60
  },

  // --- Risk signals ---
  "risk_flags": {
    "hasDefaulted": false,           // true triggers FRAUD reject rule
    "debtToIncomeRatio": 0.30        // 0.30 = 30%; > 0.45 triggers RISK manual review
  }
}
```

Copy-paste file: [`docs/examples/01-loan-context.jsonc`](examples/01-loan-context.jsonc)

---

## 4. Evaluate request & response examples

**Endpoint:** `POST /api/decisions/evaluate`

### Example 1 — Good applicant → APPROVE (ELIGIBILITY)

**Request**

```jsonc
{
  "context": {
    "applicant": {
      "creditScore": 720,
      "annualIncome": 85000,
      "employmentStatus": "EMPLOYED",
      "dateOfBirth": "1996-07-25",
      "existingCustomer": false
    },
    "loan": { "amount": 25000, "purpose": "AUTO", "termMonths": 60 },
    "risk_flags": { "hasDefaulted": false, "debtToIncomeRatio": 0.30 }
  },
  "category": null   // null = evaluate ALL active rules; or "ELIGIBILITY" | "RISK" | "FRAUD"
}
```

**Response** (`200 OK`)

```jsonc
{
  "final_decision": "APPROVE",       // winning outcome (lowest priority match)
  "matched_decisions": ["APPROVE"],  // unique outcomes from all matched rules
  "explanation": "Final decision: APPROVE (highest-priority match: 'Minimum Credit Score', priority 10).",
  "rules_matched": [
    {
      "rule_id": 1,
      "rule_name": "Minimum Credit Score",
      "priority": 10,
      "matched": true,
      "decision_outcome": "APPROVE",
      "explanation": "applicant.creditScore (720.0) >= 650.0 — matched"
    }
  ],
  "rules_rejected": [ /* other 4 rules with matched: false */ ],
  "rules_evaluated": [ /* all 5 rules in priority order */ ],
  "evaluated_at": "2026-07-25T02:00:00+00:00"
}
```

---

### Example 2 — High DTI → MANUAL_REVIEW (RISK)

Credit score is **600** (below 650) so the ELIGIBILITY approve rule does **not** win first.

**Request**

```jsonc
{
  "context": {
    "applicant": {
      "creditScore": 600,
      "annualIncome": 85000,
      "employmentStatus": "EMPLOYED",
      "dateOfBirth": "1996-07-25",
      "existingCustomer": false
    },
    "loan": { "amount": 40000, "purpose": "PERSONAL", "termMonths": 60 },
    "risk_flags": { "hasDefaulted": false, "debtToIncomeRatio": 0.55 }
  },
  "category": null
}
```

**Response** (`200 OK`)

```jsonc
{
  "final_decision": "MANUAL_REVIEW",
  "matched_decisions": ["MANUAL_REVIEW"],
  "explanation": "Final decision: MANUAL_REVIEW (highest-priority match: 'High Debt-to-Income Flag', priority 20).",
  "rules_matched": [
    {
      "rule_name": "High Debt-to-Income Flag",
      "priority": 20,
      "matched": true,
      "decision_outcome": "MANUAL_REVIEW",
      "explanation": "risk_flags.debtToIncomeRatio (0.55) > 0.45 — matched"
    }
  ]
}
```

---

### Example 3 — Prior default → REJECT (FRAUD)

**Request**

```jsonc
{
  "context": {
    "applicant": {
      "creditScore": 600,
      "annualIncome": 85000,
      "employmentStatus": "EMPLOYED",
      "dateOfBirth": "1996-07-25",
      "existingCustomer": false
    },
    "loan": { "amount": 25000, "purpose": "PERSONAL", "termMonths": 60 },
    "risk_flags": { "hasDefaulted": true, "debtToIncomeRatio": 0.30 }
  },
  "category": null
}
```

**Response** (`200 OK`)

```jsonc
{
  "final_decision": "REJECT",
  "matched_decisions": ["REJECT"],
  "explanation": "Final decision: REJECT (highest-priority match: 'Prior Default Block', priority 30).",
  "rules_matched": [
    {
      "rule_name": "Prior Default Block",
      "priority": 30,
      "matched": true,
      "decision_outcome": "REJECT",
      "explanation": "risk_flags.hasDefaulted (True) EQUALS True — matched"
    }
  ]
}
```

---

### Example 4 — Category filter (ELIGIBILITY only)

Only rules in `ELIGIBILITY` are evaluated; RISK and FRAUD rules are skipped.

**Request**

```jsonc
{
  "context": {
    "applicant": { "creditScore": 600, "hasDefaulted": false },
    "risk_flags": { "hasDefaulted": true, "debtToIncomeRatio": 0.55 }
  },
  "category": "ELIGIBILITY"   // filter: ignore RISK + FRAUD rules
}
```

**Response** — `final_decision` is `"NO_DECISION"` if no ELIGIBILITY rule matches.

---

### Example 5 — No rule matches → NO_DECISION

**Request**

```jsonc
{
  "context": {
    "applicant": { "creditScore": 400 },
    "loan": { "amount": 1000 },
    "risk_flags": { "hasDefaulted": false, "debtToIncomeRatio": 0.10 }
  }
}
```

**Response**

```jsonc
{
  "final_decision": "NO_DECISION",
  "matched_decisions": [],
  "explanation": "No rules matched. Evaluated 5 active rule(s).",
  "rules_matched": [],
  "rules_rejected": [ /* all rules with matched: false */ ]
}
```

---

## 5. Bulk evaluate

**Endpoint:** `POST /api/decisions/evaluate/bulk`

Send an **array** of evaluate requests; get an **array** of decision responses (same order).

```jsonc
[
  {
    // Request 1 — good applicant
    "context": {
      "applicant": { "creditScore": 720, "dateOfBirth": "1996-07-25", "existingCustomer": false },
      "loan": { "amount": 25000, "purpose": "AUTO", "termMonths": 60 },
      "risk_flags": { "hasDefaulted": false, "debtToIncomeRatio": 0.30 }
    }
  },
  {
    // Request 2 — high DTI
    "context": {
      "applicant": { "creditScore": 600, "dateOfBirth": "1996-07-25", "existingCustomer": false },
      "loan": { "amount": 40000, "purpose": "PERSONAL", "termMonths": 60 },
      "risk_flags": { "hasDefaulted": false, "debtToIncomeRatio": 0.55 }
    }
  }
]
```

**Response:** `[ { "final_decision": "APPROVE", ... }, { "final_decision": "MANUAL_REVIEW", ... } ]`

---

## 6. Rule API structures

### Create rule — `POST /api/rules/`

Body uses the same shape as section 2. Response adds server fields:

```jsonc
{
  "id": 1,
  "name": "Minimum Credit Score",
  "category": "ELIGIBILITY",
  "priority": 10,
  "active": true,
  "condition": { "type": "NUMERIC", "field": "applicant.creditScore", "operator": "GTE", "value": 650 },
  "decision_outcome": "APPROVE",
  "decision_metadata": { "riskTier": "A" },
  "version": 1,
  "created_at": "2026-07-25T02:00:00",
  "updated_at": "2026-07-25T02:00:00"
}
```

### List rules — `GET /api/rules/?category=RISK`

Returns an array of rule objects. Optional query param `category` filters by category.

### Error response — `400` / `404`

```jsonc
{
  "timestamp": "2026-07-25T02:00:00",
  "status": 400,
  "error": "Invalid Rule",
  "message": "Unknown condition type: UNKNOWN",
  "path": "/api/rules/"
}
```

---

## 7. Condition types (engine JSON)

```jsonc
{
  // NUMERIC — field must resolve to a number
  "type": "NUMERIC",
  "field": "applicant.creditScore",
  "operator": "GTE",    // GT | GTE | LT | LTE | EQ
  "value": 650

  // BOOLEAN
  "type": "BOOLEAN",
  "field": "risk_flags.hasDefaulted",
  "operator": "EQUALS", // EQUALS only
  "value": true

  // DATE — value is ISO date string
  "type": "DATE",
  "field": "applicant.dateOfBirth",
  "operator": "AFTER",  // BEFORE | AFTER | EQUALS | ON_OR_BEFORE | ON_OR_AFTER
  "value": "2008-07-25"

  // AND — combine conditions (all must match)
  "type": "AND",
  "conditions": [ /* array of condition objects */ ]
}
```

Full reference file: [`docs/examples/02-condition-types.jsonc`](examples/02-condition-types.jsonc)

---

## 8. Quick curl commands

```bash
# Seed demo rules first
python -m app.finance.seed_rules

# Evaluate a good applicant
curl -X POST http://localhost:8000/api/decisions/evaluate \
  -H "Content-Type: application/json" \
  -d @docs/examples/03-evaluate-approve.json

# List RISK rules only
curl "http://localhost:8000/api/rules/?category=RISK"
```

---

## 9. Related files

| File | Purpose |
|------|---------|
| `app/finance/seed_rules.py` | Source of truth for demo rules |
| `app/finance/sample_requests.py` | Programmatic demo payloads |
| `app/finance/rule_catalog.md` | Plain-English rule descriptions |
| `docs/examples/` | Copy-paste JSON/JSONC samples |
