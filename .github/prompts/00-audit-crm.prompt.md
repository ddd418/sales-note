---
agent: 'agent'
description: 'Audit the Django sales management system before making changes'
---

This repository is a Django Sales Note / Sales Management System.

It is NOT a public product/brand/catalog website.

Read:
- .github/copilot-instructions.md
- AGENTS.md
- PROJECT_BRIEF.md
- SALES_CRM_SPEC.md
- QA_CHECKLIST.md
- README or project docs

Then inspect:
- Django apps
- settings
- root urls
- reporting urls
- models
- forms
- views
- templates
- static files
- authentication flow
- database migrations

Do NOT modify production code yet.

Create or update AGENT_PLAN.md with:

1. Detected Django structure
2. Existing apps and purpose
3. Existing URL map
4. Existing reporting/CRM functionality
5. Existing models and relationships
6. Existing forms
7. Existing templates
8. Existing dashboard/list/detail/create/edit flows
9. Authentication and permission behavior
10. Impact of `public_site` if it exists
11. Whether root `/` should redirect to `/reporting/login/` or dashboard
12. Key UX gaps in the sales management system
13. Recommended Phase 4 implementation plan
14. Files likely to be changed
15. Whether model changes are needed
16. Validation commands to run

Important:
- Do not propose product detail pages.
- Do not propose brand detail pages.
- Do not propose public catalog pages.
- Focus on the internal sales CRM.