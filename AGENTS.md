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

## Ultimate architecture direction

The long-term target is a React-only CRM frontend with Django used as the backend only.

- React owns all user-facing CRM pages and product UI.
- Django owns authentication, permissions, database models, business logic, file handling, and JSON APIs.
- Django templates are temporary legacy screens. Replace them with React equivalents before deleting them.
- Do not copy the old Django template design into React. Build a distinct internal CRM product UI.
- Keep `/reporting/*` while it is needed for login, existing backend routes, API endpoints, and legacy fallback screens.
- Delete Django frontend templates only after React feature parity, permission checks, and server-side manual testing are complete.

## Workflow

For major work:

1. Inspect repository structure.
2. Identify Django apps, URLs, models, forms, templates, static files.
3. Create or update AGENT_PLAN.md.
4. Confirm whether database model changes are needed.
5. Implement scoped changes.
6. Run checks.
7. Create or update AGENT_REPORT.md.
8. Commit and push the completed task.
9. Deploy the updated backend/frontend to Railway when the task affects runtime behavior.
10. Provide a production server manual test process and wait for the user to confirm before starting the next task.

## Important rules

- Do not expose internal sales data publicly.
- Do not weaken authentication.
- Do not remove existing reporting functionality.
- Do not make unrelated large refactors.
- Do not commit secrets.
- Do not invent features without checking existing models.
- Do not add model fields without considering migrations.
- Do not improve Django template UI as the final product direction unless it is required as a temporary compatibility fix.
- Do not remove a Django template or route until the React replacement has been deployed and manually verified.
- Do not start the next implementation task after a deployment until the user has completed server-side manual testing or explicitly asks to proceed.

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
- React CRM migration
- API stability for React screens
- Railway deployment verification

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
- Production deployment status when applicable
- Manual server test process for the user
