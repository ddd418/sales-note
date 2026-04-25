# QA_CHECKLIST.md

## Scope check

- [ ] This task improves the internal sales management system.
- [ ] This task does not expand public product/brand/catalog pages.
- [ ] Existing `/reporting/*` functionality is preserved.
- [ ] Anonymous users cannot access internal CRM data.
- [ ] Root URL behavior is appropriate for an internal system.

## Django checks

- [ ] `python manage.py check` passes.
- [ ] Existing migrations are not broken.
- [ ] No unintended model changes.
- [ ] If model changes are intended, migrations are created and documented.
- [ ] No secrets are committed.

## Authentication / authorization

- [ ] Login page works.
- [ ] Logout works if present.
- [ ] Authenticated pages require login.
- [ ] User-specific data is not exposed to unauthorized users.
- [ ] CSRF protection is preserved.

## Sales note UX

- [ ] Sales note list is usable.
- [ ] Search/filter works if implemented.
- [ ] Create form works.
- [ ] Edit form works if present.
- [ ] Detail page works if present.
- [ ] Required fields validate correctly.
- [ ] Empty states are clear.
- [ ] Mobile layout is usable.

## Customer/account UX

- [ ] Customer/account list works if present.
- [ ] Customer/account detail works if present.
- [ ] Related sales notes are visible if implemented.
- [ ] Quick add sales note link works if implemented.

## Follow-up UX

- [ ] Next action is visible where relevant.
- [ ] Next contact date is visible where relevant.
- [ ] Overdue items are distinguishable if implemented.
- [ ] Follow-up completion works if implemented.

## Dashboard

- [ ] Dashboard loads.
- [ ] KPI cards do not break on empty data.
- [ ] Recent activity list works.
- [ ] Follow-up list works if implemented.
- [ ] Links from dashboard work.

## URL smoke test

Check important URLs such as:

- [ ] /
- [ ] /reporting/login/
- [ ] /reporting/
- [ ] main dashboard URL
- [ ] sales note list URL
- [ ] sales note create URL
- [ ] customer/account list URL if present
- [ ] follow-up URL if present

## Report

- [ ] AGENT_PLAN.md updated before major changes.
- [ ] AGENT_REPORT.md updated after changes.
- [ ] Files changed are listed.
- [ ] Commands run are listed.
- [ ] Known limitations are listed.
- [ ] Recommended next phase is listed.