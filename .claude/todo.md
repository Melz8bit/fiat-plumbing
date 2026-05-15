# Todo List

## Cleanup
- [ ] Remove large commented-out HTML blocks in project.html, project_invoices.html, proposal_create.html, proposal_print.html
- [ ] sign_up.html & reset_password.html: inline flash toast → replace with `flash_message.html` include
- [ ] proposal_print.html: empty `<title>` tag
- [ ] Auth forms: custom `.button` class → Bootstrap `btn btn-primary`
- [ ] Replace inline `onclick` handlers with event delegation (permits, inspections, search, client list)
- [ ] client_add.html vs client_edit.html: near-identical markup → shared Jinja macro
- [ ] Replace inline `style='width:X%'` with Bootstrap grid classes
- [ ] Replace `colspan='100%'` with actual column counts

## Features
- [ ] Mobile responsiveness: present plan before touching templates
- [ ] Permits & Inspections: filter dropdown to project city/county only
- [ ] Permit blank form links (optional)
