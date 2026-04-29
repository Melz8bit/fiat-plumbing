import mimetypes
import ast
import base64
import json
import os
import sys
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    send_file,
    session,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from itsdangerous import URLSafeTimedSerializer
from num2words import num2words
from sqlalchemy import null, select
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


@contextmanager
def suppress_c_warnings():
    """Temporarily redirects C-level stderr to devnull to suppress GLib warnings."""
    # Open a connection to the system's null device
    devnull = os.open(os.devnull, os.O_WRONLY)
    # Save the original stderr file descriptor
    old_stderr = os.dup(sys.stderr.fileno())
    try:
        # Swap stderr with devnull
        os.dup2(devnull, sys.stderr.fileno())
        yield
    finally:
        # Restore the original stderr when done
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)
        os.close(old_stderr)


with suppress_c_warnings():
    from weasyprint import HTML

import database
from database import db_connect
from documents import upload_file, download_file, upload_proposal
from forms import (
    ClientForm,
    LoginForm,
    SignUpForm,
    ResetPasswordForm,
    ForgotPasswordForm,
    ChangePasswordForm,
    UpdateEmailForm,
    ProjectForm,
    ProjectNotesForm,
    MasterPermitForm,
    DocumentUploadForm,
    ProjectStatusForm,
    InvoiceStatusUpdateForm,
    InvoicePaymentForm,
    InvoiceCreateForm,
    ApplyPaymentForm,
    ProposalFixturesForm,
    ProposalFixtureNotesForm,
    ProposalInstallmentsForm,
    ProposalNotesForm,
    PermitsAddForm,
)
from models import users

FIAT_PLUMBING = {
    "company_name": "Fiat Plumbing and General Contractors, Inc.",
    "address": "2727 SW 36th Ave",
    "city": "Miami",
    "state": "FL",
    "zip_code": "33133",
    "phone_number": "(305) 446-6366",
    "email": "afiat@aol.com",
}
DAYS_UNTIL_DUE = 30

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_KEY")
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
app.jinja_env.filters["jsonify"] = jsonify

engine = db_connect()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

logo_path = os.path.join(app.root_path, "static", "logo.png")


############## Login/Logout ##############
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("Your session has expired, please log in again.")
    return redirect(url_for("login"))


@login_manager.user_loader
def load_user(user_id):
    user = users.Users(database.get_user(user_id))
    return user or None


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        login_form = LoginForm()

        if login_form.validate_on_submit():
            email = login_form.email.data
            password = login_form.password.data

            login_form.email.data = ""
            login_form.password.data = ""

            user_db_password = database.get_user_password(email)

            if user_db_password:
                # user_db_password = user_db_password[0]
                if check_password_hash(user_db_password, password):
                    user_dict = database.get_user_from_email(email)
                    user = users.Users(user_dict)
                    login_user(user, remember=False)

                    session["user_id"] = user_dict["user_id"]

                    flash("Login successful")
                    return redirect(url_for("main"))
                else:
                    flash("Incorrect username or password")
            else:
                flash("Incorrect username or password")

        return render_template(
            "login.html",
            login_form=login_form,
        )
    except Exception as e:
        print(f"Login error: {e}")
        return redirect(url_for("login"))


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    signup_form = SignUpForm()

    if signup_form.validate_on_submit():
        first_name = signup_form.first_name.data
        last_name = signup_form.last_name.data
        email = signup_form.email.data
        password = signup_form.password.data
        confirm = signup_form.confirm.data

        if password != confirm:
            flash("Passwords do not match")

        existing_user = database.get_user_from_email(email)
        if existing_user:
            flash("Email is already in use. Please choose another email.")

        else:
            password_hash = generate_password_hash(password, "scrypt")
            user_info = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password_hash,
            }

            try:
                database.create_user(user_info)
                flash("Thank you for registering. You can now log in.")

                return redirect(url_for("login"))
            except Exception as e:
                print(f"{e=}")

    for error in list(signup_form.errors.values()):
        flash(error[0])

    return render_template(
        "sign_up.html",
        signup_form=signup_form,
    )


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


############## Password Reset ##############
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    forgot_password_form = ForgotPasswordForm()

    if forgot_password_form.validate_on_submit():
        email = forgot_password_form.email.data
        user = database.get_user_from_email(email)

        if user:
            # Generate secure token
            token = serializer.dumps(email, salt="password-reset-salt")
            reset_url = url_for("reset_password", token=token, _external=True)

            # TODO: Integrate your email sending logic here
            # send_reset_email(email, reset_url)

            print(f"Reset URL for {email}: {reset_url}")  # For local testing

            flash(
                "If an account with that email exists, a password reset link has been sent."
            )
            return redirect(url_for("login"))

    return render_template(
        "forgot_password.html", forgot_password_form=forgot_password_form
    )


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        # Token duration
        token_max_age = 3600
        email = serializer.loads(
            token, salt="password-reset-salt", max_age=token_max_age
        )
    except Exception:
        flash("The password reset link is invalid or has expired.")
        return redirect(url_for("forgot_password"))

    reset_password_form = ResetPasswordForm()

    if reset_password_form.validate_on_submit():
        password = reset_password_form.password.data
        password_hash = generate_password_hash(password, "scrypt")

        try:
            database.update_user_password(email, password_hash)
            flash("Your password has been updated. You can now log in.")
            return redirect(url_for("login"))
        except Exception as e:
            flash("An error occurred updated your password. Please try again.")
            print(f"Error updating password: {e}")

    for error in list(reset_password_form.errors.values()):
        flash(error[0])

    return render_template(
        "reset_password.html",
        reset_password_form=reset_password_form,
    )


