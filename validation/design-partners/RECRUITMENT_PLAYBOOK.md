# Phase 7 — Merchant Discovery Recruitment Playbook

## Target

Phase 7 requires:

- 20–30 discovery interviews
- 5–10 design partner commitments
- minimum 3 active pilot merchants
- at least 80% core-problem confirmation

## Who to Recruit

Prioritize merchants with:

- active retail operations
- real inventory
- real customers
- recurring transaction volume
- a willingness to test Commerce and/or POS
- willingness to provide structured feedback

Good initial segments:

- clothing/fashion retailers
- convenience/general dealers
- salons/barbers with retail stock
- phone/accessory shops
- small supermarkets
- hardware/building-supply stores
- auto-parts retailers
- restaurants/takeaway businesses using POS
- service businesses that also sell stock

## Recruitment Rule

Do not pitch Dalizebo as already proven.

The goal is to learn whether the merchant has a material problem worth solving.

Avoid leading questions such as:

- "Wouldn't an all-in-one system be better?"
- "Would you pay for Dalizebo?"
- "Don't you hate your current POS?"

Prefer behavioral questions:

- "How do you currently record sales?"
- "How do you know what stock is available?"
- "What happens when stock counts are wrong?"
- "How do you reconcile cash/card payments?"
- "What causes the most repeated admin work?"

## Recruitment Message

Use a short personal invitation:

> I'm researching how local retailers handle sales, stock, customers and
> payments. I'm not selling anything during the interview. I need 15–20 minutes
> to understand what works, what causes problems, and what you would improve.

Do not promise funding, free hardware, guaranteed revenue, or future product
features.

## Evidence

After each actual interview run:

```bash
python scripts/phase7-evidence-collect.py validate-inbox
python scripts/phase7-evidence-collect.py ingest-inbox
python scripts/phase7-evidence-collect.py progress
```

Only real interviews may use `REAL_MERCHANT`.
