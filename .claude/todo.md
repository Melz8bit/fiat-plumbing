# Todo List

## Pending

### UI / Mobile
- [ ] Mobile responsiveness: project tab partials (next)
- [ ] Mobile responsiveness: form layouts — col-12 col-md-* breakpoints on multi-column rows

### Forms
- [ ] Phone number input: allow user to type digits without hyphens; auto-format to xxx-xxx-xxxx

### Invoices
- [ ] Rework full invoice tab functionality
- [ ] Fix: View Details in invoice not working (mobile collapse)

### Permits & Inspections
- [ ] Filter permit/inspection dropdown to project city/county only
- [ ] Permit blank form links (optional)

---

## Completed

### Cleanup
- [x] Remove large commented-out HTML blocks in project.html, project_invoices.html, proposal_create.html, proposal_print.html
- [x] sign_up.html & reset_password.html: inline flash toast → replace with `flash_message.html` include
- [x] proposal_print.html: empty `<title>` tag
- [x] Auth forms: custom `.button` class → Bootstrap `btn btn-primary`
- [x] Replace inline `onclick` handlers with event delegation (proposal_create.html)
- [x] Replace `colspan='100%'` with actual column counts
- [x] client_add.html vs client_edit.html: near-identical markup → shared Jinja include (client_form.html)

### UI / Mobile
- [x] Projects list → list group (mobile-responsive)
- [x] Client list → list group (mobile-responsive)
- [x] Client detail projects table → list group (mobile-responsive)
- [x] Dashboard: chart w-75 → w-100, finances/permits/inspections → list groups

### Dashboard
- [x] Filter dashboard queries by user role (hide test projects from non-dev users)
  - [x] `get_projects_status_summary()` — add user_role param, filter is_test
  - [x] `get_projects_finance_summary()` — make is_test filter role-aware
  - [x] `get_permit_dashboard_summary()` — add user_role param + projects JOIN
  - [x] `get_all_inspections()` — add user_role param, filter is_test
  - [x] `app.py main()` — pass user.role to all four calls

### Test Data Management
- [x] is_test checkbox (dev only) on new project and new client forms
- [x] Reset Project button (test projects only) with Bootstrap confirm modal
- [x] Delete Project button (test projects only) with Bootstrap confirm modal
- [x] Delete Client button (test clients only) with Bootstrap confirm modal (cascades to projects)
- [x] Auto-check is_test when creating a project from a test client page
- [x] Client dropdown filtered by test status (test projects → test clients only, enforced server-side)