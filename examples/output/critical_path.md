# Critical Path — Nimbus Expense: Multi-Currency & Delegate Approvals

- Start date: **2026-08-03** (rolled to nearest business day)
- Finish date: **2026-08-20** (13 business days)

## Velocity assumptions

| Team | Points/day |
|---|---|
| Backend Eng | 2 |
| Finance Eng | 1.5 |
| Mobile Eng | 2 |
| Platform Eng | 1.5 |
| Web Eng | 2.5 |
| default | 2 |

These are assumptions, not measured facts — sanity-check them against real team velocity before treating the finish date above as a commitment.

## Critical path

- EPIC-2-1 (Build shared approval-resolution service for normal and delegate routing, 6d) → EPIC-2-3 (Store delegation records with auto-expiry at end of date range, 3d) → EPIC-3-4 (Extend notification service for delegation lifecycle events, 4d)

## Near-critical watch list (slack ≤ 3 business days)

| Task | Summary | Slack (days) |
|---|---|---|
| EPIC-1-1 | Extend expense data model & API to store original currency, amount, and FX rate used | 2 |
| EPIC-1-2 | Integrate with existing Finance Reporting FX rate service client | 2 |
| EPIC-1-3 | Add async conversion fallback for when the FX provider is unavailable | 2 |
| EPIC-1-8 | Allow approvers to approve on original amount before conversion is backfilled | 2 |
| EPIC-2-4 | Delegate's approval queue shows delegated-from expenses | 2 |
| EPIC-2-5 | Record both delegate (actor) and original approver (authority) on approval | 2 |
| EPIC-3-1 | Extend audit log schema with an optional 'acted as delegate for' field | 2 |
| EPIC-3-2 | Write delegated-approval audit entries using the extended schema | 2 |
| EPIC-3-3 | Audit log view: filter/search delegated-approval entries | 2 |
| EPIC-5-3 | Update export attribution logic for delegated approvals per compliance decision | 2 |
| EPIC-4-2 | Admin view: list active delegations org-wide | 3 |

## Cross-team handoffs

16 cross-team dependency edges total, 2 of them directly on the critical path. See `risk_register.md` for the full list.

