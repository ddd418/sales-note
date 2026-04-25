---
agent: 'agent'
description: 'Implement follow-up and pipeline improvements for the sales management system'
---

Implement Phase 5 improvements for the Django Sales Note / Sales Management System.

Read:
- PROJECT_BRIEF.md
- SALES_CRM_SPEC.md
- QA_CHECKLIST.md
- AGENT_PLAN.md
- AGENT_REPORT.md

Focus:
- Follow-up tracking
- Next action management
- Sales pipeline visibility
- Manager review workflow

Do not build public product/brand/catalog pages.

Before implementation:
- Inspect existing models for fields related to status, stage, due date, next action, expected amount, customer, salesperson.
- Avoid unnecessary model changes.
- If fields do not exist, propose safe options before adding them.

Possible improvements if supported by existing data:
1. Follow-up list
   - Today
   - Upcoming
   - Overdue
   - Completed

2. Follow-up badges
   - 예정
   - 오늘
   - 지연
   - 완료

3. Sales status/stage display
   - Lead
   - Contacted
   - Quoted
   - Negotiation
   - Won
   - Lost
   Use existing Korean labels if already defined.

4. Manager view
   - Activity by salesperson
   - Overdue follow-ups by owner
   - Recent important updates

5. Customer/account timeline
   - Chronological sales notes
   - Last contact date
   - Next follow-up date

Validation:
- Run Django checks.
- Run tests if present.
- Check authenticated access.
- Update AGENT_REPORT.md.