############## Account ##############
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user = database.get_user(session["user_id"])
    change_password_form = ChangePasswordForm()
    update_email_form = UpdateEmailForm()

    if (
        change_password_form.change_password_submit.data
        and change_password_form.validate()
    ):
        current_password = change_password_form.current_password.data
        stored_password = database.get_user_password(user.email)

        if not check_password_hash(stored_password, current_password):
            flash("Current password is incorrect.")
        else:
            new_hash = generate_password_hash(
                change_password_form.new_password.data, "scrypt"
            )
            try:
                database.update_user_password(user.email, new_hash)
                flash("Password updated successfully.")
                return redirect(url_for("account"))
            except Exception as e:
                flash("An error occurred updating your password. Please try again.")
                print(f"Error updating password: {e}")

    if update_email_form.update_email_submit.data and update_email_form.validate():
        current_password = update_email_form.current_password.data
        stored_password = database.get_user_password(user.email)

        if not check_password_hash(stored_password, current_password):
            flash("Current password is incorrect.")
        else:
            new_email = update_email_form.new_email.data
            existing = database.get_user_from_email(new_email)
            if existing:
                flash("That email address is already in use.")
            else:
                try:
                    database.update_user_email(user.user_id, new_email)
                    flash("Email updated successfully.")
                    return redirect(url_for("account"))
                except Exception as e:
                    flash("An error occurred updating your email. Please try again.")
                    print(f"Error updating email: {e}")

    for error in list(change_password_form.errors.values()):
        if change_password_form.change_password_submit.data:
            flash(error[0])

    for error in list(update_email_form.errors.values()):
        if update_email_form.update_email_submit.data:
            flash(error[0])

    return render_template(
        "account.html",
        user=user,
        change_password_form=change_password_form,
        update_email_form=update_email_form,
    )


############## Home ##############
@app.route("/")
@login_required
def main():
    user = database.get_user(session["user_id"])
    clients = database.get_all_clients(user.role)
    projects = database.get_all_projects(user.role)
    permits = database.get_all_permits()

    permits_summary = get_permit_dashboard_summary(permits)

    # Graph data
    status_counts = database.get_projects_status_summary()
    status_summary_labels = [item["status"] for item in status_counts]
    status_summary_values = [item["count"] for item in status_counts]

    finance_counts = database.get_projects_finance_summary()

    return render_template(
        "home.html",
        user=user,
        clients=clients,
        projects=projects,
        status_summary_labels=status_summary_labels,
        status_summary_values=status_summary_values,
        finance_counts=finance_counts,
        permits_summary=permits_summary,
    )


def get_permit_dashboard_summary(raw_permits):
    summary_dict = {}

    for permit in raw_permits:
        project_id = permit.get("project_id")

        # 1. Initialize the project in our tracking dictionary if it doesn't exist yet
        if project_id not in summary_dict:
            summary_dict[project_id] = {
                "project_id": project_id,
                "plumbing_permit_number": None,
                "plumbing_permit_status": None,
                "plumbing_permit_status_date": None,
                "master_permit_number": None,
                "master_permit_status": None,
                "master_permit_status_date": None,
            }

        # 2. Safely format the date to a string (e.g., '02/17/2026') for the UI
        status_date = permit.get("status_date")
        formatted_date = status_date.strftime("%m/%d/%Y") if status_date else None

        # 3. Map the data based on the permit type
        permit_type = permit.get("type")

        if permit_type == "Plumbing":
            summary_dict[project_id]["plumbing_permit_number"] = permit.get(
                "permit_number"
            )
            summary_dict[project_id]["plumbing_permit_status"] = permit.get("status")
            summary_dict[project_id]["plumbing_permit_status_date"] = formatted_date

        elif permit_type == "Master":
            summary_dict[project_id]["master_permit_number"] = permit.get(
                "permit_number"
            )
            summary_dict[project_id]["master_permit_status"] = permit.get("status")
            summary_dict[project_id]["master_permit_status_date"] = formatted_date

    # 4. Convert our grouping dictionary back into a flat list of dictionaries
    return list(summary_dict.values())


############## Client ##############
@app.route("/client/<client_id>")
@login_required
def client_view(client_id):
    user = database.get_user(session["user_id"])
    client = database.get_client(client_id)
    client_poc = database.get_client_poc(client_id)
    client_projects = database.get_client_projects(client_id)

    return render_template(
        "client.html",
        user=user,
        client=client,
        client_poc=client_poc,
        client_projects=client_projects,
    )


@app.route("/client_list")
@login_required
def client_list():
    user = database.get_user(session["user_id"])
    clients = database.get_all_clients(user.role)

    return render_template(
        "client_list.html",
        user=user,
        clients=clients,
    )


@app.route("/client-add", methods=["GET", "POST"])
@login_required
def create_client():
    user = database.get_user(session["user_id"])

    name = None
    address = None
    city = None
    state = None
    zip_code = None
    website = None
    phone_number = None
    poc_name = None
    poc_phone_number = None
    poc_email = None

    form = ClientForm()

    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ""
        address = form.address.data
        form.address.data = ""
        city = form.city.data
        form.city.data = ""
        state = form.state.data
        form.state.data = ""
        zip_code = form.zip_code.data
        form.zip_code.data = ""
        website = form.website.data
        form.website.data = ""
        phone_number = form.phone_number.data
        form.phone_number.data = ""
        poc_name = form.poc_name.data
        form.poc_name.data = ""
        poc_phone_number = form.poc_phone_number.data
        form.poc_phone_number.data = ""
        poc_email = form.poc_email.data
        form.poc_email.data = ""

        client_info = {
            "name": name,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "website": website,
            "phone_number": phone_number,
            "poc_name": poc_name,
            "poc_phone_number": poc_phone_number,
            "poc_email": poc_email,
        }

        database.create_client(client_info)

        return redirect(url_for("client_list"))

    return render_template(
        "client_add.html",
        user=user,
        form=form,
        name=name,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        website=website,
        phone_number=phone_number,
        poc_name=poc_name,
        poc_phone_number=poc_phone_number,
        poc_email=poc_email,
    )


