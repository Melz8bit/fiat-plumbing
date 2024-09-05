import mimetypes
import json
import os
import urllib.parse
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
from num2words import num2words
from sqlalchemy import null, select
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import database
from database import db_connect
from documents import upload_file, download_file
from forms import (
    ClientForm,
    LoginForm,
    SignUpForm,
    ProjectForm,
    MasterPermitForm,
    DocumentUploadForm,
    ProjectStatusForm,
    InvoiceStatusUpdateForm,
    InvoicePaymentForm,
    InvoiceCreateForm,
    ApplyPaymentForm,
    ProposalFixturesForm,
    ProposalInstallmentsForm,
    ProposalNotesForm,
    ProposalCreate,
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

engine = db_connect()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

############## Login/Logout ##############


@login_manager.user_loader
def load_user(user_id):
    user = users.Users(database.get_user(user_id))
    return user


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
                    login_user(user, remember=True)

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
    except:
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

        try:
            if len(database.get_user_from_email(email)) > 0:
                flash("Email is already in use. Please choose another email.")

        except Exception as e:
            password_hash = generate_password_hash(password, "scrypt")
            user_info = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password_hash,
            }

            try:
                database.create_user(user_info)
                flash("Thanks for registering")
                first_name = ""
                last_name = ""
                email = ""
                password = ""
                confirm = ""

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


############## Home ##############
@app.route("/")
@login_required
def main():
    user = database.get_user(session["user_id"])
    clients = database.get_all_clients()
    projects = database.get_all_projects()

    return render_template(
        "home.html",
        user=user,
        clients=clients,
        projects=projects,
    )


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
    clients = database.get_all_clients()

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

    search_criteria = request.args["search_criteria"]

    search_by = request.args["search_by"].lower()

    if not search_by:
        search_by = "project number"

    results = database.search(search_by, search_criteria)

    return render_template(
        "search_results.html",
        user=user,
        search_criteria=search_criteria,
        results=results,
    )


