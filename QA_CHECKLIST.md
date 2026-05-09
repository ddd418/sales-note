# QA_CHECKLIST.md

## Scope check

- [ ] This task improves the internal sales management system.
- [ ] This task does not expand public product/brand/catalog pages.
- [ ] Existing `/reporting/*` functionality is preserved.
- [ ] Anonymous users cannot access internal CRM data.
- [ ] Root URL behavior is appropriate for an internal system.
- [ ] If this is a frontend workflow, the target direction is React CRM, not Django template UI.
- [ ] Existing Django template behavior remains available until the React replacement is deployed and manually verified.

## React migration check

- [ ] Existing Django template URL and behavior were inspected before migration.
- [ ] React page does not copy the old Django template design as the final UI.
- [ ] Django provides JSON APIs or compatibility routes for the React workflow.
- [ ] Authentication, permissions, data scoping, and CSRF/session behavior are preserved.
- [ ] Migrated workflow has a fallback, redirect, or documented transition path.
- [ ] Template deletion is deferred until feature parity and production manual testing are complete.

## Django checks

- [ ] `python manage.py check` passes.
- [ ] Existing migrations are not broken.
- [ ] No unintended model changes.
- [ ] If model changes are intended, migrations are created and documented.
- [ ] No secrets are committed.

## React checks

- [ ] `npm run build` passes for frontend runtime changes.
- [ ] `node --check server.mjs` passes when the frontend server is relevant.
- [ ] New or changed React API clients handle login-required and error responses.
- [ ] UI works on desktop and mobile widths where practical.

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
- [ ] affected React production URL after Railway deployment
- [ ] affected `/reporting/api/*` production URL returns expected login protection or payload

## Railway deployment

- [ ] Changes are committed and pushed.
- [ ] Affected Railway service(s) are deployed (`web`, `sales-note-frontend`, or both).
- [ ] Production deployment status is checked.
- [ ] Production bundle/API smoke check is done.
- [ ] User receives a concrete manual test process for the deployed server.
- [ ] Next implementation task waits for user confirmation or explicit instruction.

## Report

- [ ] AGENT_PLAN.md updated before major changes.
- [ ] AGENT_REPORT.md updated after changes.
- [ ] Files changed are listed.
- [ ] Commands run are listed.
- [ ] Known limitations are listed.
- [ ] Recommended next phase is listed.
- [ ] Production deployment status is listed when applicable.
- [ ] Manual server test process is listed.
