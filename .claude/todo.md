# Todo List

## Pending

### UI / Mobile
- [ ] Mobile responsiveness: form layouts — col-12 col-md-* breakpoints on multi-column rows (remaining forms)

### Forms
- [ ] Phone number input: allow user to type digits without hyphens; auto-format to xxx-xxx-xxxx

### Invoices
- [ ] Rework full invoice tab functionality
- [ ] Fix: View Details in invoice not working (mobile collapse)

### Permits & Inspections
- [ ] Filter permit/inspection dropdown to project city/county only
- [ ] Permit blank form links (optional)

### Documents
- [ ] Email document — per-document send/share button opens modal; recipient list = client contacts with an email saved; optional body field (generic fallback if blank)

### Admin / Company Documents
- [ ] Company document upload: upload files to correct S3 location under `company-docs/`; list existing folders in `company-docs/` as save-location options; allow user to create a new folder
- [ ] Company document table in Supabase (similar to `project_documents`): track file type, S3 path, uploader, upload date, optional expiration date
- [ ] Admin email page — document version dropdown: above the entity table, show a dropdown to select which version of an existing company document to send; populated from the company documents table; default = most recent non-expired version; expired entries appear at bottom with `[EXPIRED]` tag

### Clients
- [ ] Support multiple contacts per client

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
- [x] Search results → list group
- [x] Client add/edit form — responsive columns, blue border styling
- [x] Add Project form — responsive columns, blue border styling
- [x] Project view header — h3, icon buttons, dev buttons on own row
- [x] Project view details & location — responsive columns, blue border styling
- [x] Project tabs — mobile dropdown select (dynamically built from tab buttons)
- [x] Project notes tab — list group
- [x] Project fixtures tab — list group (mobile) / table (desktop)
- [x] Project installments tab — list group (mobile) / table (desktop), progress section redesigned
- [x] Project invoices tab — card list (mobile) / table (desktop)
- [x] Project payments tab — card list (mobile) / table (desktop)
- [x] Project permits tab — card list (mobile) / table (desktop), inline edit m-prefix fix + tab reload
- [x] Project inspections tab — card list (mobile) / table (desktop), inline edit m-prefix fix + tab reload
- [x] Project documents tab — list group (mobile) / table (desktop)
- [x] Add Inspection / Add Permit modals — modal-fullscreen-sm-down, responsive columns
- [x] COI admin nav — hidden on mobile (d-none d-lg-flex)

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