@app.route("/client-edit/<client_id>", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    user = database.get_user(session["user_id"])
    client = database.get_client(client_id)
    client_poc = database.get_client_poc(client_id)

    name = client["name"]
    address = client["address"]
    city = client["city"]
    state = client["state"]
    zip_code = client["zip_code"]
    website = client["website"]
    phone_number = client["phone_number"]
    poc_name = client_poc["name"] if client_poc else ""
    poc_phone_number = client_poc["telephone"] if client_poc else ""
    poc_email = client_poc["email"] if client_poc else ""

    form = ClientForm(state=state)

    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ""
        address = form.address.data
        form.address.data = ""
        city = form.city.data
        form.city.data = ""
        state = form.state.data
        form.state.data = ""
        zip_code = form.zip_code.data
        form.zip_code.data = ""
        website = form.website.data
        form.website.data = ""
        phone_number = form.phone_number.data
        form.phone_number.data = ""
        poc_name = form.poc_name.data
        form.poc_name.data = ""
        poc_phone_number = form.poc_phone_number.data
        form.poc_phone_number.data = ""
        poc_email = form.poc_email.data
        form.poc_email.data = ""

        client_info = {
            "client_id": client_id,
            "name": name,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "website": website,
            "phone_number": phone_number,
            "poc_name": poc_name,
            "poc_phone_number": poc_phone_number,
            "poc_email": poc_email,
            "poc_exists": True if client_poc else False,
        }

        database.update_client(client_info)

        return redirect(url_for("client_view", client_id=client_id))

    return render_template(
        "client_edit.html",
        user=user,
        form=form,
        name=name,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        website=website,
        phone_number=phone_number,
        poc_name=poc_name,
        poc_phone_number=poc_phone_number,
        poc_email=poc_email,
    )


############## Search ##############
@app.route("/search")
@login_required
def search():
    user = database.get_user(session["user_id"])

    if not request.args:
        return render_template(
            "search_results.html",
            user=user,
            results="",
        )

    search_criteria = request.args["search_criteria"].strip()
    search_by = request.args["search_by"].strip()

    results = database.search(search_by, search_criteria)

    return render_template(
        "search_results.html",
        user=user,
        search_criteria=search_criteria,
        search_by=search_by,
        results=results,
    )


############## Projects ##############
@app.route("/projects")
@login_required
def projects_list():
    user = database.get_user(session["user_id"])
    projects = database.get_all_projects(user.role)

    return render_template(
        "projects.html",
        user=user,
        projects=projects,
    )


@app.route("/project/<project_id>", methods=["GET", "POST"])
@app.route("/project/<project_id>/<new_project>", methods=["GET", "POST"])
@login_required
def project_view(project_id, new_project=False):
    user = database.get_user(session["user_id"])
    project = database.get_project(project_id)
    client = database.get_client(project["client_id"])
    session["project_id"] = project_id

    if new_project:
        flash("Project has been created")

    # Only initialize forms and data needed for the header and first tab (Notes)
    project_notes_form = ProjectNotesForm()
    notes = database.get_project_notes(project_id)
    proposal_fixtures = database.get_proposal_fixtures(project_id)
    proposal_fixture_notes = database.get_proposal_fixture_notes(project_id)
    proposal_installments = database.get_proposal_installments(project_id)

    proposal_fixtures_form = ProposalFixturesForm()
    proposal_installments_form = ProposalInstallmentsForm()
    proposal_notes_form = ProposalNotesForm()
    proposal_fixture_notes_form = ProposalFixtureNotesForm()
    apply_payment_form = ApplyPaymentForm()
    project_status_form = ProjectStatusForm()
    invoice_create_form = InvoiceCreateForm()
    permit_add_form = PermitsAddForm()
    document_form = DocumentUploadForm()

    project_amount_owed = get_project_amount_owed(project_id)

    if request.method == "POST":
        # Update project status
        if project_status_form.validate_on_submit():
            project_status = project_status_form.project_status.data
            if project_status != project["status"]:
                database.update_project_status(
                    project["project_id"], project_status, session["user_id"]
                )
            return redirect(url_for("project_view", project_id=project["project_id"]))
        else:
            print(f"{project_status_form.errors=}")

        # Add Project Note
        if (
            project_notes_form.validate_on_submit()
            and project_notes_form.project_note_submit.data
        ):
            return project_note_add(project_notes_form, project_id)
        else:
            print(f"{project_notes_form.errors=}")

        # Create invoice
        if (
            invoice_create_form.validate_on_submit()
            and invoice_create_form.invoice_create_submit.data
        ):
            return project_invoice_create(
                request.form.getlist("installment_select"),
                request.form.getlist("billed_amount"),
            )
        else:
            print(f"{invoice_create_form.errors=}")

        # Apply payment
        if (
            apply_payment_form.validate_on_submit()
            and apply_payment_form.apply_payment.data
        ):
            return apply_payment(apply_payment_form)
        else:
            print(f"{apply_payment_form.errors=}")

        # Add Permit
        if (
            permit_add_form.validate_on_submit()
            and permit_add_form.permit_add_submit.data
        ):
            return add_project_permit(permit_add_form)
        else:
            print(f"{permit_add_form.errors=}")

        # Upload Document
        if (
            document_form.validate_on_submit()
            and document_form.upload_document_submit.data
        ):
            return upload_project_document(document_form)
        else:
            print(f"{document_form.errors=}")

    tab = session.pop("active_tab", None)

    return render_template(
        "project.html",
        tab=tab,
        user=user,
        project=project,
        client=client,
        notes=notes,
        project_notes_form=project_notes_form,
        proposal_fixtures_form=proposal_fixtures_form,
        proposal_fixture_notes_form=proposal_fixture_notes_form,
        proposal_installments_form=proposal_installments_form,
        proposal_notes_form=proposal_notes_form,
        proposal_fixtures=proposal_fixtures,
        proposal_fixture_notes=proposal_fixture_notes,
        proposal_fixtures_total=fixtures_total(proposal_fixtures),
        apply_payment_form=apply_payment_form,
        proposal_installments=proposal_installments,
        proposal_installments_total=installments_total(proposal_installments),
        project_status_form=project_status_form,
        project_amount_owed=project_amount_owed,
        document_form=document_form,
    )


# Project Notes
@app.route("/project/<project_id>/notes")
@login_required
def get_project_notes(project_id):
    notes = database.get_project_notes(project_id)
    project_notes_form = ProjectNotesForm()

    return render_template(
        "project_notes.html",
        notes=notes,
        project_notes_form=project_notes_form,
        project_id=project_id,
    )


def project_note_add(form, project_id):
    note = form.project_note.data
    note_info = {
        "project_id": project_id,
        "comment": note,
        "user_id": session["user_id"],
    }
    is_note_created = database.add_project_note(note_info)
    session["active_tab"] = "notes"
    flash(is_note_created)
    return redirect(url_for("project_view", project_id=project_id))


# Project Fixtures
@app.route("/project/<project_id>/fixtures")
@login_required
def get_project_fixtures(project_id):
    fixtures = database.get_project_fixtures(project_id)

    return render_template(
        "project_fixtures.html",
        fixtures=fixtures,
        fixtures_total=fixtures_total(fixtures),
    )


# Project Installments
@app.route("/project/<project_id>/installments")
@login_required
def get_project_installments(project_id):
    installments = database.get_project_installments(project_id)
    project_total = get_project_installment_total(installments)
    payments_total = get_project_payments_total()
    return render_template(
        "project_installments.html",
        installments=installments,
        project_total=project_total,
        payments_total=payments_total,
    )


def get_project_installment_total(installments):
    # Get project total amount
    project_total = 0
    for installment in installments:
        project_total += installment["installment_amount"]
    return project_total


def get_project_payments_total():
    # Get total amount of payments received
    project_payments = database.get_project_payments(session["project_id"])

    payments_total = 0
    for payment in project_payments:
        payments_total += payment["payment_amount"]
    return payments_total


# Project Invoices
@app.route("/project/<project_id>/invoices")
@login_required
def get_project_invoices(project_id):
    invoices = database.get_project_invoices(project_id)
    installments = database.get_project_installments(project_id)
    invoice_items = get_project_invoice_items(invoices)
    invoice_status_form = InvoiceStatusUpdateForm()
    invoice_create_form = InvoiceCreateForm()

    return render_template(
        "project_invoices.html",
        project_id=project_id,
        invoices=invoices,
        installments=installments,
        invoice_status_form=invoice_status_form,
        invoice_create_form=invoice_create_form,
        invoice_items=invoice_items,
    )


def get_project_invoice_items(invoices):
    # Track payments made on invoices and invoice items
    payment_info = {}
    payments_received_total = {}
    invoice_items = {}

    if invoices:
        for invoice in invoices:
            payment = database.get_invoice_payments(invoice["invoice_id"])

            if payment:
                payment_info[invoice["invoice_id"]] = payment
                payments_received_total[invoice["invoice_id"]] = (
                    database.get_invoice_payments_total(invoice["invoice_id"])
                )

            invoice_item = database.get_invoice_items(
                session["project_id"], invoice["invoice_number"]
            )
            if invoice_item:
                invoice_items[invoice_item[0]["invoice_number"]] = invoice_item
    else:
        invoices = []

    print(f"{payment_info=}")
    return invoice_items


def project_invoice_create(selected_installments, billed_invoice_amount):
    selected_installments = selected_installments
    installments = database.get_project_installments(session["project_id"])

    selected_invoices = []
    billed_invoice_amount = billed_invoice_amount
    while "0" in billed_invoice_amount:
        billed_invoice_amount.remove("0")

    zipped_installments = zip(selected_installments, billed_invoice_amount)

    for installment_id, billed_amount in zipped_installments:
        current_installment = [
            d for d in installments if d["installment_id"] == int(installment_id)
        ]

        # INFO: selected_invoices{installment_number: (user_amount, installment_total, billed_amount)}
        selected_invoices.append(
            (
                int(installment_id),
                float(billed_amount),
                current_installment[0]["installment_amount"],
                current_installment[0]["billed_amount"],
            )
        )

    is_invoice_created = database.create_invoice(
        selected_invoices, session["project_id"]
    )
    session["active_tab"] = "invoices"
    flash(is_invoice_created)
    return redirect(url_for("project_view", project_id=session["project_id"]))


# Project Payments
@app.route("/project/<project_id>/payments")
@login_required
def get_project_payments(project_id):
    payments = database.get_project_payments(project_id)
    open_invoices = database.get_open_invoices(project_id)
    project_payments = database.get_project_payments(project_id)
    project_amount_owed = get_project_amount_owed(project_id)

    payment_detail_form = InvoicePaymentForm()
    apply_payment_form = ApplyPaymentForm()

    return render_template(
        "project_payments.html",
        project_id=project_id,
        payments=payments,
        open_invoices=open_invoices,
        project_payments=project_payments,
        payment_detail_form=payment_detail_form,
        apply_payment_form=apply_payment_form,
        project_amount_owed=project_amount_owed,
    )


# Store payment information in the database - finalize application of payment
def apply_payment(form):
    # Payment Information Data
    payment_method = form.payment_method.data
    check_number = form.check_number.data
    payment_amount = form.payment_amount.data
    date_received = form.date_received.data
    payment_note = form.payment_note.data

    payment_information = {
        "project_id": session["project_id"],
        "payment_method": payment_method,
        "check_number": check_number,
        "payment_amount": payment_amount,
        "date_received": date_received,
        "payment_note": payment_note,
    }

    # Invoice Application Data
    try:
        invoice_id_list = [int(x) for x in request.form.getlist("invoice_id")]
        payment_applied_list = [float(x) for x in request.form.getlist("amount_applied")]
        payment_remaining_list = [
            float(x) for x in request.form.getlist("amount_remaining")
        ]
        invoice_status_list = request.form.getlist("invoice_status")
    except (ValueError, TypeError) as e:
        print(f"Payment form data error: {e}")
        flash("Invalid payment data submitted. Please try again.")
        return redirect(url_for("project_view", project_id=session["project_id"]))

    database.insert_payment(payment_information)

    for invoice_id, applied_amount, remaining_amount, invoice_status in list(
        zip(
            invoice_id_list,
            payment_applied_list,
            payment_remaining_list,
            invoice_status_list,
        )
    ):
        if applied_amount > 0:
            payment = {
                "invoice_id": invoice_id,
                "payment_received": applied_amount,
                "payment_remaining": remaining_amount,
                "invoice_status": invoice_status,
                "date_received": date_received,
                "project_id": session["project_id"],
                "check_number": check_number,
            }
            database.apply_payment(payment)

    # database.insert_payment(payment_information)

    session["active_tab"] = "payments"
    flash("Payment applied")
    return redirect(url_for("project_view", project_id=session["project_id"]))


@app.route("/apply_payment/<project_id>", methods=["GET", "POST"])
@login_required
def apply_payment_ajax(project_id):
    payment_form = ApplyPaymentForm().data
    payment_applied_info = []
    check_amount_remaining = float(payment_form["payment_amount"])
    open_invoices = database.get_open_invoices(project_id)

    for invoice in open_invoices:
        payment_dict = None
        check_amount_remaining = round(check_amount_remaining, 2)

        if not payment_form["is_retainage"]:
            # Only retainage is pending
            if invoice["payment_remaining"] - invoice["invoice_retainage"] == 0.00:
                payment_dict = {
                    "invoice_id": invoice["invoice_id"],
                    "invoice_status": invoice["invoice_status"],
                    "amount_remaining": invoice["payment_remaining"],
                    "amount_received": 0.00,
                }
                payment_applied_info.append(payment_dict)
                continue

            # Balance left after payment applied (not including retainage)
            if check_amount_remaining <= (
                round(invoice["payment_remaining"] - invoice["invoice_retainage"], 2)
            ):
                payment_dict = {
                    "invoice_id": invoice["invoice_id"],
                    "invoice_status": "Partial Payment",
                    "amount_received": check_amount_remaining,
                    "amount_remaining": round(
                        invoice["payment_remaining"] - check_amount_remaining, 2
                    ),
                }
                check_amount_remaining = 0

            # Check still has amount left after applying to balance (not including retainage)
            if check_amount_remaining > (
                round(invoice["payment_remaining"] - invoice["invoice_retainage"], 2)
            ):
                payment_dict = {
                    "invoice_id": invoice["invoice_id"],
                    "invoice_status": "Paid",
                    "amount_received": round(
                        invoice["payment_remaining"] - invoice["invoice_retainage"],
                        2,
                    ),
                    "amount_remaining": invoice["invoice_retainage"],
                }

                check_amount_remaining -= round(
                    invoice["payment_remaining"] - invoice["invoice_retainage"], 2
                )
        else:  # Apply payment to retainage
            # Only retainage is pending
            if invoice["payment_remaining"] - invoice["invoice_retainage"] <= 0.00:
                if check_amount_remaining >= invoice["payment_remaining"]:
                    payment_dict = {
                        "invoice_id": invoice["invoice_id"],
                        "invoice_status": "Paid",
                        "amount_received": invoice["payment_remaining"],
                        "amount_remaining": 0.00,
                    }
                    payment_applied_info.append(payment_dict)
                    check_amount_remaining -= round(invoice["payment_remaining"], 2)
                else:
                    payment_dict = {
                        "invoice_id": invoice["invoice_id"],
                        "invoice_status": "Partial Payment",
                        "amount_received": check_amount_remaining,
                        "amount_remaining": round(
                            invoice["payment_remaining"] - check_amount_remaining, 2
                        ),
                    }
                    payment_applied_info.append(payment_dict)
                    check_amount_remaining = 0
            else:
                if check_amount_remaining >= invoice["payment_remaining"]:
                    payment_dict = {
                        "invoice_id": invoice["invoice_id"],
                        "invoice_status": "Paid",
                        "amount_received": check_amount_remaining,
                        "amount_remaining": 0.00,
                    }
                    check_amount_remaining = 0
                else:
                    payment_dict = {
                        "invoice_id": invoice["invoice_id"],
                        "invoice_status": "Partial Payment",
                        "amount_received": check_amount_remaining,
                        "amount_remaining": round(
                            invoice["payment_remaining"] - check_amount_remaining, 2
                        ),
                    }
                    check_amount_remaining = 0

        payment_applied_info.append(payment_dict)

        if check_amount_remaining == 0:
            return jsonify(payment_applied_info)

    return jsonify("")


def get_project_amount_owed(project_id):
    open_invoices = database.get_open_invoices(project_id)
    return sum([invoice["payment_remaining"] for invoice in open_invoices])


# Permits
@app.route("/project/<project_id>/permits")
@login_required
def get_project_permits(project_id):
    permits = database.get_project_permits(project_id)
    permit_add_form = PermitsAddForm()

    # Create a dictionary mapping the city/county ID to its website URL
    permit_websites = {
        str(item.id): item.website for item in database.get_permit_add_information()
    }

    return render_template(
        "project_permits.html",
        permits=permits,
        permit_add_form=permit_add_form,
        permit_websites=permit_websites,
    )


def add_project_permit(permit_add_form):
    permit_info = {
        "project_id": session["project_id"],
        "permit_number": permit_add_form.permit_number.data,
        "type": permit_add_form.permit_type.data,
        "status": permit_add_form.permit_status.data,
        "status_date": permit_add_form.permit_status_date.data,
        # "follow_up_date": None,
        # "follow_up_date": permit_add_form.follow_up_date.data,
        "user_id": session["user_id"],
        "note": permit_add_form.permit_note.data,
        "city_county_id": permit_add_form.city_county.data["id"],
    }

    is_permit_added = database.add_permit(permit_info)

    flash(is_permit_added)
    session["active_tab"] = "permits"
    return redirect(url_for("project_view", project_id=session["project_id"]))


# Documents
@app.route("/project/<project_id>/documents", methods=["GET", "POST"])
@login_required
def get_project_documents(project_id):
    print(request.method)
    documents = database.get_project_docs(project_id)
    document_form = DocumentUploadForm()
    return render_template(
        "project_documents.html",
        documents=documents,
        document_form=document_form,
    )


def upload_project_document(document_upload_form):
    file_storage_obj = document_upload_form.upload_file.data
    document_type = str(document_upload_form.document_type.data).strip()
    comment = document_upload_form.comment.data

    # 2. Extract extension safely
    original_name = file_storage_obj.filename
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "bin"

    # 3. Construct and SECURE the filename immediately
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw_name = f"{session['project_id']}_{document_type}_{timestamp}.{ext}"
    safe_name = secure_filename(raw_name)

    # 4. Upload to S3
    success = upload_file(file_storage_obj, safe_name)

    if success:
        database.upload_document(
            session["project_id"],
            document_type,
            comment,
            session["user_id"],
            safe_name,
        )
        flash("Document uploaded successfully!")
    else:
        flash("S3 Upload Failed")

    document_upload_form.document_type.data = ""
    document_upload_form.comment.data = ""
    document_upload_form.upload_file.data = ""

    session["active_tab"] = "documents"
    # flash(is_document_uploaded)
    return redirect(url_for("project_view", project_id=session["project_id"]))


# Project Proposal
@app.route("/createProposalPDF/<project_id>")
@app.route("/createProposalPDF/<project_id>/<plans_date>")
@login_required
def create_proposal_pdf(project_id, plans_date):
    project_info_temp = database.get_project(project_id)
    project_info = {}
    project_info["project_id"] = project_info_temp["project_id"]
    project_info["name"] = project_info_temp["name"]
    project_info["address"] = project_info_temp["address"]
    project_info["city"] = project_info_temp["city"]
    project_info["state"] = project_info_temp["state"]
    project_info["zip_code"] = project_info_temp["zip_code"]

    logo_data = get_encoded_logo()

    client_info = database.get_project_client(project_id)
    proposal_fixtures = database.get_proposal_fixtures(project_id)
    proposal_fixture_notes = database.get_proposal_fixture_notes(project_id)
    proposal_installments = database.get_proposal_installments(project_id)
    proposal_notes = database.get_proposal_notes(project_id)

    proposal_total = 0
    for fixture in proposal_fixtures:
        proposal_total += fixture["total_per_fixture"]

    proposal_total_words = num2words(proposal_total)
    proposal_total_words = proposal_total_words.replace(",", "")

    plans_date = datetime.strptime(plans_date, "%Y-%m-%d").date()

    return render_template(
        "proposal_print.html",
        logo_data=logo_data,
        project_info=project_info,
        client_info=client_info,
        proposal_fixtures=proposal_fixtures,
        proposal_fixture_notes=proposal_fixture_notes,
        proposal_installments=proposal_installments,
        proposal_notes=proposal_notes,
        proposal_total=proposal_total,
        proposal_total_words=proposal_total_words,
        plans_date=plans_date,
    )


@app.route("/finalizeProposal", methods=["POST"])
@login_required
def finalize_proposal():
    data_string = request.data.decode("utf-8")
    data = json.loads(data_string)

    logo_data = get_encoded_logo()

    # Access data from the dictionary
    project_info = ast.literal_eval(data["projectInfo"])
    project_id = project_info["project_id"]

    plans_date = datetime.strptime(data["plansDate"], "%m/%d/%Y").date()

    # Create proposal in database
    proposal_id = database.create_proposal(project_id, session["user_id"])

    # Get proposal data again for rendering
    client_info = database.get_project_client(project_id)
    proposal_fixtures = database.get_proposal_fixtures(project_id, proposal_id)
    proposal_installments = database.get_proposal_installments(project_id, proposal_id)
    proposal_notes = database.get_proposal_notes(project_id, proposal_id)

    proposal_total = sum(f["total_per_fixture"] for f in proposal_fixtures)
    proposal_total_words = num2words(proposal_total)
    proposal_total_words = proposal_total_words.replace(",", "")

    # Render same template → HTML string
    html_str = render_template(
        "proposal_print.html",
        logo_data=logo_data,
        project_info=project_info,
        client_info=client_info,
        proposal_fixtures=proposal_fixtures,
        proposal_installments=proposal_installments,
        proposal_notes=proposal_notes,
        proposal_total=proposal_total,
        proposal_total_words=proposal_total_words,
        plans_date=plans_date,
    )

    # Convert HTML to PDF in memory
    with suppress_c_warnings():
        pdf_bytes = HTML(
            string=html_str,
            base_url=app.root_path,
        ).write_pdf()

    # upload_file_type = filename.filename.split(".")[-1]
    upload_file_name = f"{session['project_id']}-Proposal-{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

    try:
        # Add document to S3 bucket
        is_document_uploaded = upload_proposal(
            pdf_bytes,
            project_id,
            upload_file_name,
        )
    except Exception as e:
        flash("Error: Unable to upload the proposal to documents")
        return render_template(
            "proposal_print.html",
            project_info=project_info,
            client_info=client_info,
            proposal_fixtures=proposal_fixtures,
            proposal_installments=proposal_installments,
            proposal_notes=proposal_notes,
            proposal_total=proposal_total,
            proposal_total_words=proposal_total_words,
            plans_date=plans_date,
        )

    # Add information to documents table
    database.upload_document(
        session["project_id"],
        "Proposal",
        "",
        session["user_id"],
        upload_file_name,
    )

    # Update proposal items with proposal ID
    database.update_proposal_items_id(project_id, proposal_id)

    # Perform move from temp to permanent
    database.proposal_temp_tables_finalize(project_id)

    flash(is_document_uploaded)

    return url_for(
        "project_view",
        project_id=project_id,
    )


# Project Add
@app.route("/project/add", methods=["GET", "POST"])
@app.route("/project/add/<client_id>", methods=["GET", "POST"])
@login_required
def project_add(client_id=None):
    user = database.get_user(session["user_id"])

    project_id = None
    name = None
    client = None
    address = None
    city = None
    state = None
    zip_code = None
    county = None

    form = ProjectForm()

    # Populate the form with an updated list of clients
    clients = database.get_all_clients(user.role)
    client_options = []
    for client_option in clients:
        client_info = (client_option["client_id"], client_option["name"])
        client_options.append(client_info)
    form.client.choices = client_options

    if form.validate_on_submit():
        project_id = form.project_id.data
        form.project_id.data = ""
        name = form.name.data.title()
        form.name.data = ""
        client = int(form.client.data)
        form.client.data = ""
        address = form.address.data.title()
        form.address.data = ""
        city = form.city.data
        form.city.data = ""
        state = form.state.data
        form.state.data = ""
        zip_code = form.zip_code.data
        form.zip_code.data = ""
        county = form.county.data
        form.county.data = ""

        project_info = {
            "project_id": project_id,
            "name": name,
            "client": client,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "county": county,
        }

        database.create_project(project_info)
        note_info = {
            "project_id": project_id,
            "comment": f"Project Created",
            "user_id": session["user_id"],
        }
        database.add_project_note(note_info)

        return redirect(
            url_for(
                "project_view",
                project_id=project_id,
                new_project=True,
            )
        )

    if client_id:
        client = database.get_client(client_id)

    next_project_id = database.get_next_project_id()

    return render_template(
        "project_add.html",
        user=user,
        form=form,
        project_id=project_id,
        name=name,
        client=client,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        county=county,
        next_project_id=next_project_id,
    )


@app.route("/project/<project_id>/download/<doc_filename>")
@login_required
def download_document(project_id, doc_filename):
    my_file = download_file(doc_filename)
    return Response(
        my_file["Body"].read(),
        mimetype=my_file["ContentType"],
        headers={"Content-Disposition": f"attachment;filename={doc_filename}"},
    )


@app.route("/project/<project_id>/invoice/view/<invoice_number>")
@login_required
def view_invoice(project_id, invoice_number):
    user = database.get_user(session["user_id"])
    project_info = database.get_project(project_id)
    invoice_info = [database.get_invoice(project_id, invoice_number)]
    invoice_items = database.get_invoice_items(project_id, invoice_number)
    client_info = database.get_client(project_info["client_id"])

    today_date = datetime.now().strftime("%m/%d/%Y")

    invoice_total = sum(invoice["invoice_amount"] for invoice in invoice_info)

    return render_template(
        "invoice_print.html",
        user=user,
        project_info=project_info,
        invoice_info=invoice_info,
        invoice_items=invoice_items,
        client_info=client_info,
        today_date=today_date,
        fiat_plumbing=FIAT_PLUMBING,
        invoice_total=invoice_total,
        installment_number=invoice_number,
    )


@app.route("/project/permits/update-permit-status", methods=["POST"])
@login_required
def update_permit_status():
    if request.is_json:
        data = request.get_json()
        permit_id = data.get("permit_id")
        new_status = data.get("new_status")

        if not permit_id or not new_status:
            return jsonify({"error": "Missing permit ID or status"}), 400

        try:
            # Find the permit by ID
            permit = database.get_permit_by_id(permit_id)
            if permit:
                # Update the status on the database
                database.update_permit(permit_id, new_status, session["user_id"])
                flash("Permit status updated successfully")
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Permit status updated successfully",
                        }
                    ),
                    200,
                )

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        return jsonify({"error": "Invalid request"}), 400


