# Finance Rule Catalog

Plain-English descriptions of the seeded demo rules. Use this when walking a
reviewer through the loan decisioning demo without reading condition JSON.

## 1. Minimum Credit Score

**Category:** ELIGIBILITY · **Priority:** 10 · **Outcome:** APPROVE

Requires the applicant's credit score (`applicant.creditScore`) to be at least
650. This is the primary "pass" gate for a straightforward approval. Because
priority 10 is the lowest number in the seed set, it wins `final_decision`
whenever it matches — even if later rules (VIP, DTI flag) also match.

## 2. High Debt-to-Income Flag

**Category:** RISK · **Priority:** 20 · **Outcome:** MANUAL_REVIEW

Fires when `risk_flags.debtToIncomeRatio` is greater than 0.45. High leverage
is not an automatic rejection, but a human underwriter should look at the
application. In the demo, use a credit score below 650 so this rule becomes
the winning `final_decision` instead of Minimum Credit Score.

## 3. VIP Existing Customer Fast Track

**Category:** ELIGIBILITY · **Priority:** 25 · **Outcome:** APPROVE

Matches when the applicant is already a customer (`applicant.existingCustomer`
is true) **and** their credit score is at least 700. Both conditions must hold
(AND). In practice this often fires alongside Minimum Credit Score; the VIP
match still appears in `rules_matched` / `matched_decisions` even when
Minimum Credit Score wins `final_decision`.

## 4. Prior Default Block

**Category:** FRAUD · **Priority:** 30 · **Outcome:** REJECT

Rejects any application where `risk_flags.hasDefaulted` is true. Previous
defaults are treated as a hard stop. Demo payloads that showcase this outcome
keep credit score below 650 and DTI at or under 0.45 so earlier rules do not
steal the win.

## 5. Underage Applicant Block

**Category:** ELIGIBILITY · **Priority:** 40 · **Outcome:** REJECT

Rejects applicants whose `applicant.dateOfBirth` is **after** the date
eighteen years before seed time (i.e. they are under 18). The cutoff date is
computed when `seed_rules` runs, so re-seeding on a later day keeps the rule
current. Demo payloads use a 16-year-old DOB and a sub-650 credit score so
this rule is the first match.
