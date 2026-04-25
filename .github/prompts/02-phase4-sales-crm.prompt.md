---
agent: 'agent'
description: 'Implement Phase 4 improvements for the existing sales CRM'
---

Implement Phase 4 for the existing Django Sales Note / Sales Management System.

Read first:
- .github/copilot-instructions.md
- AGENTS.md
- PROJECT_BRIEF.md
- SALES_CRM_SPEC.md
- QA_CHECKLIST.md
- AGENT_PLAN.md

Scope:
Improve the existing internal CRM/reporting system.

Do NOT build:
- product detail pages
- brand detail pages
- public catalog pages
- public marketing homepage sections

Focus on the `reporting` app and existing authenticated workflows.

Phase 4 priorities:

1. Dashboard improvements
   - Show recent sales notes/reports
   - Show today or this week activity if data exists
   - Show upcoming follow-ups if fields exist
   - Show overdue follow-ups if fields exist
   - Add quick links to create sales note/report
   - Do not break on empty data

2. Sales note/report list improvements
   - Keyword search if feasible
   - Date filter if feasible
   - Customer/account filter if feasible
   - Salesperson filter if feasible
   - Status/stage filter if existing fields support it
   - Pagination if needed
   - Clear empty state
   - Mobile-friendly layout

3. Sales note/report detail improvements
   - Clear summary area
   - Customer/account info
   - Activity date
   - Author/salesperson
   - Content
   - Next action/follow-up info if fields exist
   - Edit/back actions

4. Sales note/report form improvements
   - Improve field labels/help text
   - Improve validation messages
   - Make form easier on mobile
   - Preserve CSRF and authentication
   - Do not add database fields unless truly needed and planned

5. Customer/account history
   - If customer/account model exists, improve related sales note visibility
   - Add quick link from customer/account to create sales note if feasible

Database rule:
- First inspect existing models.
- If model changes are needed, document them in AGENT_PLAN.md or AGENT_REPORT.md.
- Avoid schema changes in this phase unless necessary.

Validation:
- Run `python manage.py check`.
- Run tests if present.
- Check important URLs.
- Check form POST if feasible.
- Update AGENT_REPORT.md.

Deliverable:
AGENT_REPORT.md must include:
1. Summary of CRM improvements
2. Files changed
3. Existing functionality preserved
4. Commands run and results
5. Known limitations
6. Recommended Phase 5