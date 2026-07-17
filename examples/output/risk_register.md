# Dependency Risk Register — Nimbus Expense: Multi-Currency & Delegate Approvals

Every dependency edge that crosses a team boundary, ranked by schedule risk.

| From (team) | To (team) | Status | Slack | Risk |
|---|---|---|---|---|
| EPIC-2-1 (Platform Eng) → EPIC-2-3 (Backend Eng) | Build shared approval-resolution service for normal and delegate routing → Store delegation records with auto-expiry at end of date range | on critical path | 0d | medium |
| EPIC-2-3 (Backend Eng) → EPIC-3-4 (Platform Eng) | Store delegation records with auto-expiry at end of date range → Extend notification service for delegation lifecycle events | on critical path | 0d | medium |
| EPIC-2-1 (Platform Eng) → EPIC-2-2 (Web Eng) | Build shared approval-resolution service for normal and delegate routing → Approver UI to designate a delegate and date range | near-critical | 0d | low |
| EPIC-2-1 (Platform Eng) → EPIC-2-4 (Web Eng) | Build shared approval-resolution service for normal and delegate routing → Delegate's approval queue shows delegated-from expenses | near-critical | 0d | low |
| EPIC-2-3 (Backend Eng) → EPIC-2-4 (Web Eng) | Store delegation records with auto-expiry at end of date range → Delegate's approval queue shows delegated-from expenses | near-critical | 0d | low |
| EPIC-2-1 (Platform Eng) → EPIC-2-5 (Backend Eng) | Build shared approval-resolution service for normal and delegate routing → Record both delegate (actor) and original approver (authority) on approval | near-critical | 0d | medium |
| EPIC-2-3 (Backend Eng) → EPIC-4-2 (Web Eng) | Store delegation records with auto-expiry at end of date range → Admin view: list active delegations org-wide | near-critical | 0d | low |
| EPIC-1-1 (Backend Eng) → EPIC-1-4 (Web Eng) | Extend expense data model & API to store original currency, amount, and FX rate used → Add currency selector and local-currency amount entry to web submission form | near-critical | 2d | low |
| EPIC-1-1 (Backend Eng) → EPIC-1-5 (Mobile Eng) | Extend expense data model & API to store original currency, amount, and FX rate used → Add currency selector and local-currency amount entry to mobile submission form | near-critical | 2d | low |
| EPIC-1-2 (Backend Eng) → EPIC-1-6 (Web Eng) | Integrate with existing Finance Reporting FX rate service client → Show original and converted amount on web expense list/detail views | near-critical | 2d | low |
| EPIC-1-2 (Backend Eng) → EPIC-1-7 (Mobile Eng) | Integrate with existing Finance Reporting FX rate service client → Show original and converted amount on mobile expense list/detail views | near-critical | 2d | low |
| EPIC-3-1 (Platform Eng) → EPIC-3-2 (Backend Eng) | Extend audit log schema with an optional 'acted as delegate for' field → Write delegated-approval audit entries using the extended schema | near-critical | 2d | low |
| EPIC-3-2 (Backend Eng) → EPIC-3-3 (Web Eng) | Write delegated-approval audit entries using the extended schema → Audit log view: filter/search delegated-approval entries | near-critical | 2d | low |
| EPIC-1-1 (Backend Eng) → EPIC-4-1 (Web Eng) | Extend expense data model & API to store original currency, amount, and FX rate used → Admin settings screen: enable/disable multi-currency and set reporting currency | near-critical | 2d | low |
| EPIC-1-2 (Backend Eng) → EPIC-5-1 (Finance Eng) | Integrate with existing Finance Reporting FX rate service client → Add original and converted amount columns to the monthly finance export | near-critical | 2d | low |
| EPIC-3-2 (Backend Eng) → EPIC-5-3 (Finance Eng) | Write delegated-approval audit entries using the extended schema → Update export attribution logic for delegated approvals per compliance decision | near-critical | 2d | high |