############## Helper Methods ##############
def update_invoice_status(project_id, installment_number, installment_status):
    database.update_installment_status(
        project_id, installment_number, installment_status, session["user_id"]
    )


def fixtures_total(fixtures):
    total = sum(fixture["total_per_fixture"] for fixture in fixtures)
    return total


def installments_total(installments):
    total = sum(installment["installment_amount"] for installment in installments)
    return total



@app.route("/clear_proposal_draft/<project_id>", methods=["POST"])
@login_required
def clear_proposal_draft(project_id):
    # Call your cleanup function
    database.proposal_clear_temp_tables(project_id)
    return jsonify(success=True)


@app.route("/clear_proposal_installments/<project_id>", methods=["POST"])
@login_required
def clear_proposal_installments(project_id):
    try:
        database.proposal_clear_installment_temp(project_id)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


def get_encoded_logo():
    # This works on local Windows and Render Linux
    path = os.path.join(app.root_path, "static", "logo.png")
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Warning: Logo not found at {path}")
        return ""


############## Misc. ##############
@app.route("/populateCityStateCounty", methods=["GET", "POST"])
@login_required
def populate_city_state_county():
    results = database.get_city_state_county(request.args["zip_code"])
    return dict(results)


@app.route("/addProposalFixture", methods=["POST"])
@login_required
def add_proposal_fixture():
    # Decode the bytes to a string
    serialized_data = request.data.decode("utf-8")

    # Parse the query string into a dictionary
    parsed_data = urllib.parse.parse_qs(serialized_data)

    # Convert the dictionary values to strings (if needed)
    for key, value in parsed_data.items():
        parsed_data[key] = value[0]

    # Convert is_cost value to true/false
    if "fixture_is_cost" in parsed_data:
        parsed_data["fixture_is_cost"] = True
    else:
        parsed_data["fixture_is_cost"] = False

    # Get values for returning
    fixture_abbreviation = str(parsed_data["fixture_select"]).split(" - ")[0]
    # fixture_name = str(parsed_data["fixture_select"]).split(" - ")[1]

    # Convert to correct format and data types
    parsed_data["fixture_select"] = fixture_abbreviation
    parsed_data["fixture_quantity"] = int(parsed_data["fixture_quantity"])
    parsed_data["fixture_cost"] = float(parsed_data["fixture_cost"])

    database.add_proposal_fixture(parsed_data)

    return get_all_proposal_fixtures(parsed_data["project_id"])


