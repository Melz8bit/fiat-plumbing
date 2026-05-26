# Todo List

## Cleanup
- [x] Remove large commented-out HTML blocks in project.html, project_invoices.html, proposal_create.html, proposal_print.html
- [x] sign_up.html & reset_password.html: inline flash toast → replace with `flash_message.html` include
- [x] proposal_print.html: empty `<title>` tag
- [x] Auth forms: custom `.button` class → Bootstrap `btn btn-primary`
- [x] Replace inline `onclick` handlers with event delegation (proposal_create.html)
- [x] Replace `colspan='100%'` with actual column counts
- [x] client_add.html vs client_edit.html: near-identical markup → shared Jinja macro (client_form.html)

## Features
- [x] Filter dashboard queries by user role (hide test projects from non-dev users)
  - [x] `get_projects_status_summary()` — add user_role param, filter is_test
  - [x] `get_projects_finance_summary()` — make is_test filter role-aware
  - [x] `get_permit_dashboard_summary()` — add user_role param + projects JOIN
  - [x] `get_all_inspections()` — add user_role param, filter is_test
  - [x] `app.py main()` — pass user.role to all four calls
- [x] is_test checkbox (dev only) on new project and new client forms
- [x] Reset Project button (test projects only) with Bootstrap confirm modal
- [x] Delete Project button (test projects only) with Bootstrap confirm modal
- [x] Delete Client button (test clients only) with Bootstrap confirm modal (cascades to projects)
- [x] Auto-check is_test when creating a project from a test client page
- [x] Client dropdown filtered by test status (test projects → test clients only, enforced server-side)
- [ ] Mobile responsiveness: survey first, then implement in stages
- [ ] Permits & Inspections: filter dropdown to project city/county only
- [ ] Permit blank form links (optional)
