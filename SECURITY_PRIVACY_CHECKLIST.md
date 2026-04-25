# SECURITY_PRIVACY_CHECKLIST.md

## Purpose

This system handles personal data and business sales data.
Security and privacy must be considered before and after every major change.

## Authentication

- [ ] Login required for internal pages
- [ ] Logout works
- [ ] Failed login behavior is safe
- [ ] Passwords are never logged
- [ ] Session settings are appropriate
- [ ] CSRF protection is enabled where applicable

## Authorization

- [ ] Normal users cannot access admin-only pages
- [ ] Sales reps cannot access unauthorized team/customer data
- [ ] Managers can access only permitted team data
- [ ] Object-level permission is checked for detail/edit/delete actions
- [ ] API endpoints, if any, enforce the same permissions as pages

## Personal information

Personal data may include:
- Name
- Email
- Phone number
- Company
- Department
- Job title
- IP address
- Service usage logs

Checklist:
- [ ] Collect only necessary data
- [ ] Do not expose personal data unnecessarily in templates
- [ ] Do not include sensitive personal data in client-side logs
- [ ] Do not include sensitive personal data in server logs unless necessary
- [ ] Mask or limit display where appropriate
- [ ] Privacy policy remains consistent with actual data processing

## File uploads

If Cloudinary or other media storage is used:

- [ ] File type validation
- [ ] File size limit
- [ ] Authenticated access where needed
- [ ] No executable file upload
- [ ] File ownership/permission check
- [ ] Safe file deletion behavior

## Forms

- [ ] Server-side validation exists
- [ ] Client-side validation does not replace server-side validation
- [ ] Required fields are validated
- [ ] Error messages are clear and in Korean
- [ ] Dangerous input is escaped/sanitized
- [ ] CSRF token is used where applicable

## Secrets and environment

- [ ] No secrets committed
- [ ] API keys are stored in environment variables
- [ ] Database credentials are not exposed
- [ ] Cloudinary credentials are not exposed
- [ ] Railway environment variables are documented but not committed

## Audit and logging

Recommended for important actions:
- Login attempts
- User creation/update/delete
- Sales report delete
- Customer delete
- Opportunity stage change
- Quote/contract status change
- Admin setting changes

Checklist:
- [ ] Logs do not expose secrets
- [ ] Logs do not contain unnecessary personal data
- [ ] Important destructive actions are traceable

## Deployment safety

- [ ] Migrations are checked
- [ ] Static files build/collect correctly
- [ ] Production debug mode is not enabled
- [ ] Allowed hosts/origins are appropriate
- [ ] Error pages do not expose sensitive data