def get_all_proposal_fixtures(project_id):
    fixtures_added = []
    fixtures = database.get_proposal_fixtures(project_id)

    for fixture in fixtures:
        fixtures_added.append(
            {
                "fixture_id": fixture["fixture_id"],
                "fixture_name": fixture["fixture_name"],
                "fixture_abbreviation": fixture["fixture_abbreviation"],
                "fixture_quantity": fixture["quantity"],
                "fixture_cost": fixture["cost_per_fixture"],
                "fixture_is_cost": fixture["is_cost"],
                "fixture_total": fixture["total_per_fixture"],
            }
        )

    return jsonify(fixtures_added)


@app.route("/addProposalFixtureNote", methods=["POST"])
@login_required
def add_proposal_fixture_note():
    # Decode the bytes to a string
    serialized_data = request.data.decode("utf-8")

    # Parse the query string into a dictionary
    parsed_data = urllib.parse.parse_qs(serialized_data)

    # Convert the dictionary values to strings (if needed)
    for key, value in parsed_data.items():
        parsed_data[key] = value[0]

    database.add_proposal_fixture_note(parsed_data)

    fixture_notes_added = []
    fixture_notes = database.get_proposal_fixture_notes(parsed_data["project_id"])

    if fixture_notes:
        for note in fixture_notes:
            fixture_notes_added.append(
                {
                    "fixture_note_id": note["fixture_note_id"],
                    "fixture_note": note["fixture_note"],
                }
            )
    return jsonify(fixture_notes_added)


