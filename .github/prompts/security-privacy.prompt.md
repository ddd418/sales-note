---
agent: 'agent'
description: 'Review and improve security/privacy for Sales Note'
---

Review and improve security/privacy.

Read first:
- AGENT_PLAN.md
- PRODUCT_BRIEF.md
- SECURITY_PRIVACY_CHECKLIST.md
- QA_CHECKLIST.md
- Existing settings/config files
- Existing auth/permission code
- Existing forms/views/controllers

Scope:
- Authentication checks
- Authorization checks
- Object-level access
- CSRF/session safety
- Form validation
- File upload safety if present
- Sensitive data exposure
- Environment variable usage
- Privacy policy consistency
- Admin access safety

Do not:
- Commit secrets
- Print environment variables
- Weaken authentication
- Remove authorization checks
- Make private data public
- Add breaking changes without documenting them

If security issues are found:
- Fix low-risk, clear issues.
- Document larger or risky issues in AGENT_REPORT.md.
- Keep changes scoped and reviewable.

After implementation:
- Run available validation commands.
- Update AGENT_REPORT.md.