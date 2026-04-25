---
agent: 'agent'
description: 'Improve form UX, Korean validation messages, lists, filters, and mobile usability'
---

Improve form UX and list usability across the Sales Note system.

Read first:
- AGENT_PLAN.md
- PRODUCT_BRIEF.md
- SALES_NOTE_SPEC.md
- QA_CHECKLIST.md

Scope:
- Forms
- Validation messages
- Empty states
- Tables/lists
- Search/filter/sort UI
- Mobile usability

Focus pages:
- Sales report create/edit
- Customer create/edit
- Contact create/edit if present
- Opportunity create/edit if present
- Schedule/task create/edit if present
- Quote/contract form if present

UX requirements:
- Korean field labels
- Clear required field indicators
- Korean error messages
- Helpful placeholder text
- Success messages
- Cancel/back navigation
- Confirmation for destructive actions
- Empty states
- Mobile-friendly layout

Do not:
- Remove server-side validation
- Replace security checks with only client-side checks
- Add heavy dependencies unnecessarily

After implementation:
- Run available validation commands.
- Update AGENT_REPORT.md.