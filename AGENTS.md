# AGENTS.md

## Role

You are working on a Django-based Sales Note / Sales Management System.

Your job is to improve the existing internal sales CRM/reporting workflow.

This is not a public website project.

## Required reading order

Before changing code, read:

1. .github/copilot-instructions.md
2. PROJECT_BRIEF.md
3. SALES_CRM_SPEC.md
4. QA_CHECKLIST.md
5. README or project documentation
6. Django settings, urls, models, views, forms, templates
7. package or static build configuration if present

## Existing system priority

Preserve the existing `reporting` app and `/reporting/*` routes.

Do not replace the CRM system with a public site.

If `public_site` exists, inspect it only to understand whether it affects root URL behavior. Do not expand it unless explicitly requested.

## Workflow

For major work:

1. Inspect repository structure.
2. Identify Django apps, URLs, models, forms, templates, static files.
3. Create or update AGENT_PLAN.md.
4. Confirm whether database model changes are needed.
5. Implement scoped changes.
6. Run checks.
7. Create or update AGENT_REPORT.md.

## Important rules

- Do not expose internal sales data publicly.
- Do not weaken authentication.
- Do not remove existing reporting functionality.
- Do not make unrelated large refactors.
- Do not commit secrets.
- Do not invent features without checking existing models.
- Do not add model fields without considering migrations.

## Preferred improvements

Prioritize:

- Sales note usability
- Customer/account history
- Dashboard clarity
- Follow-up tracking
- Search and filters
- Mobile-friendly forms
- Manager review workflow
- Data stability

## Deliverables

At the end of each task, update AGENT_REPORT.md with:

- Summary
- Files changed
- CRM improvements
- Existing functionality preserved
- Commands run
- Results
- Known limitations
- Recommended next task