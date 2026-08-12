import logging
import mimetypes
import time
import ast
import base64
import json
import os
import smtplib
import sys
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
from flask_wtf.csrf import CSRFError, CSRFProtect
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
from documents import upload_file, download_file, upload_proposal, list_company_doc_folders, upload_company_doc, list_coi_year_folders, delete_file
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
    InspectionAddForm,
    COIEditForm,
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

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
AOL_EMAIL = os.getenv("AOL_EMAIL")
AOL_APP_PASSWORD = os.getenv("AOL_APP_PASSWORD")
AFIAT_GMAIL_EMAIL = os.getenv("AFIAT_GMAIL_EMAIL")
AFIAT_GMAIL_APP_PASSWORD = os.getenv("AFIAT_GMAIL_APP_PASSWORD")
VENTURA_CLIENT_ID = "10"
COMPANY_DOC_TYPES = [
    "State License - Plumbing",
    "State License - Contractor",
    "BTR - Plumbing",
    "BTR - Contractor",
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_KEY")
csrf = CSRFProtect(app)
logging.getLogger("database").setLevel(logging.DEBUG)
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
app.jinja_env.filters["jsonify"] = jsonify

engine = db_connect()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


############## Login/Logout ##############
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("Your session has expired, please log in again.")
    return redirect(url_for("login"))


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("Your form session expired, please try again.")
    return redirect(url_for("login"))


@login_manager.user_loader
def load_user(user_id):
    user_dict = database.get_user(user_id)
    if not user_dict:
        return None
    return users.Users(user_dict)


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        login_form = LoginForm()

        if login_form.validate_on_submit():
            email = login_form.email.data
            password = login_form.password.data

            user_db_password = database.get_user_password(email)

            if user_db_password:
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
        app.logger.error("Login error: %s", e)
        return redirect(url_for("login"))


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    signup_form = SignUpForm()

    if signup_form.validate_on_submit():
        first_name = signup_form.first_name.data
        last_name = signup_form.last_name.data
        email = signup_form.email.data
        password = signup_form.password.data

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
                app.logger.error("Sign-up error: %s", e)

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
def send_reset_email(recipient, reset_url):
    html_body = f"""
    <html><body>
    <p>Hello,</p>
    <p>We received a request to reset your password for your Fiat Plumbing account.
    Click the link below to set a new password. This link expires in 1 hour.</p>
    <p><a href="{reset_url}">Reset My Password</a></p>
    <p>If you did not request a password reset, you can ignore this email.</p>
    <br>
    <p>Thank you,<br>
    <strong>{FIAT_PLUMBING["company_name"]}</strong><br>
    {FIAT_PLUMBING["phone_number"]}<br>
    {FIAT_PLUMBING["email"]}</p>
    </body></html>
    """

    msg = MIMEMultipart("mixed")
    msg["From"] = GMAIL_EMAIL
    msg["To"] = recipient
    msg["Subject"] = "Fiat Plumbing — Password Reset Request"
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        smtp.sendmail(GMAIL_EMAIL, recipient, msg.as_string())


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    forgot_password_form = ForgotPasswordForm()

    if forgot_password_form.validate_on_submit():
        email = forgot_password_form.email.data
        user = database.get_user_from_email(email)

        if user:
            token = serializer.dumps(email, salt="password-reset-salt")
            reset_url = url_for("reset_password", token=token, _external=True)
            try:
                send_reset_email(email, reset_url)
            except Exception as e:
                app.logger.error("Password reset email error: %s", e)

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
            app.logger.error("Error updating password: %s", e)

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
                app.logger.error("Error updating password: %s", e)

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
                    app.logger.error("Error updating email: %s", e)

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
    permits_summary = database.get_permit_dashboard_summary(user.role)

    # Graph data
    status_counts = database.get_projects_status_summary(user.role)
    status_summary_labels = [item["status"] for item in status_counts]
    status_summary_values = [item["count"] for item in status_counts]

    finance_counts = database.get_projects_finance_summary(user.role)
    inspections_summary = database.get_all_inspections(user.role)

    return render_template(
        "home.html",
        user=user,
        clients=clients,
        projects=projects,
        status_summary_labels=status_summary_labels,
        status_summary_values=status_summary_values,
        finance_counts=finance_counts,
        permits_summary=permits_summary,
        inspections_summary=inspections_summary,
    )


############## Client ##############
@app.route("/client/<client_id>")
@login_required
def client_view(client_id):
    user = database.get_user(session["user_id"])
    client = database.get_client(client_id)
    contacts = database.get_client_contacts(client_id)
    client_projects = database.get_client_projects(client_id)

    return render_template(
        "client.html",
        user=user,
        client=client,
        contacts=contacts,
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
        address = form.address.data
        city = form.city.data
        state = form.state.data
        zip_code = form.zip_code.data
        website = form.website.data
        phone_number = form.phone_number.data
        poc_name = form.poc_name.data
        poc_phone_number = form.poc_phone_number.data
        poc_email = form.poc_email.data

        client_info = {
            "name": name,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "website": website,
            "phone_number": phone_number,
            "is_test": form.is_test.data and user.role == "developer",
        }

        client_id = database.create_client(client_info)

        if client_id and any([poc_name, poc_phone_number, poc_email]):
            database.add_client_contact(client_id, poc_name, poc_phone_number, poc_email)

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

    name = client["name"]
    address = client["address"]
    city = client["city"]
    state = client["state"]
    zip_code = client["zip_code"]
    website = client["website"]
    phone_number = client["phone_number"]

    form = ClientForm(state=state)

    if not form.is_submitted() and client.get("is_test") and user.role == "developer":
        form.is_test.data = True

    if form.validate_on_submit():
        client_info = {
            "client_id": client_id,
            "name": form.name.data,
            "address": form.address.data,
            "city": form.city.data,
            "state": form.state.data,
            "zip_code": form.zip_code.data,
            "website": form.website.data,
            "phone_number": form.phone_number.data,
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
    )


@app.route("/client/<client_id>/contacts/add", methods=["POST"])
@login_required
def client_contact_add(client_id):
    name = request.form.get("name", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip()
    title = request.form.get("title", "").strip()
    database.add_client_contact(client_id, name, telephone, email, title)
    return redirect(url_for("client_view", client_id=client_id))


@app.route("/client/<client_id>/contacts/<int:contact_id>/edit", methods=["POST"])
@login_required
def client_contact_edit(client_id, contact_id):
    name = request.form.get("name", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip()
    title = request.form.get("title", "").strip()
    database.update_client_contact(contact_id, name, telephone, email, title)
    return redirect(url_for("client_view", client_id=client_id))


@app.route("/client/<client_id>/contacts/<int:contact_id>/delete", methods=["POST"])
@login_required
def client_contact_delete(client_id, contact_id):
    database.delete_client_contact(contact_id)
    return redirect(url_for("client_view", client_id=client_id))


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
    inspection_add_form = InspectionAddForm()
    document_form = DocumentUploadForm()

    project_amount_owed = get_project_amount_owed(project_id)
    project_documents = database.get_project_docs(project_id)
    doc_contacts = [c for c in database.get_client_contacts(project["client_id"]) if c["email"]]
    doc_default_from_email = AFIAT_GMAIL_EMAIL if str(project["client_id"]) == VENTURA_CLIENT_ID else AOL_EMAIL
    doc_from_emails = [
        {"email": AOL_EMAIL, "label": f"AOL ({AOL_EMAIL})"},
        {"email": AFIAT_GMAIL_EMAIL, "label": f"Gmail ({AFIAT_GMAIL_EMAIL})"},
    ]

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
            app.logger.debug(
                "project_status_form errors: %s", project_status_form.errors
            )

        # Add Project Note
        if (
            project_notes_form.validate_on_submit()
            and project_notes_form.project_note_submit.data
        ):
            return project_note_add(project_notes_form, project_id)
        else:
            app.logger.debug("project_notes_form errors: %s", project_notes_form.errors)

        # Create invoice
        if (
            invoice_create_form.validate_on_submit()
            and invoice_create_form.invoice_create_submit.data
        ):
            return project_invoice_create(
                request.form.getlist("installment_select"),
                request.form.getlist("billed_amount"),
                project_id,
            )
        else:
            app.logger.debug(
                "invoice_create_form errors: %s", invoice_create_form.errors
            )

        # Apply payment
        if (
            apply_payment_form.validate_on_submit()
            and apply_payment_form.apply_payment.data
        ):
            return apply_payment(apply_payment_form, project_id)
        else:
            app.logger.debug("apply_payment_form errors: %s", apply_payment_form.errors)

        # Add Permit
        if (
            permit_add_form.validate_on_submit()
            and permit_add_form.permit_add_submit.data
        ):
            return add_project_permit(permit_add_form, project_id)
        else:
            app.logger.debug("permit_add_form errors: %s", permit_add_form.errors)

        # Add Inspection (legacy non-AJAX fallback)
        if (
            inspection_add_form.validate_on_submit()
            and inspection_add_form.inspection_add_submit.data
        ):
            return add_project_inspection(inspection_add_form, project_id)
        else:
            app.logger.debug(
                "inspection_add_form errors: %s", inspection_add_form.errors
            )

        # Upload Document
        if (
            document_form.validate_on_submit()
            and document_form.upload_document_submit.data
        ):
            return upload_project_document(document_form, project_id)
        else:
            app.logger.debug("document_form errors: %s", document_form.errors)

    tab = session.pop("active_tab", None) or request.args.get("tab")

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
        project_documents=project_documents,
        doc_contacts=doc_contacts,
        doc_default_from_email=doc_default_from_email,
        doc_from_emails=doc_from_emails,
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
    payments_total = get_project_payments_total(project_id)
    return render_template(
        "project_installments.html",
        installments=installments,
        project_total=project_total,
        payments_total=payments_total,
    )


def get_project_installment_total(installments):
    return sum(installment["installment_amount"] for installment in installments)


def get_project_payments_total(project_id):
    project_payments = database.get_project_payments(project_id)
    return sum(payment["payment_amount"] for payment in project_payments)


# Project Invoices
@app.route("/project/<project_id>/invoices")
@login_required
def get_project_invoices(project_id):
    invoices = database.get_project_invoices(project_id)
    installments = database.get_project_installments(project_id)
    invoice_items = get_project_invoice_items(invoices, project_id)
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


def get_project_invoice_items(invoices, project_id):
    invoice_items = {}
    if not invoices:
        return invoice_items

    all_items = database.get_all_invoice_items(project_id)
    for item in all_items:
        key = item["invoice_number"]
        invoice_items.setdefault(key, []).append(item)

    return invoice_items


def project_invoice_create(selected_installments, billed_invoice_amount, project_id):
    installments = database.get_project_installments(project_id)

    selected_invoices = []
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

    is_invoice_created = database.create_invoice(selected_invoices, project_id)
    session["active_tab"] = "invoices"
    flash(is_invoice_created)
    return redirect(url_for("project_view", project_id=project_id))


# Project Payments
@app.route("/project/<project_id>/payments")
@login_required
def get_project_payments(project_id):
    payments = database.get_project_payments(project_id)
    open_invoices = database.get_open_invoices(project_id)
    project_amount_owed = get_project_amount_owed(project_id)

    payment_detail_form = InvoicePaymentForm()
    apply_payment_form = ApplyPaymentForm()

    return render_template(
        "project_payments.html",
        project_id=project_id,
        payments=payments,
        open_invoices=open_invoices,
        project_payments=payments,
        payment_detail_form=payment_detail_form,
        apply_payment_form=apply_payment_form,
        project_amount_owed=project_amount_owed,
    )


# Store payment information in the database - finalize application of payment
def apply_payment(form, project_id):
    # Payment Information Data
    payment_method = form.payment_method.data
    check_number = form.check_number.data
    payment_amount = form.payment_amount.data
    date_received = form.date_received.data
    payment_note = form.payment_note.data

    payment_information = {
        "project_id": project_id,
        "payment_method": payment_method,
        "check_number": check_number,
        "payment_amount": payment_amount,
        "date_received": date_received,
        "payment_note": payment_note,
    }

    # Invoice Application Data
    try:
        invoice_id_list = [int(x) for x in request.form.getlist("invoice_id")]
        payment_applied_list = [
            float(x) for x in request.form.getlist("amount_applied")
        ]
        payment_remaining_list = [
            float(x) for x in request.form.getlist("amount_remaining")
        ]
        invoice_status_list = request.form.getlist("invoice_status")
    except (ValueError, TypeError) as e:
        app.logger.error("Payment form data error: %s", e)
        flash("Invalid payment data submitted. Please try again.")
        return redirect(url_for("project_view", project_id=project_id))

    database.insert_payment(payment_information)

    for invoice_id, applied_amount, remaining_amount, invoice_status in zip(
        invoice_id_list,
        payment_applied_list,
        payment_remaining_list,
        invoice_status_list,
    ):
        if applied_amount > 0:
            payment = {
                "invoice_id": invoice_id,
                "payment_received": applied_amount,
                "payment_remaining": remaining_amount,
                "invoice_status": invoice_status,
                "date_received": date_received,
                "project_id": project_id,
                "check_number": check_number,
            }
            database.apply_payment(payment)

    session["active_tab"] = "payments"
    flash("Payment applied")
    return redirect(url_for("project_view", project_id=project_id))


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

        if check_amount_remaining <= 0:
            return jsonify(payment_applied_info)

    return jsonify(payment_applied_info)


def get_project_amount_owed(project_id):
    open_invoices = database.get_open_invoices(project_id)
    return sum(invoice["payment_remaining"] for invoice in open_invoices)


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


def add_project_permit(permit_add_form, project_id):
    permit_info = {
        "project_id": project_id,
        "permit_number": permit_add_form.permit_number.data,
        "type": permit_add_form.permit_type.data,
        "status": permit_add_form.permit_status.data,
        "status_date": permit_add_form.permit_status_date.data,
        "user_id": session["user_id"],
        "note": permit_add_form.permit_note.data,
        "city_county_id": permit_add_form.city_county.data["id"],
    }

    is_permit_added = database.add_permit(permit_info)

    flash(is_permit_added)
    session["active_tab"] = "permits"
    return redirect(url_for("project_view", project_id=project_id))


# Documents
@app.route("/project/<project_id>/documents", methods=["GET", "POST"])
@login_required
def get_project_documents(project_id):
    documents = database.get_project_docs(project_id)
    document_form = DocumentUploadForm()
    return render_template(
        "project_documents.html",
        documents=documents,
        document_form=document_form,
    )


@app.route("/project/<project_id>/documents/send", methods=["POST"])
@login_required
def send_project_documents(project_id):
    from_email = request.form.get("from_email", "").strip()
    to_ids = request.form.getlist("to_ids")
    cc_ids = request.form.getlist("cc_ids")
    doc_filenames = request.form.getlist("doc_filenames")
    body = request.form.get("body", "").strip()

    if not to_ids:
        return jsonify({"success": False, "error": "At least one 'To' recipient is required."})
    if not doc_filenames:
        return jsonify({"success": False, "error": "At least one document must be selected."})

    try:
        project = database.get_project(project_id)
        user = database.get_user(session["user_id"])
        all_contacts = database.get_client_contacts(project["client_id"])
        contacts_by_id = {str(c["id"]): c for c in all_contacts}

        to_contacts = [contacts_by_id[i] for i in to_ids if i in contacts_by_id]
        cc_contacts = [contacts_by_id[i] for i in cc_ids if i in contacts_by_id]
        all_docs = database.get_project_docs(project_id)
        selected_docs = [d for d in all_docs if d["filename"] in doc_filenames]

        project_address = project['address']

        if not body:
            greeting = f"Hello {to_contacts[0]['name']}," if len(to_contacts) == 1 else "Hello,"
            doc_phrase = "document" if len(selected_docs) == 1 else "documents"
            doc_lines = "\n".join(f"- {d['type']}" for d in selected_docs)
            body = (
                f"{greeting}\n\n"
                f"Please see attached the following {doc_phrase} for {project_address}:\n"
                f"{doc_lines}\n\n\n"
                f"Thank you,\n"
                f"{user.first_name} {user.last_name}\n"
                f"Fiat Plumbing and General Contractors, Inc."
            )

        to_emails = [c["email"] for c in to_contacts]
        cc_emails = [c["email"] for c in cc_contacts]

        msg = MIMEMultipart("mixed")
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        msg["Subject"] = f"Fiat Plumbing — Documents for {project_address}"
        html_body = body.replace("\n", "<br>")
        msg.attach(MIMEText(f"<html><body><p>{html_body}</p></body></html>", "html"))

        for doc in selected_docs:
            response = download_file(doc["filename"])
            data = response["Body"].read()
            ext = ("." + doc["filename"].rsplit(".", 1)[-1]) if "." in doc["filename"] else ""
            display = f"{doc['type']} ({doc['upload_date'].strftime('%m-%d-%Y')}){ext}"
            part = MIMEApplication(data, Name=display)
            part["Content-Disposition"] = f'attachment; filename="{display}"'
            msg.attach(part)

        if from_email == AFIAT_GMAIL_EMAIL:
            host, port, login, pwd = "smtp.gmail.com", 587, AFIAT_GMAIL_EMAIL, AFIAT_GMAIL_APP_PASSWORD
        else:
            host, port, login, pwd = "smtp.aol.com", 587, AOL_EMAIL, AOL_APP_PASSWORD

        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(login, pwd)
            smtp.sendmail(from_email, to_emails + cc_emails, msg.as_string())

        doc_names = ", ".join(d["type"] for d in selected_docs)
        database.add_project_note({
            "project_id": project_id,
            "comment": f"Documents emailed to client: {doc_names}",
            "user_id": session["user_id"],
        })
        session["active_tab"] = "documents"
        flash("Documents emailed successfully.")
        return jsonify({"success": True})

    except Exception as e:
        app.logger.error("send_project_documents() - Error: %s", e)
        return jsonify({"success": False, "error": str(e)})


def upload_project_document(document_upload_form, project_id):
    file_storage_obj = document_upload_form.upload_file.data
    document_type = str(document_upload_form.document_type.data).strip()
    comment = document_upload_form.comment.data

    # 2. Extract extension safely
    original_name = file_storage_obj.filename
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "bin"

    # 3. Construct and SECURE the filename immediately
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw_name = f"{project_id}_{document_type}_{timestamp}.{ext}"
    safe_name = secure_filename(raw_name)

    # 4. Upload to S3
    success = upload_file(file_storage_obj, safe_name)

    if success:
        database.upload_document(
            project_id,
            document_type,
            comment,
            session["user_id"],
            safe_name,
        )
        flash("Document uploaded successfully!")
    else:
        flash("S3 Upload Failed")

    session["active_tab"] = "documents"
    return redirect(url_for("project_view", project_id=project_id))


# Project Proposal
@app.route("/createProposalPDF/<project_id>")
@app.route("/createProposalPDF/<project_id>/<plans_date>")
@login_required
def create_proposal_pdf(project_id, plans_date=None):
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

    try:
        plans_date = datetime.strptime(plans_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        flash("Invalid plans date.")
        return redirect(url_for("project_view", project_id=project_id))

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
    upload_file_name = (
        f"{project_id}-Proposal-{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    )

    try:
        # Add document to S3 bucket
        is_document_uploaded = upload_proposal(
            pdf_bytes,
            project_id,
            upload_file_name,
        )
    except Exception as e:
        app.logger.error("Proposal upload error: %s", e)
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
        project_id,
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


@app.route("/project/<project_id>/reset", methods=["POST"])
@login_required
def reset_project(project_id):
    project = database.get_project(project_id)

    if not project or not project.get("is_test"):
        return "Not found", 404

    database.reset_project(project_id)
    flash("Project has been reset.")
    return redirect(url_for("project_view", project_id=project_id))


@app.route("/project/<project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    project = database.get_project(project_id)

    if not project or not project.get("is_test"):
        return "Not found", 404

    database.delete_project(project_id)
    flash(f"Project '{project['name']}' has been deleted.")
    return redirect(url_for("projects_list"))


@app.route("/client/<client_id>/delete", methods=["POST"])
@login_required
def delete_client(client_id):
    client = database.get_client(client_id)

    if not client or not client.get("is_test"):
        return "Not found", 404

    database.delete_client(client_id)
    flash(f"Client '{client['name']}' and all associated projects have been deleted.")
    return redirect(url_for("client_list"))


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

    # Populate the form with an updated list of clients, split by is_test
    clients = database.get_all_clients(user.role)
    test_client_options = [
        (c["client_id"], c["name"]) for c in clients if c.get("is_test")
    ]
    regular_client_options = [
        (c["client_id"], c["name"]) for c in clients if not c.get("is_test")
    ]
    form.client.choices = test_client_options + regular_client_options

    if form.validate_on_submit():
        project_id = form.project_id.data
        name = form.name.data.title()
        client = int(form.client.data)
        address = form.address.data.title()
        city = form.city.data
        state = form.state.data
        zip_code = form.zip_code.data
        county = form.county.data
        is_test = form.is_test.data and user.role == "developer"

        if is_test:
            selected_client = database.get_client(client)
            if not selected_client or not selected_client.get("is_test"):
                flash("A test project must be attached to a test client.")
                if client_id:
                    return redirect(url_for("project_add", client_id=client_id))
                return redirect(url_for("project_add"))

        project_info = {
            "project_id": project_id,
            "name": name,
            "client": client,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "county": county,
            "is_test": is_test,
        }

        database.create_project(project_info)
        note_info = {
            "project_id": project_id,
            "comment": "Project Created",
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
        if client and client.get("is_test") and user.role == "developer":
            form.is_test.data = True

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
        test_client_options=test_client_options,
        regular_client_options=regular_client_options,
    )


@app.route("/project/<project_id>/download/<doc_filename>")
@login_required
def download_document(project_id, doc_filename):
    my_file = download_file(doc_filename)
    safe_name = secure_filename(doc_filename)
    return Response(
        my_file["Body"].read(),
        mimetype=my_file["ContentType"],
        headers={"Content-Disposition": f"attachment;filename={safe_name}"},
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


@app.route("/project/<project_id>/inspections")
@login_required
def get_project_inspections_tab(project_id):
    inspections = database.get_project_inspections(project_id)
    inspection_add_form = InspectionAddForm()
    building_dept_urls = {
        str(dept.id): dept.web_portal
        for dept in database.get_building_departments_list()
    }
    return render_template(
        "project_inspections.html",
        inspections=inspections,
        inspection_add_form=inspection_add_form,
        building_dept_urls=building_dept_urls,
        project_id=project_id,
    )


def add_project_inspection(inspection_add_form, project_id):
    inspection_info = {
        "project_id": project_id,
        "building_dept_id": (
            inspection_add_form.building_dept.data["id"]
            if inspection_add_form.building_dept.data
            else None
        ),
        "inspection_type": inspection_add_form.inspection_type.data,
        "scheduled_date": inspection_add_form.scheduled_date.data,
        "scheduled_time": inspection_add_form.scheduled_time.data,
        "status": inspection_add_form.status.data,
        "status_date": inspection_add_form.status_date.data,
        "notes": inspection_add_form.notes.data,
    }
    result = database.add_inspection(inspection_info)
    flash(result)
    session["active_tab"] = "inspections"
    return redirect(url_for("project_view", project_id=project_id))


@app.route("/project/<project_id>/add-inspection", methods=["POST"])
@login_required
def add_inspection_ajax(project_id):
    form = InspectionAddForm()
    if form.validate_on_submit():
        inspection_info = {
            "project_id": project_id,
            "building_dept_id": (
                form.building_dept.data["id"] if form.building_dept.data else None
            ),
            "inspection_type": form.inspection_type.data,
            "scheduled_date": form.scheduled_date.data,
            "scheduled_time": form.scheduled_time.data,
            "status": form.status.data,
            "status_date": form.status_date.data,
            "notes": form.notes.data,
            "inspection_number": form.inspection_number.data,
            "inspector_name": form.inspector_name.data,
        }
        database.add_inspection(inspection_info)
        return jsonify({"status": "success", "message": "Inspection added"})
    errors = [
        f"{form[field].label.text}: {error}"
        for field, errs in form.errors.items()
        for error in errs
        if field != "csrf_token"
    ]
    return jsonify({"status": "error", "errors": errors}), 400


@app.route("/project/inspections/update-status", methods=["POST"])
@login_required
def update_inspection_status():
    if request.is_json:
        data = request.get_json()
        inspection_id = data.get("inspection_id")
        new_status = data.get("new_status")

        if not inspection_id or not new_status:
            return jsonify({"error": "Missing inspection ID or status"}), 400

        try:
            database.update_inspection_status(inspection_id, new_status)
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Inspection status updated successfully",
                    }
                ),
                200,
            )
        except Exception as e:
            app.logger.error("Error updating inspection status: %s", e)
            return jsonify({"error": "An internal error occurred"}), 500

    return jsonify({"error": "Invalid request"}), 400


@app.route("/project/permits/update-permit-status", methods=["POST"])
@login_required
def update_permit_status():
    if request.is_json:
        data = request.get_json()
        permit_id = data.get("permit_id")
        new_status = data.get("new_status")

        if not permit_id or not new_status:
            return jsonify({"error": "Missing permit ID or status"}), 400

        permit = database.get_permit_by_id(permit_id)
        if not permit:
            return jsonify({"error": "Permit not found"}), 404

        try:
            database.update_permit(permit_id, new_status, session["user_id"])
            return (
                jsonify(
                    {"success": True, "message": "Permit status updated successfully"}
                ),
                200,
            )
        except Exception as e:
            app.logger.error("Error updating permit status: %s", e)
            return jsonify({"error": "An internal error occurred"}), 500


############## Admin - COI ##############
def get_coverage_period():
    today = date.today()
    if today.month >= 3:
        coverage_start = date(today.year, 3, 1)
    else:
        coverage_start = date(today.year - 1, 3, 1)
    coverage_end = date(coverage_start.year + 1, 3, 31)
    return coverage_start, coverage_end


def send_coi_email(
    dept,
    coverage_start,
    docs,
    state_license_plumbing_key=None,
    state_license_contractor_key=None,
    btr_plumbing_key=None,
    btr_contractor_key=None,
    coi_year=None,
):
    coverage_folder = coi_year or f"{coverage_start.year}-{coverage_start.year + 1}"
    entity_name = dept["entity"]
    recipient = dept["primary_email"]

    def key_year(s3_key):
        parts = s3_key.split("/")
        return parts[2] if len(parts) > 2 else ""

    attachments = []
    doc_names = []
    subject_parts = []

    if docs.get("coi"):
        attachments.append(
            (
                f"company-docs/certificates-of-liability/{coverage_folder}/{entity_name}.pdf",
                f"{entity_name} - COI.pdf",
            )
        )
        doc_names.append("Certificate of Liability Insurance")
        subject_parts.append(f"COI {coverage_folder}")

    if docs.get("sl_plumbing") and state_license_plumbing_key:
        attachments.append((state_license_plumbing_key, state_license_plumbing_key.split("/")[-1]))
        doc_names.append("State License (Plumbing)")
        subject_parts.append(f"State License Plumbing {key_year(state_license_plumbing_key)}")

    if docs.get("sl_contractor") and state_license_contractor_key:
        attachments.append((state_license_contractor_key, state_license_contractor_key.split("/")[-1]))
        doc_names.append("State License (Contractor)")
        subject_parts.append(f"State License Contractor {key_year(state_license_contractor_key)}")

    if docs.get("btr_plumbing") and btr_plumbing_key:
        attachments.append((btr_plumbing_key, btr_plumbing_key.split("/")[-1]))
        doc_names.append("Local Business Tax Receipt (Plumbing)")
        subject_parts.append(f"BTR Plumbing {key_year(btr_plumbing_key)}")

    if docs.get("btr_contractor") and btr_contractor_key:
        attachments.append((btr_contractor_key, btr_contractor_key.split("/")[-1]))
        doc_names.append("Local Business Tax Receipt (Contractor)")
        subject_parts.append(f"BTR Contractor {key_year(btr_contractor_key)}")

    if len(doc_names) == 1:
        doc_list = doc_names[0]
    elif len(doc_names) == 2:
        doc_list = f"{doc_names[0]} and {doc_names[1]}"
    else:
        doc_list = ", ".join(doc_names[:-1]) + f", and {doc_names[-1]}"

    subject_doc_list = ", ".join(subject_parts)

    html_body = f"""
    <html><body>
    <p>Hello,</p>
    <p>Please see attached {doc_list} for Fiat Plumbing & General Contractor, Inc. for the {coverage_folder} coverage period.</p>
    <p>Should you have any questions or require additional information, please do not
    hesitate to contact us.</p>
    <br>
    <p>Thank you,<br>
    <strong>{FIAT_PLUMBING["company_name"]}</strong><br>
    {FIAT_PLUMBING["phone_number"]}<br>
    {FIAT_PLUMBING["email"]}</p>
    </body></html>
    """

    msg = MIMEMultipart("mixed")
    msg["From"] = AOL_EMAIL
    msg["To"] = recipient
    msg["Subject"] = (
        f"Fiat Plumbing & General Contractor, Inc. - {subject_doc_list} — {entity_name}"
    )
    msg.attach(MIMEText(html_body, "html"))

    for s3_key, display_name in attachments:
        try:
            response = download_file(s3_key)
            pdf_bytes = response["Body"].read()
            part = MIMEApplication(pdf_bytes, Name=display_name)
            part["Content-Disposition"] = f'attachment; filename="{display_name}"'
            msg.attach(part)
        except Exception as e:
            raise Exception(f"Missing file in S3: {s3_key}") from e

    with smtplib.SMTP("smtp.aol.com", 587, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(AOL_EMAIL, AOL_APP_PASSWORD)
        smtp.sendmail(AOL_EMAIL, recipient, msg.as_string())


@app.route("/admin/coi", methods=["GET"])
@login_required
def admin_coi():
    user = database.get_user(session["user_id"])
    show_all = request.args.get("show_all", "true").lower() == "true"
    coverage_start, coverage_end = get_coverage_period()
    departments = database.get_coi_departments(
        pending_only=not show_all,
        coverage_start=coverage_start,
    )
    edit_form = COIEditForm()
    company_docs = database.get_company_documents()
    state_license_plumbing_docs = [d for d in company_docs if d["doc_type"] == "State License - Plumbing"]
    state_license_contractor_docs = [d for d in company_docs if d["doc_type"] == "State License - Contractor"]
    btr_plumbing_docs = [d for d in company_docs if d["doc_type"] == "BTR - Plumbing"]
    btr_contractor_docs = [d for d in company_docs if d["doc_type"] == "BTR - Contractor"]
    coi_year_folders = list_coi_year_folders()
    failure_count = database.count_coi_send_failures()
    return render_template(
        "admin_coi.html",
        user=user,
        departments=departments,
        show_all=show_all,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        edit_form=edit_form,
        state_license_plumbing_docs=state_license_plumbing_docs,
        state_license_contractor_docs=state_license_contractor_docs,
        btr_plumbing_docs=btr_plumbing_docs,
        btr_contractor_docs=btr_contractor_docs,
        coi_year_folders=coi_year_folders,
        failure_count=failure_count,
    )


@app.route("/admin/coi/update/<int:dept_id>", methods=["POST"])
@login_required
def admin_coi_update(dept_id):
    show_all = request.form.get("show_all", "false")
    edit_form = COIEditForm()
    if edit_form.validate_on_submit():
        web_portal = edit_form.web_portal.data.strip()
        if web_portal and not web_portal.startswith(("http://", "https://")):
            web_portal = "https://" + web_portal
        fields = {
            "entity": edit_form.entity.data,
            "primary_phone": edit_form.primary_phone.data,
            "primary_email": edit_form.primary_email.data,
            "web_portal": web_portal,
            "submission_method": edit_form.submission_method.data,
            "notes": edit_form.notes.data,
        }
        try:
            database.update_coi_department(dept_id, fields)
            flash("Department updated successfully.")
        except Exception as e:
            flash("Error updating department. Please try again.")
            app.logger.error("COI update error: %s", e)
    else:
        for errors in edit_form.errors.values():
            flash(errors[0])
    return redirect(url_for("admin_coi", show_all=show_all))


@app.route("/admin/coi/send", methods=["POST"])
@login_required
def admin_coi_send():
    show_all = request.form.get("show_all", "false")
    coverage_start, _ = get_coverage_period()

    selected_ids = request.form.getlist("selected_depts")
    if not selected_ids:
        flash("No departments selected.")
        return redirect(url_for("admin_coi", show_all=show_all))

    state_license_plumbing_key = request.form.get("state_license_plumbing_key", "").strip() or None
    state_license_contractor_key = request.form.get("state_license_contractor_key", "").strip() or None
    btr_plumbing_key = request.form.get("btr_plumbing_key", "").strip() or None
    btr_contractor_key = request.form.get("btr_contractor_key", "").strip() or None
    coi_year = request.form.get("coi_year", "").strip() or None

    doc_coi_ids = set(request.form.getlist("doc_coi"))
    doc_sl_plumbing_ids = set(request.form.getlist("doc_sl_plumbing"))
    doc_sl_contractor_ids = set(request.form.getlist("doc_sl_contractor"))
    doc_btr_plumbing_ids = set(request.form.getlist("doc_btr_plumbing"))
    doc_btr_contractor_ids = set(request.form.getlist("doc_btr_contractor"))

    all_depts = database.get_coi_departments(
        pending_only=False, coverage_start=coverage_start
    )
    id_to_dept = {str(d["id"]): d for d in all_depts}

    email_successes = []
    email_failures = []
    portal_ids = []

    for dept_id in selected_ids:
        dept = id_to_dept.get(dept_id)
        if not dept:
            continue
        if dept["submission_method"] == "Portal":
            portal_ids.append(dept_id)
        else:
            if not dept["primary_email"]:
                reason = "no email on file"
                email_failures.append(dept["entity"])
                database.log_coi_send_failure(dept_id, dept["entity"], reason)
                continue
            docs = {
                "coi": dept_id in doc_coi_ids,
                "sl_plumbing": dept_id in doc_sl_plumbing_ids,
                "sl_contractor": dept_id in doc_sl_contractor_ids,
                "btr_plumbing": dept_id in doc_btr_plumbing_ids,
                "btr_contractor": dept_id in doc_btr_contractor_ids,
            }
            if not any(docs.values()):
                reason = "no documents selected"
                email_failures.append(dept["entity"])
                database.log_coi_send_failure(dept_id, dept["entity"], reason)
                continue
            try:
                send_coi_email(
                    dept, coverage_start, docs,
                    state_license_plumbing_key=state_license_plumbing_key,
                    state_license_contractor_key=state_license_contractor_key,
                    btr_plumbing_key=btr_plumbing_key,
                    btr_contractor_key=btr_contractor_key,
                    coi_year=coi_year,
                )
                database.mark_coi_sent([dept_id], dept["primary_email"])
                email_successes.append(dept["entity"])
                time.sleep(1)
            except Exception as e:
                app.logger.error("COI email error for %s: %s", dept["entity"], e)
                email_failures.append(dept["entity"])
                database.log_coi_send_failure(dept_id, dept["entity"], str(e))

    if portal_ids:
        try:
            database.mark_coi_sent(portal_ids, "Portal")
            flash(f"Marked {len(portal_ids)} portal submission(s) as sent.")
        except Exception as e:
            flash("Error marking portal submissions as sent.")
            app.logger.error("Portal mark error: %s", e)

    if email_successes:
        flash(f"Email sent to {len(email_successes)} department(s).")
    if email_failures:
        flash(f"Failed to send to: {', '.join(email_failures)}. See the failure log for details.")

    return redirect(url_for("admin_coi", show_all=show_all))


@app.route("/admin/coi/failures", methods=["GET"])
@login_required
def admin_coi_failures():
    user = database.get_user(session["user_id"])
    failures = database.get_coi_send_failures(resolved=False)
    return render_template("admin_coi_failures.html", user=user, failures=failures)


@app.route("/admin/coi/failures/<int:failure_id>/resolve", methods=["POST"])
@login_required
def resolve_coi_failure(failure_id):
    database.resolve_coi_send_failure(failure_id)
    return redirect(url_for("admin_coi_failures"))


@app.route("/admin/coi/failures/resolve-all", methods=["POST"])
@login_required
def resolve_all_coi_failures():
    database.resolve_all_coi_send_failures()
    return redirect(url_for("admin_coi_failures"))


@app.route("/admin/company-docs", methods=["GET"])
@login_required
def admin_company_docs():
    user = database.get_user(session["user_id"])
    docs = database.get_company_documents()
    folders = list_company_doc_folders()
    return render_template(
        "admin_company_docs.html",
        user=user,
        docs=docs,
        folders=folders,
        doc_types=COMPANY_DOC_TYPES,
    )


@app.route("/admin/company-docs/upload", methods=["POST"])
@login_required
def admin_company_docs_upload():
    file = request.files.get("file")
    doc_type = request.form.get("doc_type", "").strip()
    folder_select = request.form.get("folder_select", "").strip()
    new_folder = request.form.get("new_folder", "").strip()
    expiration_date = request.form.get("expiration_date", "").strip() or None

    if not file or not file.filename:
        flash("No file selected.")
        return redirect(url_for("admin_company_docs"))
    if not doc_type:
        flash("Document type is required.")
        return redirect(url_for("admin_company_docs"))

    folder = new_folder if folder_select == "__new__" else folder_select
    if not folder:
        flash("A folder name is required.")
        return redirect(url_for("admin_company_docs"))

    s3_key = upload_company_doc(file, folder, file.filename)
    if not s3_key:
        flash("Upload failed — file was not saved to S3.")
        return redirect(url_for("admin_company_docs"))

    filename = secure_filename(file.filename)
    success = database.insert_company_document(
        doc_type=doc_type,
        s3_key=s3_key,
        folder=folder,
        filename=filename,
        user_id=session["user_id"],
        expiration_date=expiration_date,
    )
    if success:
        flash(f"'{filename}' uploaded successfully.")
    else:
        flash("File uploaded to S3 but database record failed.")

    return redirect(url_for("admin_company_docs"))


@app.route("/admin/company-docs/edit/<int:doc_id>", methods=["POST"])
@login_required
def admin_company_docs_edit(doc_id):
    doc_type = request.form.get("doc_type", "").strip()
    expiration_date = request.form.get("expiration_date", "").strip() or None

    if not doc_type:
        flash("Document type is required.")
        return redirect(url_for("admin_company_docs"))

    success = database.update_company_document(doc_id, doc_type, expiration_date)
    if success:
        flash("Document updated successfully.")
    else:
        flash("Error updating document. Please try again.")

    return redirect(url_for("admin_company_docs"))


@app.route("/admin/company-docs/delete/<int:doc_id>", methods=["POST"])
@login_required
def admin_company_docs_delete(doc_id):
    doc = database.get_company_document(doc_id)
    if not doc:
        flash("Document not found.")
        return redirect(url_for("admin_company_docs"))

    delete_file(doc["s3_key"])
    success = database.delete_company_document(doc_id)
    if success:
        flash(f"'{doc['filename']}' deleted.")
    else:
        flash("Error deleting document. Please try again.")

    return redirect(url_for("admin_company_docs"))


############## Helper Methods ##############
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
        app.logger.error("Error clearing proposal installments: %s", e)
        return jsonify(success=False, error="An internal error occurred"), 500


def get_encoded_logo():
    # This works on local Windows and Render Linux
    path = os.path.join(app.root_path, "static", "logo.png")
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        app.logger.warning("Logo not found at %s", path)
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
def safe_url(value):
    if not value:
        return "#"
    value = str(value).strip()
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value


@app.template_filter()
def format_currency(value):
    return "$" + format(value, ",.2f")


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
