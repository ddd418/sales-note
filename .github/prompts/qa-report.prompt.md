---
agent: 'agent'
description: 'Run final QA and update AGENT_REPORT.md for Sales Note'
---

Run final QA for the Sales Note system.

Read:
- AGENT_PLAN.md
- AGENT_REPORT.md if it exists
- PRODUCT_BRIEF.md
- SALES_NOTE_SPEC.md
- SECURITY_PRIVACY_CHECKLIST.md
- QA_CHECKLIST.md

Check:
- Login/auth flow
- Dashboard
- Sales reports
- Customer management
- Opportunities
- Schedule/tasks
- Quotes/contracts if present
- Forms and validation
- Search/filter/list usability
- Mobile usability
- Security/privacy
- Permissions
- Build/test/deployment readiness

Run available validation commands only.

For Django-like projects, consider:
- python manage.py check
- python manage.py test
- python manage.py makemigrations --check --dry-run
- python manage.py collectstatic --noinput

For Node/front-end projects, consider:
- npm run lint
- npm run typecheck
- npm run test
- npm run build

Update AGENT_REPORT.md with:

1. Summary of completed changes
2. Files changed
3. Functional improvements
4. UX improvements
5. Security/privacy improvements
6. Commands run and results
7. Remaining issues
8. Missing information
9. Recommended next tasks

Do not make unrelated code changes.