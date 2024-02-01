import os

from flask import (
    Flask,
    flash,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
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

import database
from database import db_connect
from forms import ClientForm, LoginForm, SignUpForm
from models import users

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_KEY")

engine = db_connect()
# session = create_session(engine)
# app.config["SESSION_TYPE"] = "sqlalchemy"
# app.config.from_object(__name__)
# Session(app)

# USER_ID = "525bc4ea-b0f7-482d-a954-db517e6b5b89"
# USER_ID = ""

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    user = users.Users(database.get_user(user_id))
    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        login_form.email.data = ""
        login_form.password.data = ""

        user_db_password = database.get_user_password(email)
        if user_db_password:
            user_db_password = user_db_password[0]
            if check_password_hash(user_db_password["password"], password):
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


@app.route("/client_list")
def client_list():
    user = database.get_user(session["user_id"])
    clients = database.get_all_clients()

    return render_template(
        "client_list.html",
        user=user,
        clients=clients,
    )


@app.route("/search")
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
        results=results,
    )


@app.route("/project/<project_id>")
def project_view(project_id):
    user = database.get_user(session["user_id"])
    project = database.get_project(project_id)
    notes = database.get_notes(project_id)
    invoices = database.get_invoices(project_id)

    return render_template(
        "project.html",
        user=user,
        project=project,
        notes=notes,
        invoices=invoices,
    )


@app.route("/client-add", methods=["GET", "POST"])
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