############## Projects ##############
@app.route("/projects")
@login_required
def projects_list():
    user = database.get_user(session["user_id"])
    projects = database.get_all_projects()

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
    notes = database.get_notes(project_id)
    installments = database.get_installments(project_id)
    invoices = database.get_invoices(project_id)
    open_invoices = database.get_open_invoices(project_id)
    project_payments = database.get_project_payments(project_id)
    documents = database.get_project_docs(project_id)
    master_permit = database.get_master_permit(project_id)
    plumbing_permit = database.get_plumbing_permit(project_id)
    proposal_fixtures = database.get_proposal_fixtures(project_id)
    proposal_installments = database.get_proposal_installments(project_id)
    proposal_notes = database.get_proposal_notes(project_id)

    if new_project:
        flash("Project has been created")

    # Form Initialization
    master_form = MasterPermitForm()
    document_form = DocumentUploadForm()
    project_status_form = ProjectStatusForm()
    invoice_status_form = InvoiceStatusUpdateForm()
    payment_detail_form = InvoicePaymentForm()
    invoice_create_form = InvoiceCreateForm()
    apply_payment_form = ApplyPaymentForm()
    proposal_fixtures_form = ProposalFixturesForm()
    proposal_installments_form = ProposalInstallmentsForm()
    proposal_notes_form = ProposalNotesForm()
    proposal_create_form = ProposalCreate()

    # Variable Initialization
    document_type = None
    comment = None
    filename = None

    # Track payments made on invoices and invoice items
    payment_info = {}
    payments_received_total = {}
    invoice_items = {}

    # Get installments per payment
    installment_payments = database.get_payment_installments(project_id)

    # Get project total amount
    project_total = 0
    for installment in installments:
        project_total += installment["installment_amount"]

    # Get total amount of payments received
    payments_total = 0
    for payment in project_payments:
        payments_total += payment["payment_amount"]

    if invoices:
        for invoice in invoices:
            payment = database.get_invoice_payments(invoice["invoice_id"])
            if payment:
                payment_info[invoice["invoice_id"]] = payment
                payments_received_total[invoice["invoice_id"]] = (
                    database.get_invoice_payments_total(invoice["invoice_id"])
                )

            invoice_item = database.get_invoice_items(
                project_id, invoice["invoice_number"]
            )
            if invoice_item:
                invoice_items[invoice_item[0]["invoice_number"]] = invoice_item
    else:
        invoices = []

    if master_form.validate_on_submit():
        master_permit = master_form.master_permit.data
        master_form.master_permit.data = ""

        database.insert_master_permit(project["project_id"], master_permit)
        return redirect(url_for("project_view", project_id=project["project_id"]))
    else:
        print(f"{master_form.errors=}")

    if project_status_form.validate_on_submit():
        project_status = project_status_form.project_status.data
        if project_status != project["status"]:
            database.update_project_status(
                project["project_id"], project_status, session["user_id"]
            )
        return redirect(url_for("project_view", project_id=project["project_id"]))
    else:
        print(f"{project_status_form.errors=}")

    if document_form.validate_on_submit():
        document_type = document_form.document_type.data
        document_form.document_type.data = ""
        comment = document_form.comment.data
        document_form.comment.data = ""
        filename = document_form.upload_file.data
        document_form.upload_file.data = ""

        upload_file_type = filename.filename.split(".")[-1]
        upload_file_name = f"{project_id}-{document_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}.{upload_file_type}"

        upload_file(
            filename,
            upload_file_name,
            filename.mimetype,
        )

        database.upload_document(
            project_id,
            document_type,
            comment,
            session["user_id"],
            upload_file_name,
        )

        return redirect(url_for("project_view", project_id=project["project_id"]))
    else:
        print(f"{document_form.errors=}")

    if apply_payment_form.validate_on_submit():
        # Payment Information Data
        payment_method = apply_payment_form.payment_method.data
        check_number = apply_payment_form.check_number.data
        payment_amount = apply_payment_form.payment_amount.data
        date_received = apply_payment_form.date_received.data
        payment_note = apply_payment_form.payment_note.data

        payment_information = {
            "project_id": project_id,
            "payment_method": payment_method,
            "check_number": check_number,
            "payment_amount": payment_amount,
            "date_received": date_received,
            "payment_note": payment_note,
        }

        # Invoice Application Data
        invoice_id_list = [int(x) for x in request.form.getlist("invoice_id")]
        payment_applied_list = [
            float(x) for x in request.form.getlist("amount_applied")
        ]
        payment_remaining_list = [
            float(x) for x in request.form.getlist("amount_remaining")
        ]
        invoice_status_list = request.form.getlist("invoice_status")

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
                    "project_id": project_id,
                    "check_number": check_number,
                }
                database.apply_payment(payment)

        # database.insert_payment(payment_information)

        return redirect(url_for("project_view", project_id=project["project_id"]))
    else:
        print(f"{apply_payment_form.errors=}")

    if invoice_create_form.validate_on_submit():
        selected_installments = request.form.getlist("installment_select")

        selected_invoices = []
        billed_invoice_amount = request.form.getlist("billed_amount")
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

        database.create_invoice(selected_invoices, project_id)

        return redirect(url_for("project_view", project_id=project["project_id"]))
    else:
        print(f"{invoice_create_form.errors=}")

    return render_template(
        "project.html",
        user=user,
        project=project,
        client=client,
        notes=notes,
        installments=installments,
        invoices=invoices,
        invoice_items=invoice_items,
        documents=documents,
        master_permit=master_permit,
        plumbing_permit=plumbing_permit,
        master_form=master_form,
        document_form=document_form,
        project_status_form=project_status_form,
        invoice_status_form=invoice_status_form,
        payment_detail_form=payment_detail_form,
        apply_payment_form=apply_payment_form,
        invoice_create_form=invoice_create_form,
        proposal_fixtures_form=proposal_fixtures_form,
        proposal_installments_form=proposal_installments_form,
        proposal_notes_form=proposal_notes_form,
        proposal_create_form=proposal_create_form,
        payment_info=payment_info,
        payments_received_total=payments_received_total,
        open_invoices=open_invoices,
        project_payments=project_payments,
        project_total=project_total,
        payments_total=payments_total,
        installment_payments=installment_payments,
        proposal_fixtures=proposal_fixtures,
        proposal_fixtures_total=fixtures_total(proposal_fixtures),
        proposal_installments=proposal_installments,
        proposal_installments_total=installments_total(proposal_installments),
        proposal_notes=proposal_notes,
    )


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

    if form.validate_on_submit():
        project_id = form.project_id.data
        form.project_id.data = ""
        name = form.name.data
        form.name.data = ""
        client = int(form.client.data)
        form.client.data = ""
        address = form.address.data
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
        database.insert_note(project_id, f"Project Created", session["user_id"])

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


