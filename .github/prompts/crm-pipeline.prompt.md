---
agent: 'agent'
description: 'Improve customer management, contacts, opportunities, and pipeline flow'
---

Improve CRM and pipeline-related functionality.

Read first:
- AGENT_PLAN.md
- PRODUCT_BRIEF.md
- SALES_NOTE_SPEC.md
- SECURITY_PRIVACY_CHECKLIST.md
- QA_CHECKLIST.md

Scope:
- Customer/company list and detail
- Contact person information
- Opportunity/deal list and detail
- Pipeline/status display
- Related sales reports
- Related schedules/tasks
- Related quotes/contracts if present

Do not invent data models if the repository already has existing models.
Follow existing model names and relationships.

Customer UX:
- Search by company name.
- Show recent activity.
- Show last contact date if data exists.
- Show next follow-up if data exists.
- Link to related reports/opportunities.

Opportunity UX:
- Show stage/status clearly.
- Show expected amount/date if fields exist.
- Show next action.
- Link opportunity to customer and reports.
- Use status badges.

Security:
- Respect user/team permissions.
- Do not expose customer data to unauthorized users.

After implementation:
- Run available validation commands.
- Update AGENT_REPORT.md. 