@app.route(
    "/deleteProposalFixtureNote/<fixture_note_id>/<project_id>", methods=["POST"]
)
@login_required
def delete_proposal_fixture_note(fixture_note_id, project_id):
    database.delete_proposal_fixture_note(fixture_note_id)

    return get_all_proposal_fixture_notes(project_id)


def get_all_proposal_fixture_notes(project_id):
    fixture_notes_added = []
    fixture_notes = database.get_proposal_fixture_notes(project_id)

    for note in fixture_notes:
        fixture_notes_added.append(
            {
                "fixture_note_id": note["fixture_note_id"],
                "fixture_note": note["fixture_note"],
            }
        )

    return jsonify(fixture_notes_added)


@app.route("/deleteProposalFixture/<fixture_id>/<project_id>", methods=["POST"])
@login_required
def delete_proposal_fixture(fixture_id, project_id):
    # database.add_proposal_fixture(fixture_id, table_name="project_proposal_fixtures")
    database.delete_proposal_fixture(fixture_id)
    return get_all_proposal_fixtures(project_id)


@app.route("/addProposalInstallment", methods=["POST"])
@login_required
def add_proposal_installment():
    # Decode the bytes to a string
    serialized_data = request.data.decode("utf-8")

    # Parse the query string into a dictionary
    parsed_data = urllib.parse.parse_qs(serialized_data)

    # Convert the dictionary values to strings (if needed)
    for key, value in parsed_data.items():
        parsed_data[key] = value[0]

    # Convert to correct format and data types
    parsed_data["installment_amount"] = float(parsed_data["installment_amount"])

    database.add_proposal_installment(parsed_data)

    installments_added = []
    installments = database.get_proposal_installments(parsed_data["project_id"])

    for installment in installments:
        installments_added.append(
            {
                "installment_id": installment["installment_id"],
                "installment_number": installment["installment_number"],
                "installment_category": installment["installment_category"],
                "installment_amount": installment["installment_amount"],
            }
        )
    return jsonify(installments_added)


