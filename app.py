import mimetypes
import json
import os
from datetime import datetime, date
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
    notes = database.get_notes(project_id)
    installments = database.get_installments(project_id)
    invoices = database.get_invoices(project_id)
    documents = database.get_project_docs(project_id)
    master_permit = database.get_master_permit(project_id)
    plumbing_permit = database.get_plumbing_permit(project_id)

    if new_project:
        flash("Project has been created")

    # Form Initialization
    master_form = MasterPermitForm()
    document_form = DocumentUploadForm()
    project_status_form = ProjectStatusForm()
    invoice_status_form = InvoiceStatusUpdateForm()
    payment_detail_form = InvoicePaymentForm()
    invoice_create_form = InvoiceCreateForm()

    # Variable Initialization
    document_type = None
    comment = None
    filename = None

    # Track payments made on invoices
    payment_info = {}
    payments_received_total = {}
    if invoices:
        for invoice in invoices:
            payment = database.get_invoice_payments(invoice["invoice_id"])
            if payment:
                payment_info[invoice["invoice_id"]] = payment
                payments_received_total[invoice["invoice_id"]] = (
                    database.get_invoice_payments_total(invoice["invoice_id"])
                )
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

    if invoice_create_form.validate_on_submit():
        selected_installments = request.form.getlist("installment_select")
        database.create_invoice(selected_installments, project_id)
        return redirect(url_for("project_view", project_id=project["project_id"]))

    return render_template(
        "project.html",
        user=user,
        project=project,
        notes=notes,
        installments=installments,
        invoices=invoices,
        documents=documents,
        master_permit=master_permit,
        plumbing_permit=plumbing_permit,
        master_form=master_form,
        document_form=document_form,
        project_status_form=project_status_form,
        invoice_status_form=invoice_status_form,
        payment_detail_form=payment_detail_form,
        invoice_create_form=invoice_create_form,
        payment_info=payment_info,
        payments_received_total=payments_received_total,
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
    )


@app.route("/project/<project_id>/download/<doc_filename>")
@login_required
def download_document(project_id, doc_filename):
    my_file = download_file(doc_filename)
    print(my_file["ContentType"])
    return Response(
        my_file["Body"].read(),
        mimetype=my_file["ContentType"],
        headers={"Content-Disposition": f"attachment;filename={doc_filename}"},
    )


@app.route("/project/<project_id>/invoice/view/<installment_number>")
@login_required
def view_invoice(project_id, installment_number):
    user = database.get_user(session["user_id"])
    project_info = database.get_project(project_id)
    invoice_info = [database.get_invoice(project_id, installment_number)]
    client_info = database.get_client(project_info["client_id"])

    today_date = datetime.now().strftime("%m/%d/%Y")
    print(len(invoice_info))
    if len(invoice_info) == 1:
        if invoice_info[0]["installment_status"] != "Paid":
            invoice_info = database.get_open_invoices(project_id, installment_number)

    invoice_total = sum(invoice["installment_amount"] for invoice in invoice_info)

    return render_template(
        "invoice_print.html",
        user=user,
        project_info=project_info,
        invoice_info=invoice_info,
        client_info=client_info,
        today_date=today_date,
        fiat_plumbing=FIAT_PLUMBING,
        invoice_total=invoice_total,
        installment_number=installment_number,
    )


############## Helper Methods ##############
def update_invoice_status(project_id, installment_number, installment_status):
    database.update_installment_status(
        project_id, installment_number, installment_status, session["user_id"]
    )


############## Misc. ##############
@app.route("/populateCityStateCounty", methods=["GET", "POST"])
def populate_city_state_county():
    results = database.get_city_state_county(request.args["zip_code"])[0]
    return results


@app.template_filter()
def format_currency(value):
    # locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    value = format(value, ",.2f")

    if not value:
        return "$0.00"
        # return locale.currency(0, symbol=True, grouping=True)

    return "$" + str(value)
    # return locale.currency(value, symbol=True, grouping=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
