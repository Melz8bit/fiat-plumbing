# Todo List

## Cleanup
- [x] Remove large commented-out HTML blocks in project.html, project_invoices.html, proposal_create.html, proposal_print.html
- [x] sign_up.html & reset_password.html: inline flash toast → replace with `flash_message.html` include
- [x] proposal_print.html: empty `<title>` tag
- [x] Auth forms: custom `.button` class → Bootstrap `btn btn-primary`
- [x] Replace inline `onclick` handlers with event delegation (proposal_create.html)
- [x] Replace `colspan='100%'` with actual column counts
- [ ] client_add.html vs client_edit.html: near-identical markup → shared Jinja macro

## Features
- [ ] Filter dashboard queries by user role (hide test projects from non-dev users)
  - [ ] `get_projects_status_summary()` — add user_role param, filter is_test
  - [ ] `get_projects_finance_summary()` — make is_test filter role-aware
  - [ ] `get_permit_dashboard_summary()` — add user_role param + projects JOIN
  - [ ] `get_all_inspections()` — add user_role param, filter is_test
  - [ ] `app.py main()` — pass user.role to all four calls
- [ ] Mobile responsiveness: survey first, then implement in stages
- [ ] Permits & Inspections: filter dropdown to project city/county only
- [ ] Permit blank form links (optional)