@app.route("/addProposalNote", methods=["POST"])
@login_required
def add_proposal_note():
    # Decode the bytes to a string
    serialized_data = request.data.decode("utf-8")

    # Parse the query string into a dictionary
    parsed_data = urllib.parse.parse_qs(serialized_data)

    # Convert the dictionary values to strings (if needed)
    for key, value in parsed_data.items():
        parsed_data[key] = value[0]

    database.add_proposal_note(parsed_data)

    notes_added = []
    notes = database.get_proposal_notes(parsed_data["project_id"])

    for note in notes:
        notes_added.append(
            {
                "note_id": note["note_id"],
                "note": note["note"],
            }
        )
    return jsonify(notes_added)


@app.route("/deleteProposalNote/<note_id>/<project_id>", methods=["POST"])
@login_required
def delete_proposal_note(note_id, project_id):
    database.delete_proposal_note(note_id)

    return get_all_proposal_notes(project_id)


def get_all_proposal_notes(project_id):
    notes_added = []
    notes = database.get_proposal_notes(project_id)

    for note in notes:
        notes_added.append(
            {
                "note_id": note["note_id"],
                "note": note["note"],
            }
        )

    return jsonify(notes_added)


@app.template_filter()
def format_currency(value):
    # locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    value = format(value, ",.2f")

    if not value:
        return "$0.00"
        # return locale.currency(0, symbol=True, grouping=True)

    return "$" + str(value)
    # return locale.currency(value, symbol=True, grouping=True)


@app.template_filter()
def calculate_due_date(value):
    return (datetime.now() + timedelta(days=DAYS_UNTIL_DUE)).strftime("%m/%d/%Y")


@app.template_filter()
def get_today_date(value):
    return datetime.now().date().strftime("%m/%d/%Y")


if __name__ == "__main__":
    # Fetches the environment variable. If it doesn't exist, it defaults to "False" for safety.
    is_debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", debug=is_debug)
