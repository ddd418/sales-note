---
agent: 'agent'
description: 'Improve dashboard and sales report workflow for Sales Note'
---

Improve the dashboard and sales report workflow.

Read first:
- AGENT_PLAN.md
- PRODUCT_BRIEF.md
- SALES_NOTE_SPEC.md
- SECURITY_PRIVACY_CHECKLIST.md
- QA_CHECKLIST.md

Scope:
- Dashboard
- Sales report list
- Sales report detail
- Sales report create/edit form
- Manager review/comment flow if already present
- Related navigation links

Do not make unrelated changes.

Dashboard improvements:
- Show clear next actions.
- For sales reps, prioritize today’s schedule, pending reports, recent customer activity, and follow-ups.
- For managers, prioritize team reports, unreviewed reports, overdue follow-ups, and pipeline summary if data exists.
- Use cards/tables/status badges where appropriate.
- Add empty states.

Sales report list:
- Search/filter by date/customer/status/author if supported.
- Show useful columns.
- Sort by recent date.
- Keep mobile usability in mind.

Sales report form:
- Clear Korean labels.
- Required field validation.
- Helpful placeholder text.
- Success/error states.
- Prevent accidental data issues.

Security:
- Preserve authentication.
- Preserve object-level permissions.
- Do not expose reports to unauthorized users.

After implementation:
- Run available validation commands.
- Update AGENT_REPORT.md.