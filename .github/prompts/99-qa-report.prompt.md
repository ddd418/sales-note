---
agent: 'agent'
description: 'Run QA checks for the internal sales management system'
---

Run final QA for the Django Sales Note / Sales Management System.

Read:
- QA_CHECKLIST.md
- AGENT_PLAN.md
- AGENT_REPORT.md
- PROJECT_BRIEF.md
- SALES_CRM_SPEC.md

Check:

1. Scope
   - Internal CRM focus is preserved
   - No unrelated product/brand/catalog public pages expanded
   - Existing reporting app works

2. Authentication
   - Login works
   - Internal pages require login
   - Anonymous users cannot access CRM data

3. URLs
   - /
   - /reporting/login/
   - /reporting/
   - dashboard URL if present
   - sales note/report list URL
   - create/edit/detail URLs if present

4. Forms
   - CSRF preserved
   - Required fields validate
   - Submit works
   - Error messages display

5. Dashboard/list/detail pages
   - Empty states work
   - Pagination/search/filter works if implemented
   - Links work
   - Mobile layout is usable

6. Django
   - Run `python manage.py check`
   - Run tests if present
   - Check migrations if model changes were made

Update AGENT_REPORT.md with:

1. Final QA summary
2. Commands run and results
3. URLs checked
4. Issues found
5. Remaining risks
6. Recommended next task

Do not make unrelated code changes.