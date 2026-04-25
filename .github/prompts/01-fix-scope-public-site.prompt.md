---
agent: 'agent'
description: 'Fix accidental public-site scope and preserve internal CRM behavior'
---

The project scope is an internal Django Sales Note / Sales Management System.

A `public_site` app may have been added in a previous phase by mistake.

Task:
Audit the impact of `public_site` and fix scope safely.

Goals:
1. Preserve existing `/reporting/*` CRM functionality.
2. Ensure internal sales data is not public.
3. Ensure root `/` behavior is appropriate:
   - unauthenticated users should go to `/reporting/login/`
   - authenticated users may go to dashboard/reporting home if supported
4. Do not expand public product/brand/document pages.
5. Do not delete code destructively unless clearly safe.
6. If disabling `public_site`, do it with minimal changes and document what was changed.

Before changing code:
- Read AGENT_PLAN.md.
- Inspect root urls.
- Inspect installed apps.
- Inspect templates and views affected by public_site.

After changes:
- Run `python manage.py check`.
- Smoke test important URLs where possible.
- Update AGENT_REPORT.md.

Important:
This is a correction task. Do not implement product or brand detail pages.