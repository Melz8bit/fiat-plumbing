# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Approval Workflow

- For multi-step features or non-trivial changes, present a plan and wait for explicit approval before implementing.
- Do not over-implement: stick to the scope requested. If you discover related work, ask first.

## Commands

**Run the development server:**
```bash
# Activate virtualenv first (Windows)
.venv\Scripts\Activate.ps1

# Set required environment variables (see .env), then:
python app.py
```

**Run with gunicorn (production-style):**
```bash
gunicorn app:app
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

There are no automated tests in this codebase.

## Environment Variables

Copy `.env` and populate the following before running:

| Variable | Purpose |
|---|---|
| `APP_KEY` | Flask secret key |
| `SUPABASE_URL` | Supabase DB user (used in connection string) |
| `SUPABASE_PWD` | Supabase DB password |
| `SUPABASE_DB_NAME` | Supabase database name |
| `SUPABASE_HOST` | Supabase host |
| `S3_ACCESS_KEY` | AWS S3 access key |
| `S3_SECRET_ACCESS_KEY` | AWS S3 secret key |
| `S3_REGION` | AWS S3 region |
| `S3_BUCKET_NAME` | AWS S3 bucket for document storage |
| `FLASK_DEBUG` | Set to `true` to enable debug mode |

## Architecture

This is a single-file Flask application (`app.py`) for Fiat Plumbing — an internal business management tool for a plumbing contractor. There are no blueprints or application factory patterns; all routes live in `app.py`.

**Module layout:**
- `app.py` — All Flask routes and business logic
- `database.py` — All SQL queries via SQLAlchemy `text()` against a PostgreSQL (Supabase) database. No ORM models are used; queries return `RowMapping` dicts.
- `forms.py` — WTForms/Flask-WTF form classes. Several forms (`DocumentUploadForm`, `ProjectStatusForm`, `ProposalFixturesForm`, `PermitsAddForm`) call `database.*` functions at import time to populate `SelectField` choices — this means the DB connection is required when the module is imported.
- `documents.py` — AWS S3 integration (upload/download) via boto3.
- `models/users.py` — Thin `UserMixin` wrapper around a user dict row; used only by Flask-Login.
- `templates/` — Jinja2 HTML templates. `bootstrap.html` is the base layout; `nav.html` is the nav partial.

**Key data flow patterns:**

*Project page (`/project/<project_id>`)* is the most complex route: it initializes all forms at once and dispatches multiple `validate_on_submit()` checks in a single POST handler. The active tab is preserved across redirects via `session["active_tab"]`.

*Proposal workflow* uses a two-stage temp-table pattern: fixtures, installments, and notes are written to `tmp_project_proposal_*` tables during drafting (AJAX endpoints), then on finalization (`/finalizeProposal`), they are copied to permanent `project_proposal_*` tables and temp tables are cleared. The PDF is generated in-memory by WeasyPrint and uploaded directly to S3.

*Invoice/payment flow:* installments → invoices (`project_invoices`) → payments. Invoices automatically calculate 10% retainage. The `/apply_payment/<project_id>` AJAX endpoint computes payment allocation across open invoices (handling retainage vs. non-retainage separately) and returns JSON for the UI before the form is submitted.

*Role-based data visibility:* `database.get_all_clients()` and `database.get_all_projects()` accept a `user_role` argument; the `developer` role sees test data, all other roles filter `is_test = FALSE`.

*Permit follow-up dates* are calculated automatically from `matrix_permits_request.follow_up_days` when a permit is added or updated.

**Database tables of note:**
- `matrix_*` tables are lookup/reference tables (fixtures, installment categories, document types, permit request info, project statuses)
- `tmp_project_proposal_*` are temporary draft tables cleared after proposal finalization
- `zip_code_county` supports address auto-fill by zip code

**Jinja2 template filters** registered in `app.py`: `format_currency`, `calculate_due_date`, `get_today_date`.

## Flask Conventions

### Modal & Form Patterns

- Avoid hidden-field approaches that depend on modal open/close timing for passing IDs (e.g., `dept_id`). Prefer URL parameters or server-rendered context.
- Use Bootstrap's `show.bs.modal` event with `event.relatedTarget` to pre-fill modal fields from the triggering button's `data-*` attributes.
- For edit modals, set the form `action` URL dynamically in the `show.bs.modal` handler so the ID travels in the URL, not a hidden field.
- Test modal interactions end-to-end after changes.

## Terminology

- "TODO list" / "task list" refers to the Claude Code `TodoWrite` task list UI, not code `# TODO` comments. Use `TodoWrite` for tracking multi-step work.