@app.route("/createProposalPDF/<project_id>")
@login_required
def create_proposal_pdf(project_id):
    project_info = database.get_project(project_id)
    client_info = database.get_project_client(project_id)
    proposal_fixtures = database.get_proposal_fixtures(project_id)
    proposal_installments = database.get_proposal_installments(project_id)
    proposal_notes = database.get_proposal_notes(project_id)

    proposal_total = 0
    for fixture in proposal_fixtures:
        proposal_total += fixture["total_per_fixture"]

    proposal_total_words = num2words(proposal_total)
    proposal_total_words = proposal_total_words.replace(",", "")

    return render_template(
        "proposal_print.html",
        project_info=project_info,
        client_info=client_info,
        proposal_fixtures=proposal_fixtures,
        proposal_installments=proposal_installments,
        proposal_notes=proposal_notes,
        proposal_total=proposal_total,
        proposal_total_words=proposal_total_words,
    )


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


############## Misc. ##############
@app.route("/populateCityStateCounty", methods=["GET", "POST"])
def populate_city_state_county():
    results = database.get_city_state_county(request.args["zip_code"])
    return dict(results)


@app.route("/addProposalFixture", methods=["POST"])
def add_proposal_fixture():
    # Decode the bytes to a string
    serialized_data = request.data.decode("utf-8")

    # Parse the query string into a dictionary
    parsed_data = urllib.parse.parse_qs(serialized_data)

    # Convert the dictionary values to strings (if needed)
    for key, value in parsed_data.items():
        parsed_data[key] = value[0]

    # Get values for returning
    fixture_abbreviation = str(parsed_data["fixture_select"]).split(" - ")[0]
    fixture_name = str(parsed_data["fixture_select"]).split(" - ")[1]

    # Convert to correct format and data types
    parsed_data["fixture_select"] = fixture_abbreviation
    parsed_data["fixture_quantity"] = int(parsed_data["fixture_quantity"])
    parsed_data["fixture_cost"] = float(parsed_data["fixture_cost"])

    database.add_proposal_fixture(parsed_data)

    return get_all_proposal_fixtures(parsed_data["project_id"])


@app.route("/deleteProposalFixture/<fixture_id>/<project_id>", methods=["POST"])
def delete_proposal_fixture(fixture_id, project_id):
    database.delete_proposal_fixture(fixture_id)

    return get_all_proposal_fixtures(project_id)


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
                "fixture_total": fixture["total_per_fixture"],
            }
        )

    return jsonify(fixtures_added)


@app.route("/addProposalInstallment", methods=["POST"])
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


@app.route("/applyPayment/<project_id>", methods=["GET", "POST"])
def apply_payment(project_id):
    payment_form = ApplyPaymentForm()

    payment_applied_info = []

    payment_remaining = float(ApplyPaymentForm().data["payment_amount"])
    open_invoices = database.get_open_invoices(project_id)

    for invoice in open_invoices:
        payment_dict = None
        # print(f"{invoice['payment_remaining']=}")
        # print(f"{invoice['payment_received']=}")
        if payment_remaining < invoice["payment_remaining"]:
            payment_dict = {
                "invoice_id": invoice["invoice_id"],
                "invoice_status": "Partial Payment",
                "amount_remaining": invoice["payment_remaining"] - payment_remaining,
                "amount_received": payment_remaining,
            }
            payment_remaining = 0

        if payment_remaining >= invoice["payment_remaining"]:
            payment_dict = {
                "invoice_id": invoice["invoice_id"],
                "invoice_status": "Paid",
                "amount_received": invoice["payment_remaining"],
                "amount_remaining": 0,
            }

            payment_remaining -= invoice["payment_remaining"]

        print(f"{payment_dict=}")
        payment_applied_info.append(payment_dict)

        if payment_remaining == 0:
            # print(payment_applied_info)
            return jsonify(payment_applied_info)

    # print(f"{invoice_id=}")
    return jsonify("")


@app.route("/addProposalNote", methods=["POST"])
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
# A dumb change
