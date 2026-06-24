# Todo List

## Pending

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
- [x] Mobile responsiveness: remaining form layouts (account.html, admin_coi.html edit modal)

### Forms
- [x] Phone number input: auto-format to xxx-xxx-xxxx as user types (client add/edit, contact modals, COI edit modal)
- [x] Phone number validation: pattern attribute (frontend) + Regexp validator (backend) on all phone fields

### Dashboard
- [x] Filter dashboard queries by user role (hide test projects from non-dev users)
  - [x] `get_projects_status_summary()` — add user_role param, filter is_test
  - [x] `get_projects_finance_summary()` — make is_test filter role-aware
  - [x] `get_permit_dashboard_summary()` — add user_role param + projects JOIN
  - [x] `get_all_inspections()` — add user_role param, filter is_test
  - [x] `app.py main()` — pass user.role to all four calls

### Documents
- [x] Email document — "Send Documents" button on project Documents tab; modal with From dropdown (AOL/Gmail, Ventura client auto-selects Gmail), To/CC recipient cards, document attach/remove workflow, auto-generated body with placeholder preview; note added on success

### Admin / Company Documents
- [x] `company_documents` Supabase table — tracks doc type, S3 key, folder, filename, uploader, upload date, optional expiration date
- [x] Company document upload page (`/admin/company-docs`) — upload to S3 `company-docs/`, list existing folders, new folder creation
- [x] License & Insurance Submissions page — COI year, State License, and BTR version dropdowns populated from `company_documents` table; default = most recent non-expired; expired tagged `[EXPIRED]`; dynamic email body lists only attached docs; hardcoded env var keys removed

### Clients
- [x] Multiple contacts per client — `client_poc` table given `id` PK and `title` column; add/edit/delete modals on client detail page; fixed bug where POC was never saved on client creation
- [x] Edit client: pre-check "Test Client?" checkbox when client is a test client

### Test Data Management
- [x] is_test checkbox (dev only) on new project and new client forms
- [x] Reset Project button (test projects only) with Bootstrap confirm modal
- [x] Delete Project button (test projects only) with Bootstrap confirm modal
- [x] Delete Client button (test clients only) with Bootstrap confirm modal (cascades to projects)
- [x] Auto-check is_test when creating a project from a test client page
- [x] Client dropdown filtered by test status (test projects → test clients only, enforced server-side)
