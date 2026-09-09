# Phase 7 — Durable Pilot Onboarding Event Evidence

Adds durable `PILOT_ONBOARDING_EVENT` evidence so Gate 3 can later reconstruct
completed onboarding and first-sale-within-24h from real step evidence.

Safeguards:
- links only to an ingested real `PILOT_ONBOARDING`
- merchant identity is inherited from onboarding evidence
- canonical `OnboardingEvent.validate()` is enforced
- evidence origin is `REAL_MERCHANT`
- no onboarding completion, Gate 3 PASS, or Phase 8 claim is made
