# Phase 7 — Pilot Validation Metrics Contract

## Purpose

Pilot metrics quantify actual activation, engagement, reliability, commercial,
and support outcomes without treating projections as business-data authority.

## Canonical Metric Families

### Activation

- organizations created
- stores activated
- first transaction completed
- time to first sale

### Engagement

- weekly active merchants
- orders per merchant
- POS transactions
- Commerce transactions
- active branches

### Reliability

- successful checkout rate
- correct order-state rate
- payment reconciliation
- inventory accuracy
- API error rate

### Commercial

- paying merchants
- trial-to-paid conversion
- monthly recurring revenue
- churn
- willingness to continue

### Support

- tickets per merchant
- first response time
- resolution time
- engineering interventions

## Pilot Exit Gate

Canonical PASS requires:

- at least 5 merchants onboarded
- at least 70% transact weekly
- at least 80% reach first sale within 24 hours
- at least 90% of orders reach correct final state
- payment reconciliation >= 99.5%
- inventory accuracy >= 98%
- at least 3 merchants want to continue
- at least 2 merchants are willing to pay
- no critical cross-tenant exposure

The weekly activity measurement window must cover at least seven days.

## Controlled Capacity

The active Public MVP cap remains:

- organizations <= 100
- POS branches <= 250
- monthly orders <= 10,000

Capacity violations fail closed and do not authorize automatic expansion.

## Integrity

Metric snapshots store integer counters and derive rates deterministically.

Invalid numerator/denominator relationships fail closed.

No snapshot may claim pilot exit without recorded onboarding evidence.
